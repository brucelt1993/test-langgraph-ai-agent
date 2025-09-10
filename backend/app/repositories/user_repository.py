"""
User repository for authentication and user management.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import logging

from app.models.user import User, Role, UserSession
from app.repositories.base_repository import BaseRepository, PaginationResult

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model with authentication-specific methods."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            query = (
                select(User)
                .options(selectinload(User.role))
                .where(and_(
                    User.username == username,
                    User.deleted_at.is_(None)
                ))
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            query = (
                select(User)
                .options(selectinload(User.role))
                .where(and_(
                    User.email == email,
                    User.deleted_at.is_(None)
                ))
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        try:
            query = (
                select(User)
                .options(selectinload(User.role))
                .where(and_(
                    or_(
                        User.username == identifier,
                        User.email == identifier
                    ),
                    User.deleted_at.is_(None)
                ))
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user by username or email {identifier}: {e}")
            raise
    
    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role_name: str = "user",
        full_name: Optional[str] = None,
        is_verified: bool = False
    ) -> User:
        """Create a new user with role assignment."""
        try:
            # Get role by name
            role = await self._get_role_by_name(role_name)
            if not role:
                raise ValueError(f"Role '{role_name}' not found")
            
            user = await self.create(
                username=username,
                email=email,
                password_hash=password_hash,
                role_id=role.id,
                full_name=full_name,
                is_verified=is_verified,
                is_active=True
            )
            
            # Load the role relationship
            await self.session.refresh(user, ['role'])
            
            logger.info(f"Created user: {username} ({email}) with role: {role_name}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            raise
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        try:
            await self.update(user_id, last_login_at=datetime.now(timezone.utc))
            logger.debug(f"Updated last login for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {e}")
            raise
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account."""
        try:
            return await self.update(user_id, is_active=True)
            
        except Exception as e:
            logger.error(f"Error activating user {user_id}: {e}")
            raise
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate a user account."""
        try:
            return await self.update(user_id, is_active=False)
            
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise
    
    async def verify_user(self, user_id: str) -> Optional[User]:
        """Verify a user's email."""
        try:
            return await self.update(user_id, is_verified=True)
            
        except Exception as e:
            logger.error(f"Error verifying user {user_id}: {e}")
            raise
    
    async def change_password(self, user_id: str, new_password_hash: str) -> Optional[User]:
        """Change user password."""
        try:
            return await self.update(user_id, password_hash=new_password_hash)
            
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            raise
    
    async def get_active_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> PaginationResult[User]:
        """Get paginated list of active users with optional search."""
        try:
            filters = {"is_active": True, "deleted_at": None}
            
            if search:
                # For search, we need custom query
                query = (
                    select(User)
                    .options(selectinload(User.role))
                    .where(and_(
                        User.is_active == True,
                        User.deleted_at.is_(None),
                        or_(
                            User.username.ilike(f"%{search}%"),
                            User.email.ilike(f"%{search}%"),
                            User.full_name.ilike(f"%{search}%")
                        )
                    ))
                    .order_by(desc(User.created_at))
                )
                
                # Count query for search
                count_query = (
                    select(func.count())
                    .select_from(User)
                    .where(and_(
                        User.is_active == True,
                        User.deleted_at.is_(None),
                        or_(
                            User.username.ilike(f"%{search}%"),
                            User.email.ilike(f"%{search}%"),
                            User.full_name.ilike(f"%{search}%")
                        )
                    ))
                )
                
                # Execute count
                total_result = await self.session.execute(count_query)
                total = total_result.scalar()
                
                # Apply pagination to main query
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
                    order_by="created_at",
                    order_direction="desc",
                    filters=filters
                )
                
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """Get all users with specific role."""
        try:
            query = (
                select(User)
                .join(Role)
                .options(selectinload(User.role))
                .where(and_(
                    Role.name == role_name,
                    User.is_active == True,
                    User.deleted_at.is_(None)
                ))
                .order_by(User.username)
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting users by role {role_name}: {e}")
            raise
    
    async def username_exists(self, username: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if username exists (excluding specific user)."""
        try:
            query = select(func.count()).select_from(User).where(
                and_(
                    User.username == username,
                    User.deleted_at.is_(None)
                )
            )
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await self.session.execute(query)
            return result.scalar() > 0
            
        except Exception as e:
            logger.error(f"Error checking username existence {username}: {e}")
            raise
    
    async def email_exists(self, email: str, exclude_user_id: Optional[str] = None) -> bool:
        """Check if email exists (excluding specific user)."""
        try:
            query = select(func.count()).select_from(User).where(
                and_(
                    User.email == email,
                    User.deleted_at.is_(None)
                )
            )
            
            if exclude_user_id:
                query = query.where(User.id != exclude_user_id)
            
            result = await self.session.execute(query)
            return result.scalar() > 0
            
        except Exception as e:
            logger.error(f"Error checking email existence {email}: {e}")
            raise
    
    async def _get_role_by_name(self, role_name: str) -> Optional[Role]:
        """Get role by name (internal method)."""
        query = select(Role).where(Role.name == role_name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class RoleRepository(BaseRepository[Role]):
    """Repository for Role model."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        try:
            query = select(Role).where(Role.name == name)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting role by name {name}: {e}")
            raise
    
    async def get_active_roles(self) -> List[Role]:
        """Get all active roles."""
        try:
            return await self.get_all(
                filters={"is_active": True},
                order_by="name"
            )
            
        except Exception as e:
            logger.error("Error getting active roles: {e}")
            raise
    
    async def create_role(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> Role:
        """Create a new role with permissions."""
        try:
            import json
            
            role = await self.create(
                name=name,
                display_name=display_name,
                description=description,
                permissions=json.dumps(permissions or []),
                is_active=True
            )
            
            logger.info(f"Created role: {name}")
            return role
            
        except Exception as e:
            logger.error(f"Error creating role {name}: {e}")
            raise


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession model."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSession)
    
    async def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create a new user session."""
        try:
            session = await self.create(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
                device_info=device_info,
                ip_address=ip_address
            )
            
            logger.debug(f"Created session for user: {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            raise
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Get session by token hash."""
        try:
            query = (
                select(UserSession)
                .options(selectinload(UserSession.user))
                .where(UserSession.token_hash == token_hash)
            )
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting session by token hash: {e}")
            raise
    
    async def get_active_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user."""
        try:
            now = datetime.now(timezone.utc)
            query = (
                select(UserSession)
                .where(and_(
                    UserSession.user_id == user_id,
                    UserSession.expires_at > now
                ))
                .order_by(desc(UserSession.last_used_at))
            )
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting active sessions for user {user_id}: {e}")
            raise
    
    async def update_last_used(self, session_id: str) -> Optional[UserSession]:
        """Update session's last used timestamp."""
        try:
            return await self.update(
                session_id,
                last_used_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error updating session last used {session_id}: {e}")
            raise
    
    async def revoke_session(self, session_id: str) -> bool:
        """Revoke (delete) a session."""
        try:
            return await self.delete(session_id, soft_delete=False)
            
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")
            raise
    
    async def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user."""
        try:
            from sqlalchemy import delete
            
            query = delete(UserSession).where(UserSession.user_id == user_id)
            result = await self.session.execute(query)
            await self.session.commit()
            
            count = result.rowcount
            logger.info(f"Revoked {count} sessions for user: {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error revoking sessions for user {user_id}: {e}")
            await self.session.rollback()
            raise
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            from sqlalchemy import delete
            
            now = datetime.now(timezone.utc)
            query = delete(UserSession).where(UserSession.expires_at <= now)
            result = await self.session.execute(query)
            await self.session.commit()
            
            count = result.rowcount
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            await self.session.rollback()
            raise