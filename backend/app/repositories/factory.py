"""
Repository factory for dependency injection and session management.
"""

from typing import Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import logging

from app.core.database import get_async_db
from app.repositories import (
    BaseRepository, 
    UserRepository, 
    RoleRepository, 
    UserSessionRepository,
    ChatSessionRepository, 
    MessageRepository, 
    ThinkingStepRepository
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseRepository)


class RepositoryFactory:
    """Factory class for creating repository instances with proper session management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories = {}
    
    def get_user_repository(self) -> UserRepository:
        """Get UserRepository instance."""
        if 'user' not in self._repositories:
            self._repositories['user'] = UserRepository(self.session)
        return self._repositories['user']
    
    def get_role_repository(self) -> RoleRepository:
        """Get RoleRepository instance."""
        if 'role' not in self._repositories:
            self._repositories['role'] = RoleRepository(self.session)
        return self._repositories['role']
    
    def get_user_session_repository(self) -> UserSessionRepository:
        """Get UserSessionRepository instance."""
        if 'user_session' not in self._repositories:
            self._repositories['user_session'] = UserSessionRepository(self.session)
        return self._repositories['user_session']
    
    def get_chat_session_repository(self) -> ChatSessionRepository:
        """Get ChatSessionRepository instance."""
        if 'chat_session' not in self._repositories:
            self._repositories['chat_session'] = ChatSessionRepository(self.session)
        return self._repositories['chat_session']
    
    def get_message_repository(self) -> MessageRepository:
        """Get MessageRepository instance.""" 
        if 'message' not in self._repositories:
            self._repositories['message'] = MessageRepository(self.session)
        return self._repositories['message']
    
    def get_thinking_step_repository(self) -> ThinkingStepRepository:
        """Get ThinkingStepRepository instance."""
        if 'thinking_step' not in self._repositories:
            self._repositories['thinking_step'] = ThinkingStepRepository(self.session)
        return self._repositories['thinking_step']
    
    async def commit(self):
        """Commit the current transaction."""
        try:
            await self.session.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            logger.error(f"Error committing transaction: {e}")
            await self.session.rollback()
            raise
    
    async def rollback(self):
        """Rollback the current transaction."""
        try:
            await self.session.rollback()
            logger.debug("Transaction rolled back")
        except Exception as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise


@asynccontextmanager
async def get_repository_factory():
    """Context manager to get repository factory with proper session handling."""
    async for session in get_async_db():
        try:
            factory = RepositoryFactory(session)
            yield factory
        except Exception as e:
            logger.error(f"Error in repository factory context: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Convenience functions for dependency injection
async def get_user_repository() -> UserRepository:
    """Dependency injection for UserRepository."""
    async for session in get_async_db():
        yield UserRepository(session)


async def get_role_repository() -> RoleRepository:
    """Dependency injection for RoleRepository."""
    async for session in get_async_db():
        yield RoleRepository(session)


async def get_user_session_repository() -> UserSessionRepository:
    """Dependency injection for UserSessionRepository."""
    async for session in get_async_db():
        yield UserSessionRepository(session)


async def get_chat_session_repository() -> ChatSessionRepository:
    """Dependency injection for ChatSessionRepository."""
    async for session in get_async_db():
        yield ChatSessionRepository(session)


async def get_message_repository() -> MessageRepository:
    """Dependency injection for MessageRepository."""
    async for session in get_async_db():
        yield MessageRepository(session)


async def get_thinking_step_repository() -> ThinkingStepRepository:
    """Dependency injection for ThinkingStepRepository."""
    async for session in get_async_db():
        yield ThinkingStepRepository(session)


# Repository registry for service layer
class RepositoryRegistry:
    """Registry pattern for repository management in services."""
    
    _repositories = {}
    
    @classmethod
    def register(cls, name: str, repository_class: Type[T]) -> None:
        """Register a repository class."""
        cls._repositories[name] = repository_class
        logger.debug(f"Registered repository: {name}")
    
    @classmethod
    def get(cls, name: str, session: AsyncSession) -> T:
        """Get repository instance by name."""
        if name not in cls._repositories:
            raise ValueError(f"Repository '{name}' not registered")
        
        repository_class = cls._repositories[name]
        return repository_class(session)
    
    @classmethod
    def list_registered(cls) -> list[str]:
        """List all registered repositories."""
        return list(cls._repositories.keys())


# Register all repositories
RepositoryRegistry.register("user", UserRepository)
RepositoryRegistry.register("role", RoleRepository) 
RepositoryRegistry.register("user_session", UserSessionRepository)
RepositoryRegistry.register("chat_session", ChatSessionRepository)
RepositoryRegistry.register("message", MessageRepository)
RepositoryRegistry.register("thinking_step", ThinkingStepRepository)