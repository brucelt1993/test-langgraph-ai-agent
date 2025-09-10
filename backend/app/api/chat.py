"""
聊天API端点。

提供完整的聊天会话管理和实时流式响应功能。
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime, timezone

from app.core.database import get_async_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession as DBChatSession, Message as DBMessage
from app.services.chat_service import get_chat_service, ChatService
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionUpdate,
    MessageCreate, MessageResponse, MessageUpdate,
    SendMessageRequest, StreamingResponse as StreamingResponseSchema,
    ChatSessionListResponse, ChatSessionStatsResponse
)
from app.core.permissions import PermissionType
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    db: AsyncSession = Depends(get_async_db)
):
    """创建新的聊天会话。"""
    try:
        session = await chat_service.create_session(
            user_id=current_user.id,
            title=session_data.title,
            agent_name=session_data.agent_name,
            context=session_data.context or {}
        )
        return ChatSessionResponse.from_orm(session)
    except Exception as e:
        logger.error(f"创建聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建聊天会话失败"
        )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取用户的聊天会话列表。"""
    try:
        sessions, total = await chat_service.get_user_sessions(
            user_id=current_user.id,
            page=page,
            size=size
        )
        
        return ChatSessionListResponse(
            sessions=[ChatSessionResponse.from_orm(session) for session in sessions],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        logger.error(f"获取聊天会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取聊天会话列表失败"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取指定的聊天会话。"""
    try:
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        return ChatSessionResponse.from_orm(session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取聊天会话失败"
        )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """更新聊天会话。"""
    try:
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        updated_session = await chat_service.update_session(
            session_id=session_id,
            user_id=current_user.id,
            title=update_data.title,
            is_active=update_data.is_active,
            metadata=update_data.metadata
        )
        
        return ChatSessionResponse.from_orm(updated_session)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新聊天会话失败"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """删除聊天会话。"""
    try:
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        await chat_service.delete_session(session_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除聊天会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除聊天会话失败"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话的消息列表。"""
    try:
        # 验证会话所有权
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            page=page,
            size=size
        )
        
        return [MessageResponse.from_orm(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话消息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话消息失败"
        )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """发送消息并获取AI流式响应。"""
    
    # 验证会话所有权
    session = await chat_service.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天会话不存在"
        )
    
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            # 使用ChatService的流式响应生成器
            async for chunk in chat_service.send_message(
                session_id=session_id,
                user_id=current_user.id,
                content=message_data.content,
                message_type=DBMessageType.USER,
                metadata=message_data.metadata
            ):
                # 将响应数据格式化为SSE格式
                chunk_data = json.dumps(chunk, ensure_ascii=False, default=str)
                yield f"data: {chunk_data}\n\n"
                
                # 小延迟以确保流式传输效果
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"发送消息流式响应失败: {str(e)}")
            error_chunk = {
                "type": "error",
                "content": "处理消息时发生错误",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            error_data = json.dumps(error_chunk, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
        finally:
            # 发送结束标记
            end_chunk = {
                "type": "stream_end",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            end_data = json.dumps(end_chunk, ensure_ascii=False)
            yield f"data: {end_data}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/sessions/{session_id}/context", response_model=Dict[str, Any])
async def get_session_context(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话上下文（最近10轮对话）。"""
    try:
        # 验证会话所有权
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        context = await chat_service.get_conversation_context(session_id)
        return {
            "session_id": session_id,
            "context_messages": context,
            "context_rounds": len(context) // 2,  # 每轮包含用户消息和AI响应
            "max_rounds": chat_service.context_window_rounds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话上下文失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话上下文失败"
        )


@router.get("/sessions/{session_id}/stats", response_model=ChatSessionStatsResponse)
async def get_session_stats(
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话统计信息。"""
    try:
        # 验证会话所有权
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        stats = await chat_service.get_session_stats(session_id)
        return ChatSessionStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话统计信息失败"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_user_chat_stats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取用户整体聊天统计信息。"""
    try:
        stats = await chat_service.get_user_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"获取用户聊天统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户聊天统计信息失败"
        )


@router.post("/sessions/{session_id}/cleanup")
async def cleanup_session_context(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """清理会话上下文（管理员功能）。"""
    try:
        # 验证会话存在
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天会话不存在"
            )
        
        # 在后台任务中执行清理
        background_tasks.add_task(
            chat_service.cleanup_session_context,
            session_id
        )
        
        return {
            "message": "会话上下文清理任务已启动",
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动会话上下文清理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动会话上下文清理失败"
        )


@router.websocket("/sessions/{session_id}/ws")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """WebSocket聊天端点（备用实现）。"""
    await websocket.accept()
    
    try:
        # 验证会话所有权
        session = await chat_service.get_session(session_id, current_user.id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": "聊天会话不存在"
            })
            await websocket.close()
            return
        
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message_content = data.get("content", "")
            
            if not message_content.strip():
                await websocket.send_json({
                    "type": "error", 
                    "message": "消息内容不能为空"
                })
                continue
            
            # 流式发送AI响应
            async for chunk in chat_service.send_message(
                session_id=session_id,
                user_id=current_user.id,
                content=message_content,
                message_type=DBMessageType.USER,
                metadata=data.get("metadata")
            ):
                await websocket.send_json(chunk)
                
    except Exception as e:
        logger.error(f"WebSocket聊天错误: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": "连接出现错误"
        })
    finally:
        await websocket.close()