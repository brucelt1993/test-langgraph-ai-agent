"""
User authentication and RBAC models.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey

from app.core.database import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique user identifier"
    )
    
    # Basic user information
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True,
        comment="Unique username for login"
    )
    
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="User's full name"
    )
    
    # Authentication
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Hashed password"
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Account active status"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="Email verification status"
    )
    
    # RBAC
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User's role ID"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login timestamp"
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    # Relationships
    role: Mapped["Role"] = relationship(
        "Role", 
        back_populates="users",
        lazy="selectin"
    )
    
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        sa.Index("ix_users_email_active", "email", "is_active"),
        sa.Index("ix_users_username_active", "username", "is_active"),
        sa.Index("ix_users_created_at", "created_at"),
        {"comment": "User accounts and authentication"}
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role and self.role.name == "admin"
    
    @property
    def is_deleted(self) -> bool:
        """Check if user is soft deleted."""
        return self.deleted_at is not None


class Role(Base):
    """Role model for RBAC system."""
    
    __tablename__ = "roles"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique role identifier"
    )
    
    # Role information
    name: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        nullable=False,
        index=True,
        comment="Role name (e.g., 'admin', 'user')"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable role name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Role description"
    )
    
    # Permissions (stored as JSON array of permission strings)
    permissions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
        comment="JSON array of permissions"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Role active status"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Role creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="role",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission."""
        import json
        try:
            perms = json.loads(self.permissions)
            return permission in perms
        except (json.JSONDecodeError, TypeError):
            return False
    
    def add_permission(self, permission: str) -> None:
        """Add permission to role."""
        import json
        try:
            perms = json.loads(self.permissions)
            if permission not in perms:
                perms.append(permission)
                self.permissions = json.dumps(perms)
        except (json.JSONDecodeError, TypeError):
            self.permissions = json.dumps([permission])
    
    def remove_permission(self, permission: str) -> None:
        """Remove permission from role."""
        import json
        try:
            perms = json.loads(self.permissions)
            if permission in perms:
                perms.remove(permission)
                self.permissions = json.dumps(perms)
        except (json.JSONDecodeError, TypeError):
            pass


class UserSession(Base):
    """User session model for JWT token management."""
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid4()),
        comment="Unique session identifier"
    )
    
    # User reference
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID for this session"
    )
    
    # Session data
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Hashed JWT token"
    )
    
    device_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Device/browser information"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # Support IPv6
        nullable=True,
        comment="IP address of the session"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Session creation timestamp"
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Session expiration timestamp"
    )
    
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last session usage timestamp"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        sa.Index("ix_sessions_user_expires", "user_id", "expires_at"),
        sa.Index("ix_sessions_expires", "expires_at"),
        {"comment": "User authentication sessions"}
    )
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(timezone.utc) > self.expires_at