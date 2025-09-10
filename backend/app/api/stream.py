"""
SSE流式响应API端点。

提供Server-Sent Events流式数据传输的HTTP API接口。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.services.stream_service import (
    get_stream_service, StreamService, StreamMessage, StreamEventType,
    stream_connection
)
from app.services.chat_service import get_chat_service, ChatService
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


@router.post("/connections")
async def create_stream_connection(
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    创建SSE流式连接。
    
    Returns:
        连接信息
    """
    try:
        connection_id = await stream_service.create_connection(
            user_id=current_user.id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        connection_info = stream_service.get_connection_info(connection_id)
        
        return {
            "connection_id": connection_id,
            "connection_info": connection_info,
            "stream_url": f"/api/stream/events/{connection_id}",
            "message": "SSE连接已创建",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"创建SSE连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建SSE连接失败"
        )


@router.get("/events/{connection_id}")
async def stream_events(
    connection_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    SSE事件流端点。
    
    Args:
        connection_id: 连接ID
        request: HTTP请求对象
        current_user: 当前用户
        stream_service: 流式服务
        
    Returns:
        SSE流式响应
    """
    # 验证连接所有权
    connection_info = stream_service.get_connection_info(connection_id)
    if not connection_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
        
    if connection_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此连接"
        )
    
    async def generate_events():
        """生成SSE事件流。"""
        try:
            async for event_data in stream_service.get_event_stream(connection_id):
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    logger.info(f"客户端断开连接: {connection_id}")
                    break
                    
                yield event_data
                
        except Exception as e:
            logger.error(f"生成SSE事件流时出错: {str(e)}")
            # 发送错误事件
            error_message = StreamMessage(
                event_type=StreamEventType.ERROR,
                data={
                    "error": "流生成错误",
                    "message": str(e),
                    "connection_id": connection_id
                }
            )
            yield error_message.to_sse_format()
            
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "Access-Control-Allow-Credentials": "true"
        }
    )


@router.post("/connections/{connection_id}/message")
async def send_stream_message(
    connection_id: str,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    向指定连接发送消息。
    
    Args:
        connection_id: 连接ID
        message_data: 消息数据
        current_user: 当前用户
        stream_service: 流式服务
        
    Returns:
        发送结果
    """
    # 验证连接所有权
    connection_info = stream_service.get_connection_info(connection_id)
    if not connection_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
        
    if connection_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权向此连接发送消息"
        )
    
    try:
        # 创建流式消息
        message = StreamMessage(
            event_type=StreamEventType(message_data.get("event_type", StreamEventType.MESSAGE.value)),
            data=message_data.get("data", {}),
            id=message_data.get("id")
        )
        
        # 发送消息
        success = await stream_service.send_message(connection_id, message)
        
        return {
            "success": success,
            "connection_id": connection_id,
            "message_id": message.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"发送流式消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送消息失败"
        )


@router.post("/broadcast")
async def broadcast_message(
    message_data: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    广播消息到匹配的连接。
    
    Args:
        message_data: 消息数据
        user_id: 目标用户ID（可选）
        session_id: 目标会话ID（可选）
        current_user: 当前用户
        stream_service: 流式服务
        
    Returns:
        广播结果
    """
    # 如果指定了用户ID且不是当前用户，需要管理员权限
    if user_id and user_id != current_user.id:
        # 这里可以添加权限检查
        pass
    
    try:
        # 创建流式消息
        message = StreamMessage(
            event_type=StreamEventType(message_data.get("event_type", StreamEventType.MESSAGE.value)),
            data=message_data.get("data", {}),
            id=message_data.get("id")
        )
        
        # 广播消息
        await stream_service.broadcast_message(
            message=message,
            user_id=user_id or current_user.id,
            session_id=session_id
        )
        
        return {
            "success": True,
            "target_user_id": user_id or current_user.id,
            "target_session_id": session_id,
            "message_id": message.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"广播消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="广播消息失败"
        )


@router.get("/connections/{connection_id}")
async def get_connection_info(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    获取连接信息。
    
    Args:
        connection_id: 连接ID
        current_user: 当前用户
        stream_service: 流式服务
        
    Returns:
        连接信息
    """
    connection_info = stream_service.get_connection_info(connection_id)
    if not connection_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
        
    # 验证连接所有权
    if connection_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此连接信息"
        )
        
    return connection_info


@router.delete("/connections/{connection_id}")
async def disconnect_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    断开连接。
    
    Args:
        connection_id: 连接ID
        current_user: 当前用户  
        stream_service: 流式服务
        
    Returns:
        断开结果
    """
    connection_info = stream_service.get_connection_info(connection_id)
    if not connection_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
        
    # 验证连接所有权
    if connection_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权断开此连接"
        )
    
    try:
        await stream_service.disconnect(connection_id)
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": "连接已断开",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"断开连接失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="断开连接失败"
        )


@router.get("/connections")
async def list_user_connections(
    current_user: User = Depends(get_current_user),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    获取用户的所有连接。
    
    Args:
        current_user: 当前用户
        stream_service: 流式服务
        
    Returns:
        连接列表
    """
    all_connections = stream_service.get_all_connections()
    
    # 过滤当前用户的连接
    user_connections = [
        conn for conn in all_connections
        if conn and conn["user_id"] == current_user.id
    ]
    
    return {
        "connections": user_connections,
        "total": len(user_connections),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def stream_health_check(
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    流式服务健康检查。
    
    Args:
        stream_service: 流式服务
        
    Returns:
        健康状态
    """
    all_connections = stream_service.get_all_connections()
    active_connections = len(all_connections)
    
    return {
        "status": "healthy",
        "service": "SSE Streaming",
        "active_connections": active_connections,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 集成聊天流式响应
@router.post("/chat/{session_id}/stream")
async def stream_chat_response(
    session_id: str,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    发送聊天消息并返回流式响应连接。
    
    Args:
        session_id: 会话ID
        message_data: 消息数据
        current_user: 当前用户
        chat_service: 聊天服务
        stream_service: 流式服务
        
    Returns:
        流式响应连接信息
    """
    # 验证会话权限
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    try:
        # 创建流式连接
        connection_id = await stream_service.create_connection(
            user_id=current_user.id,
            session_id=session_id,
            metadata={"type": "chat_stream", "message_type": "user_message"}
        )
        
        # 在后台处理聊天响应
        async def process_chat_response():
            try:
                async for chunk in chat_service.send_message(
                    session_id=session_id,
                    user_id=current_user.id,
                    content=message_data.get("content", ""),
                    message_type=DBMessageType.USER,
                    metadata=message_data.get("metadata")
                ):
                    # 转换为流式消息格式
                    event_type = StreamEventType.MESSAGE
                    if chunk.get("type") == "thinking":
                        event_type = StreamEventType.THINKING
                    elif chunk.get("type") == "tool_call":
                        event_type = StreamEventType.TOOL_CALL
                    elif chunk.get("type") == "tool_response":
                        event_type = StreamEventType.TOOL_RESPONSE
                    elif chunk.get("type") == "error":
                        event_type = StreamEventType.ERROR
                    
                    # 发送到流式连接
                    message = StreamMessage(
                        event_type=event_type,
                        data=chunk
                    )
                    
                    await stream_service.send_message(connection_id, message)
                    
            except Exception as e:
                # 发送错误消息
                error_message = StreamMessage(
                    event_type=StreamEventType.ERROR,
                    data={
                        "error": "聊天响应处理错误",
                        "message": str(e),
                        "session_id": session_id
                    }
                )
                await stream_service.send_message(connection_id, error_message)
        
        # 启动后台任务
        import asyncio
        asyncio.create_task(process_chat_response())
        
        return {
            "connection_id": connection_id,
            "session_id": session_id,
            "stream_url": f"/api/stream/events/{connection_id}",
            "message": "聊天流式响应已启动",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"启动聊天流式响应失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动聊天流式响应失败"
        )