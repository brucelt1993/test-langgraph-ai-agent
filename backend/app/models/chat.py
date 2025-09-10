"""
Chat session and message models.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer, JSON

from app.core.database import Base


class ChatSession(Base):
    """Chat session model for conversation management."""
    
    __tablename__ = "chat_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique chat session identifier"
    )
    
    # User reference
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    # Session metadata
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="New Conversation",
        comment="Session title/name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Session description"
    )
    
    # Session configuration
    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Custom system prompt for this session"
    )
    
    ai_model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="gpt-4",
        comment="AI model used for this session"
    )
    
    temperature: Mapped[Optional[float]] = mapped_column(
        sa.Float,
        nullable=True,
        default=0.7,
        comment="AI temperature setting"
    )
    
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=4096,
        comment="Maximum tokens per response"
    )
    
    # Status and settings
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Session active status"
    )
    
    is_archived: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Session archived status"
    )
    
    is_pinned: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Session pinned status"
    )
    
    # Statistics
    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of messages in session"
    )
    
    token_usage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Total tokens used in session"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Session creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last message timestamp"
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="chat_sessions",
        lazy="selectin"
    )
    
    messages: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        sa.Index("ix_sessions_user_created", "user_id", sa.desc("created_at")),
        sa.Index("ix_sessions_user_updated", "user_id", sa.desc("updated_at")),
        sa.Index("ix_sessions_user_active", "user_id", "is_active"),
        sa.Index("ix_sessions_user_archived", "user_id", "is_archived"),
        {"comment": "Chat conversation sessions"}
    )
    
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, title={self.title}, user_id={self.user_id})>"
    
    @property
    def is_deleted(self) -> bool:
        """Check if session is soft deleted."""
        return self.deleted_at is not None


class Message(Base):
    """Message model for individual chat messages."""
    
    __tablename__ = "messages"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique message identifier"
    )
    
    # Session reference
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chat session ID"
    )
    
    # Message content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Message text content"
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Message role: 'user', 'assistant', 'system', 'tool'"
    )
    
    # Message metadata
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Message order in conversation"
    )
    
    token_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of tokens in message"
    )
    
    # AI-specific fields
    model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI model used for this message"
    )
    
    temperature: Mapped[Optional[float]] = mapped_column(
        sa.Float,
        nullable=True,
        comment="Temperature used for AI response"
    )
    
    finish_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="AI completion finish reason"
    )
    
    # Tool usage
    tool_calls: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of tool calls made"
    )
    
    tool_results: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON array of tool call results"
    )
    
    # Status
    is_edited: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Message has been edited"
    )
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Message has been deleted"
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if generation failed"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Message creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession", 
        back_populates="messages",
        lazy="selectin"
    )
    
    thinking_steps: Mapped[List["ThinkingStep"]] = relationship(
        "ThinkingStep", 
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="ThinkingStep.step_order",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        sa.Index("ix_messages_session_sequence", "session_id", "sequence_number"),
        sa.Index("ix_messages_session_created", "session_id", "created_at"),
        sa.Index("ix_messages_role", "role"),
        sa.UniqueConstraint("session_id", "sequence_number", name="uq_session_sequence"),
        {"comment": "Individual chat messages"}
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


class ThinkingStep(Base):
    """AI thinking process step model."""
    
    __tablename__ = "thinking_steps"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique thinking step identifier"
    )
    
    # Message reference
    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated message ID"
    )
    
    # Step content
    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of thinking step: 'analysis', 'planning', 'execution', 'reflection'"
    )
    
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Step title/summary"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Step content/reasoning"
    )
    
    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Order of this step in the thinking process"
    )
    
    # Metadata
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Processing duration in milliseconds"
    )
    
    confidence: Mapped[Optional[float]] = mapped_column(
        sa.Float,
        nullable=True,
        comment="Confidence score for this step"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Step creation timestamp"
    )
    
    # Relationships
    message: Mapped["Message"] = relationship(
        "Message", 
        back_populates="thinking_steps",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        sa.Index("ix_thinking_message_order", "message_id", "step_order"),
        sa.Index("ix_thinking_type", "step_type"),
        sa.UniqueConstraint("message_id", "step_order", name="uq_message_step_order"),
        {"comment": "AI thinking process steps"}
    )
    
    def __repr__(self) -> str:
        return f"<ThinkingStep(id={self.id}, type={self.step_type}, message_id={self.message_id})>"