"""
Database configuration and setup.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_async_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    
    # 初始化默认数据
    await initialize_default_data()


async def initialize_default_data():
    """初始化默认数据（角色等）。"""
    try:
        from app.repositories.factory import get_repository_factory
        from app.core.permissions import permission_registry
        
        async with get_repository_factory() as repo_factory:
            role_repo = repo_factory.get_role_repository()
            
            # 检查是否已有角色数据
            existing_roles = await role_repo.get_all()
            if existing_roles:
                logger.info("Default roles already exist, skipping initialization")
                return
            
            # 创建默认角色
            default_roles = permission_registry.get_all_roles()
            
            for role_name, role_def in default_roles.items():
                await role_repo.create_role(
                    name=role_def.name,
                    display_name=role_def.display_name,
                    description=role_def.description,
                    permissions=[p.value for p in role_def.permissions]
                )
            
            await repo_factory.commit()
            logger.info(f"Created {len(default_roles)} default roles")
            
    except Exception as e:
        logger.error(f"Failed to initialize default data: {e}")
        # 不抛出异常，让应用继续启动


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")


async def close_db():
    """Close database connection pool."""
    await engine.dispose()
    logger.info("Database connection pool closed")