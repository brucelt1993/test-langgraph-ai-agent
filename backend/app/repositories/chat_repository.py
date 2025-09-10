"""
Chat repository for conversation and message management.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, delete
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timezone
import logging

from app.models.chat import ChatSession, Message, ThinkingStep
from app.repositories.base_repository import BaseRepository, PaginationResult

logger = logging.getLogger(__name__)


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession model."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ChatSession)
    
    async def create_session(
        self,
        user_id: str,
        title: str = "New Conversation",
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        ai_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session = await self.create(
                user_id=user_id,
                title=title,
                description=description,
                system_prompt=system_prompt,
                ai_model=ai_model,
                temperature=temperature,
                max_tokens=max_tokens,
                is_active=True,
                message_count=0,
                token_usage=0
            )
            
            logger.info(f"Created chat session: {session.id} for user: {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating chat session for user {user_id}: {e}")
            raise
    
    async def get_user_sessions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False,
        search: Optional[str] = None
    ) -> PaginationResult[ChatSession]:
        """Get paginated chat sessions for a user."""
        try:
            base_filters = {
                "user_id": user_id,
                "deleted_at": None
            }
            
            if not include_archived:
                base_filters["is_archived"] = False
            
            if search:
                # Custom query for search
                conditions = [
                    ChatSession.user_id == user_id,
                    ChatSession.deleted_at.is_(None)
                ]
                
                if not include_archived:
                    conditions.append(ChatSession.is_archived == False)
                
                conditions.append(
                    or_(
                        ChatSession.title.ilike(f"%{search}%"),
                        ChatSession.description.ilike(f"%{search}%")
                    )
                )
                
                query = (
                    select(ChatSession)
                    .where(and_(*conditions))
                    .order_by(desc(ChatSession.updated_at))
                )
                
                # Count query for search
                count_query = (
                    select(func.count())
                    .select_from(ChatSession)
                    .where(and_(*conditions))
                )
                
                # Execute count
                total_result = await self.session.execute(count_query)
                total = total_result.scalar()
                
                # Apply pagination
                offset = (page - 1) * page_size
                query = query.offset(offset).limit(page_size)
                
                result = await self.session.execute(query)
                items = result.scalars().all()
                
                total_pages = (total + page_size - 1) // page_size
                
                return PaginationResult(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
            else:
                return await self.get_paginated(
                    page=page,
                    page_size=page_size,
                    order_by="updated_at",
                    order_direction="desc",
                    filters=base_filters
                )
                
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            raise
    
    async def get_recent_sessions(self, user_id: str, limit: int = 10) -> List[ChatSession]:
        """Get recent chat sessions for a user."""
        try:
            return await self.get_all(
                limit=limit,
                order_by="last_message_at",
                order_direction="desc",
                filters={
                    "user_id": user_id,
                    "is_active": True,
                    "is_archived": False,
                    "deleted_at": None
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting recent sessions for user {user_id}: {e}")
            raise
    
    async def get_pinned_sessions(self, user_id: str) -> List[ChatSession]:
        """Get pinned chat sessions for a user."""
        try:
            return await self.get_all(
                order_by="updated_at",
                order_direction="desc",
                filters={
                    "user_id": user_id,
                    "is_pinned": True,
                    "deleted_at": None
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting pinned sessions for user {user_id}: {e}")
            raise
    
    async def update_session_activity(
        self,
        session_id: str,
        increment_messages: bool = True,
        add_tokens: int = 0
    ) -> Optional[ChatSession]:
        """Update session activity (message count and token usage)."""
        try:
            session = await self.get_by_id(session_id)
            if not session:
                return None
            
            updates = {
                "updated_at": datetime.now(timezone.utc),
                "last_message_at": datetime.now(timezone.utc)
            }
            
            if increment_messages:
                updates["message_count"] = session.message_count + 1
            
            if add_tokens > 0:
                updates["token_usage"] = session.token_usage + add_tokens
            
            return await self.update(session_id, **updates)
            
        except Exception as e:
            logger.error(f"Error updating session activity {session_id}: {e}")
            raise
    
    async def archive_session(self, session_id: str) -> Optional[ChatSession]:
        """Archive a chat session."""
        try:
            return await self.update(session_id, is_archived=True)
            
        except Exception as e:
            logger.error(f"Error archiving session {session_id}: {e}")
            raise
    
    async def unarchive_session(self, session_id: str) -> Optional[ChatSession]:
        """Unarchive a chat session."""
        try:
            return await self.update(session_id, is_archived=False)
            
        except Exception as e:
            logger.error(f"Error unarchiving session {session_id}: {e}")
            raise
    
    async def pin_session(self, session_id: str) -> Optional[ChatSession]:
        """Pin a chat session."""
        try:
            return await self.update(session_id, is_pinned=True)
            
        except Exception as e:
            logger.error(f"Error pinning session {session_id}: {e}")
            raise
    
    async def unpin_session(self, session_id: str) -> Optional[ChatSession]:
        """Unpin a chat session."""
        try:
            return await self.update(session_id, is_pinned=False)
            
        except Exception as e:
            logger.error(f"Error unpinning session {session_id}: {e}")
            raise


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)
    
    async def create_message(
        self,
        session_id: str,
        content: str,
        role: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        token_count: int = 0,
        tool_calls: Optional[Dict] = None,
        tool_results: Optional[Dict] = None
    ) -> Message:
        """Create a new message."""
        try:
            # Get the next sequence number for this session
            sequence_number = await self._get_next_sequence_number(session_id)
            
            message = await self.create(
                session_id=session_id,
                content=content,
                role=role,
                sequence_number=sequence_number,
                token_count=token_count,
                model=model,
                temperature=temperature,
                tool_calls=tool_calls,
                tool_results=tool_results,
                is_edited=False,
                is_deleted=False
            )
            
            logger.debug(f"Created message: {message.id} in session: {session_id}")
            return message
            
        except Exception as e:
            logger.error(f"Error creating message in session {session_id}: {e}")
            raise
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_deleted: bool = False,
        include_thinking: bool = False
    ) -> List[Message]:
        """Get messages for a chat session."""
        try:
            query = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.sequence_number)
            )
            
            if not include_deleted:
                query = query.where(Message.is_deleted == False)
            
            if include_thinking:
                query = query.options(selectinload(Message.thinking_steps))
            
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            raise
    
    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10,
        include_thinking: bool = False
    ) -> List[Message]:
        """Get recent messages for context window."""
        try:
            query = (
                select(Message)
                .where(and_(
                    Message.session_id == session_id,
                    Message.is_deleted == False
                ))
                .order_by(desc(Message.sequence_number))
                .limit(limit)
            )
            
            if include_thinking:
                query = query.options(selectinload(Message.thinking_steps))
            
            result = await self.session.execute(query)
            messages = result.scalars().all()
            
            # Reverse to get chronological order
            return list(reversed(messages))
            
        except Exception as e:
            logger.error(f"Error getting recent messages for session {session_id}: {e}")
            raise
    
    async def get_conversation_context(
        self,
        session_id: str,
        max_rounds: int = 10
    ) -> List[Message]:
        """Get conversation context (last N rounds of user/assistant messages)."""
        try:
            # Get recent user/assistant messages only
            query = (
                select(Message)
                .where(and_(
                    Message.session_id == session_id,
                    Message.role.in_(["user", "assistant"]),
                    Message.is_deleted == False
                ))
                .order_by(desc(Message.sequence_number))
                .limit(max_rounds * 2)  # Max rounds * 2 for user+assistant pairs
            )
            
            result = await self.session.execute(query)
            messages = result.scalars().all()
            
            # Reverse to get chronological order
            return list(reversed(messages))
            
        except Exception as e:
            logger.error(f"Error getting conversation context for session {session_id}: {e}")
            raise
    
    async def update_message_content(self, message_id: str, content: str) -> Optional[Message]:
        """Update message content and mark as edited."""
        try:
            return await self.update(
                message_id,
                content=content,
                is_edited=True,
                updated_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error updating message {message_id}: {e}")
            raise
    
    async def delete_message(self, message_id: str, soft_delete: bool = True) -> bool:
        """Delete a message."""
        try:
            if soft_delete:
                result = await self.update(message_id, is_deleted=True)
                return result is not None
            else:
                return await self.delete(message_id, soft_delete=False)
                
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            raise
    
    async def get_message_stats(self, session_id: str) -> Dict[str, Any]:
        """Get message statistics for a session."""
        try:
            query = (
                select(
                    func.count(Message.id).label("total_messages"),
                    func.sum(Message.token_count).label("total_tokens"),
                    func.count(Message.id).filter(Message.role == "user").label("user_messages"),
                    func.count(Message.id).filter(Message.role == "assistant").label("assistant_messages"),
                    func.count(Message.id).filter(Message.is_deleted == True).label("deleted_messages")
                )
                .where(Message.session_id == session_id)
            )
            
            result = await self.session.execute(query)
            stats = result.first()
            
            return {
                "total_messages": stats.total_messages or 0,
                "total_tokens": stats.total_tokens or 0,
                "user_messages": stats.user_messages or 0,
                "assistant_messages": stats.assistant_messages or 0,
                "deleted_messages": stats.deleted_messages or 0
            }
            
        except Exception as e:
            logger.error(f"Error getting message stats for session {session_id}: {e}")
            raise
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """Get the next sequence number for a session."""
        query = (
            select(func.coalesce(func.max(Message.sequence_number), 0) + 1)
            .where(Message.session_id == session_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar()


class ThinkingStepRepository(BaseRepository[ThinkingStep]):
    """Repository for ThinkingStep model."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ThinkingStep)
    
    async def create_thinking_step(
        self,
        message_id: str,
        step_type: str,
        content: str,
        title: Optional[str] = None,
        duration_ms: Optional[int] = None,
        confidence: Optional[float] = None
    ) -> ThinkingStep:
        """Create a new thinking step."""
        try:
            # Get the next step order for this message
            step_order = await self._get_next_step_order(message_id)
            
            step = await self.create(
                message_id=message_id,
                step_type=step_type,
                title=title,
                content=content,
                step_order=step_order,
                duration_ms=duration_ms,
                confidence=confidence
            )
            
            logger.debug(f"Created thinking step: {step.id} for message: {message_id}")
            return step
            
        except Exception as e:
            logger.error(f"Error creating thinking step for message {message_id}: {e}")
            raise
    
    async def get_message_thinking_steps(self, message_id: str) -> List[ThinkingStep]:
        """Get all thinking steps for a message."""
        try:
            return await self.get_all(
                filters={"message_id": message_id},
                order_by="step_order",
                order_direction="asc"
            )
            
        except Exception as e:
            logger.error(f"Error getting thinking steps for message {message_id}: {e}")
            raise
    
    async def get_steps_by_type(self, message_id: str, step_type: str) -> List[ThinkingStep]:
        """Get thinking steps of specific type for a message."""
        try:
            return await self.get_all(
                filters={"message_id": message_id, "step_type": step_type},
                order_by="step_order",
                order_direction="asc"
            )
            
        except Exception as e:
            logger.error(f"Error getting {step_type} thinking steps for message {message_id}: {e}")
            raise
    
    async def delete_message_thinking_steps(self, message_id: str) -> int:
        """Delete all thinking steps for a message."""
        try:
            query = delete(ThinkingStep).where(ThinkingStep.message_id == message_id)
            result = await self.session.execute(query)
            await self.session.commit()
            
            count = result.rowcount
            logger.debug(f"Deleted {count} thinking steps for message: {message_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting thinking steps for message {message_id}: {e}")
            await self.session.rollback()
            raise
    
    async def _get_next_step_order(self, message_id: str) -> int:
        """Get the next step order for a message."""
        query = (
            select(func.coalesce(func.max(ThinkingStep.step_order), 0) + 1)
            .where(ThinkingStep.message_id == message_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar()