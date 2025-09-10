"""
聊天服务层。

提供完整的会话管理功能，包括：
- 会话创建和管理
- 消息历史存储和检索
- 10轮上下文管理
- Agent集成
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
from datetime import datetime, timezone, timedelta
import logging
import json

from app.agents.base_agent import AgentManager, AgentResponse, MessageType, get_agent_manager
from app.agents.weather_agent import get_weather_service
from app.repositories.factory import get_repository_factory
from app.models.chat import ChatSession, Message
from app.models.user import User
from app.core.permissions import PermissionType
from app.services.auth_service import get_auth_service

logger = logging.getLogger(__name__)


class ChatService:
    """
    聊天服务类。
    
    提供完整的聊天会话管理功能。
    """
    
    def __init__(self):
        self.agent_manager = get_agent_manager()
        self.auth_service = get_auth_service()
        self.weather_service = get_weather_service()
        
        # 上下文管理配置
        self.max_context_messages = 20  # 最大保留消息数
        self.context_window_rounds = 10  # 10轮对话上下文
    
    async def create_chat_session(
        self,
        user_id: str,
        title: Optional[str] = None,
        agent_name: str = "weather_agent",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建新的聊天会话。
        
        Args:
            user_id: 用户ID
            title: 会话标题
            agent_name: Agent名称
            context: 初始上下文
            
        Returns:
            会话信息
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                # 验证Agent是否存在
                agent = self.agent_manager.get_agent(agent_name)
                if not agent:
                    raise ValueError(f"Agent '{agent_name}' not found")
                
                # 生成默认标题
                if not title:
                    title = f"与{agent_name}的对话 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
                # 创建会话
                session = await chat_repo.create_session(
                    user_id=user_id,
                    title=title,
                    agent_name=agent_name,
                    context=context or {}
                )
                
                await repo_factory.commit()
                
                logger.info(f"Created chat session: {session.id} for user: {user_id}")
                
                return {
                    "session_id": session.id,
                    "title": session.title,
                    "agent_name": session.agent_name,
                    "context": session.context,
                    "created_at": session.created_at,
                    "message_count": 0,
                    "last_message_at": None
                }
                
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_user_chat_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        include_message_preview: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取用户的聊天会话列表。
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            include_message_preview: 是否包含消息预览
            
        Returns:
            会话列表
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                sessions = await chat_repo.get_user_sessions(
                    user_id=user_id,
                    limit=limit,
                    offset=offset,
                    load_stats=True
                )
                
                session_list = []
                
                for session in sessions:
                    session_info = {
                        "session_id": session.id,
                        "title": session.title,
                        "agent_name": session.agent_name,
                        "created_at": session.created_at,
                        "updated_at": session.updated_at,
                        "message_count": len(session.messages) if session.messages else 0,
                        "last_message_at": session.updated_at
                    }
                    
                    # 添加最后一条消息预览
                    if include_message_preview and session.messages:
                        last_message = session.messages[-1]
                        session_info["last_message_preview"] = {
                            "content": last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                            "message_type": last_message.message_type,
                            "created_at": last_message.created_at
                        }
                    
                    session_list.append(session_info)
                
                return session_list
                
        except Exception as e:
            logger.error(f"Error getting user chat sessions: {e}")
            return []
    
    async def get_chat_session(
        self,
        session_id: str,
        user_id: str,
        include_messages: bool = True,
        message_limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """
        获取聊天会话详情。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            include_messages: 是否包含消息
            message_limit: 消息限制数量
            
        Returns:
            会话详情
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                session = await chat_repo.get_session_by_id(
                    session_id=session_id,
                    user_id=user_id,
                    load_messages=include_messages
                )
                
                if not session:
                    return None
                
                session_info = {
                    "session_id": session.id,
                    "title": session.title,
                    "agent_name": session.agent_name,
                    "context": session.context,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": len(session.messages) if session.messages else 0
                }
                
                if include_messages and session.messages:
                    # 按时间排序并限制数量
                    messages = sorted(session.messages, key=lambda m: m.created_at)
                    if len(messages) > message_limit:
                        messages = messages[-message_limit:]
                    
                    session_info["messages"] = [
                        {
                            "message_id": msg.id,
                            "content": msg.content,
                            "message_type": msg.message_type,
                            "metadata": msg.metadata,
                            "created_at": msg.created_at,
                            "thinking_process": msg.thinking_process
                        }
                        for msg in messages
                    ]
                
                return session_info
                
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        message_type: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        发送消息并获取AI响应。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            content: 消息内容
            message_type: 消息类型
            metadata: 元数据
            
        Yields:
            消息响应事件
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                # 获取会话
                session = await chat_repo.get_session_by_id(
                    session_id=session_id,
                    user_id=user_id,
                    load_messages=True
                )
                
                if not session:
                    yield {
                        "type": "error",
                        "content": "会话不存在或无权限访问",
                        "timestamp": datetime.now(timezone.utc)
                    }
                    return
                
                # 保存用户消息
                user_message = await chat_repo.add_message(
                    session_id=session_id,
                    content=content,
                    message_type=message_type,
                    metadata=metadata or {}
                )
                
                await repo_factory.commit()
                
                # 发送用户消息事件
                yield {
                    "type": "user_message",
                    "message_id": user_message.id,
                    "content": content,
                    "message_type": message_type.value,
                    "timestamp": user_message.created_at
                }
                
                # 获取Agent并处理消息
                agent = self.agent_manager.get_agent(session.agent_name)
                if not agent:
                    yield {
                        "type": "error",
                        "content": f"Agent '{session.agent_name}' 不可用",
                        "timestamp": datetime.now(timezone.utc)
                    }
                    return
                
                # 构建对话上下文
                context = await self._build_conversation_context(session, user_id)
                
                # 处理AI响应
                ai_response_content = ""
                thinking_process = ""
                
                try:
                    async for response in agent.process_message(
                        message=content,
                        user_id=user_id,
                        session_id=session_id,
                        context=context,
                        enable_thinking_tracking=True
                    ):
                        if response.message_type == MessageType.THINKING:
                            # 思考过程
                            thinking_process = response.content
                            yield {
                                "type": "thinking",
                                "content": response.content,
                                "timestamp": response.timestamp
                            }
                        
                        elif response.message_type == MessageType.AI:
                            # AI最终响应
                            ai_response_content = response.content
                            thinking_process = response.thinking_process or thinking_process
                            
                            # 保存AI消息
                            ai_message = await chat_repo.add_message(
                                session_id=session_id,
                                content=ai_response_content,
                                message_type="assistant",
                                metadata={
                                    "tool_calls": response.tool_calls,
                                    "model_used": agent.model_name
                                },
                                thinking_process=thinking_process
                            )
                            
                            await repo_factory.commit()
                            
                            yield {
                                "type": "ai_response",
                                "message_id": ai_message.id,
                                "content": ai_response_content,
                                "thinking_process": thinking_process,
                                "tool_calls": response.tool_calls,
                                "timestamp": ai_message.created_at
                            }
                
                except Exception as agent_error:
                    logger.error(f"Agent processing error: {agent_error}")
                    
                    # 保存错误消息
                    error_message = await chat_repo.add_message(
                        session_id=session_id,
                        content=f"抱歉，处理您的消息时遇到了问题：{str(agent_error)}",
                        message_type="assistant",
                        metadata={"error": True, "error_message": str(agent_error)}
                    )
                    
                    await repo_factory.commit()
                    
                    yield {
                        "type": "error",
                        "message_id": error_message.id,
                        "content": f"处理失败：{str(agent_error)}",
                        "timestamp": error_message.created_at
                    }
                
                # 清理旧消息（保持上下文窗口）
                await self._cleanup_old_messages(session_id, repo_factory)
                
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            yield {
                "type": "error",
                "content": f"发送消息失败：{str(e)}",
                "timestamp": datetime.now(timezone.utc)
            }
    
    async def _build_conversation_context(
        self, 
        session: ChatSession, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        构建对话上下文。
        
        Args:
            session: 聊天会话
            user_id: 用户ID
            
        Returns:
            上下文信息
        """
        try:
            # 基础上下文
            context = {
                "session_id": session.id,
                "session_title": session.title,
                "agent_name": session.agent_name,
                "user_id": user_id
            }
            
            # 添加会话上下文
            if session.context:
                context.update(session.context)
            
            # 添加最近的对话历史摘要
            if session.messages:
                recent_messages = session.messages[-self.context_window_rounds * 2:]  # 10轮对话 = 20条消息
                context["recent_conversation"] = [
                    {
                        "type": msg.message_type.value,
                        "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for msg in recent_messages
                ]
                
                context["conversation_length"] = len(session.messages)
                context["conversation_started_at"] = session.created_at.isoformat()
            
            # 获取用户信息（用于个性化）
            try:
                async with get_repository_factory() as repo_factory:
                    user_repo = repo_factory.get_user_repository()
                    user = await user_repo.get_by_id(user_id)
                    
                    if user:
                        context["user_info"] = {
                            "username": user.username,
                            "full_name": user.full_name
                        }
            except Exception as e:
                logger.warning(f"Could not get user info for context: {e}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            return {"session_id": session.id, "user_id": user_id}
    
    async def _cleanup_old_messages(self, session_id: str, repo_factory):
        """
        清理旧消息以维持上下文窗口。
        
        Args:
            session_id: 会话ID
            repo_factory: 仓储工厂
        """
        try:
            chat_repo = repo_factory.get_chat_repository()
            
            # 获取消息数量
            message_count = await chat_repo.get_message_count(session_id)
            
            if message_count > self.max_context_messages:
                # 计算需要删除的消息数量
                to_delete_count = message_count - self.max_context_messages
                
                # 删除最旧的消息，但保留最近的对话
                await chat_repo.delete_oldest_messages(session_id, to_delete_count)
                
                logger.debug(f"Cleaned up {to_delete_count} old messages from session {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")
    
    async def update_session_title(
        self,
        session_id: str,
        user_id: str,
        new_title: str
    ) -> bool:
        """
        更新会话标题。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            new_title: 新标题
            
        Returns:
            是否成功更新
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                success = await chat_repo.update_session_title(
                    session_id=session_id,
                    user_id=user_id,
                    title=new_title
                )
                
                if success:
                    await repo_factory.commit()
                    logger.info(f"Updated session title: {session_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error updating session title: {e}")
            return False
    
    async def delete_chat_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        删除聊天会话。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            是否成功删除
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                success = await chat_repo.delete_session(
                    session_id=session_id,
                    user_id=user_id
                )
                
                if success:
                    await repo_factory.commit()
                    logger.info(f"Deleted chat session: {session_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error deleting chat session: {e}")
            return False
    
    async def get_message_thinking_steps(
        self,
        session_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        获取会话的AI思考步骤。
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            思考步骤列表
        """
        try:
            # 验证用户权限
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                session = await chat_repo.get_session_by_id(session_id, user_id)
                
                if not session:
                    return []
                
                # 获取对应的Agent
                agent = self.agent_manager.get_agent(session.agent_name)
                if not agent:
                    return []
                
                # 获取思考步骤
                return await agent.get_thinking_steps(session_id)
                
        except Exception as e:
            logger.error(f"Error getting thinking steps: {e}")
            return []
    
    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的会话统计信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            async with get_repository_factory() as repo_factory:
                chat_repo = repo_factory.get_chat_repository()
                
                # 获取基础统计
                total_sessions = await chat_repo.get_user_session_count(user_id)
                total_messages = await chat_repo.get_user_message_count(user_id)
                
                # 获取最近活跃会话
                recent_sessions = await chat_repo.get_user_sessions(
                    user_id=user_id,
                    limit=5,
                    load_stats=True
                )
                
                # 统计Agent使用情况
                agent_usage = {}
                for session in recent_sessions:
                    agent_name = session.agent_name
                    agent_usage[agent_name] = agent_usage.get(agent_name, 0) + 1
                
                return {
                    "total_sessions": total_sessions,
                    "total_messages": total_messages,
                    "recent_sessions_count": len(recent_sessions),
                    "agent_usage": agent_usage,
                    "most_used_agent": max(agent_usage.items(), key=lambda x: x[1])[0] if agent_usage else None
                }
                
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "recent_sessions_count": 0,
                "agent_usage": {},
                "most_used_agent": None
            }


# 创建全局聊天服务实例
chat_service = ChatService()


def get_chat_service() -> ChatService:
    """获取聊天服务实例。"""
    return chat_service