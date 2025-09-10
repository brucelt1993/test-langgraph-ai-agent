"""
Pytest配置和共享fixture。
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_async_db
from app.core.security import PasswordManager
from app.models.user import User, Role
from app.repositories.factory import RepositoryFactory
from main import app


# 测试数据库URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# 创建测试会话工厂
TestSessionLocal = async_sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def async_db() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话。"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话
    async with TestSessionLocal() as session:
        yield session
    
    # 清理表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(async_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试HTTP客户端。"""
    
    # 重写数据库依赖
    async def override_get_db():
        yield async_db
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    
    # 清理依赖重写
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def repo_factory(async_db: AsyncSession) -> RepositoryFactory:
    """创建测试仓库工厂。"""
    return RepositoryFactory(async_db)


@pytest.fixture(scope="function")
def sample_user_data() -> dict:
    """示例用户数据。"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest_asyncio.fixture(scope="function")
async def sample_user(async_db: AsyncSession, repo_factory: RepositoryFactory) -> User:
    """创建示例用户。"""
    user_repo = repo_factory.get_user_repository()
    
    # 先创建默认角色
    role_repo = repo_factory.get_role_repository()
    role = await role_repo.create_role(
        name="user",
        display_name="普通用户",
        permissions=["chat:create", "chat:read"]
    )
    
    # 创建用户
    password_hash = PasswordManager.hash_password("TestPassword123!")
    user = await user_repo.create_user(
        username="testuser",
        email="test@example.com",
        password_hash=password_hash,
        full_name="Test User",
        role_name=role.name
    )
    
    await async_db.commit()
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(async_db: AsyncSession, repo_factory: RepositoryFactory) -> User:
    """创建管理员用户。"""
    user_repo = repo_factory.get_user_repository()
    
    # 创建管理员角色
    role_repo = repo_factory.get_role_repository()
    admin_role = await role_repo.create_role(
        name="admin",
        display_name="管理员",
        permissions=["*"]  # 所有权限
    )
    
    # 创建管理员用户
    password_hash = PasswordManager.hash_password("AdminPassword123!")
    admin = await user_repo.create_user(
        username="admin",
        email="admin@example.com",
        password_hash=password_hash,
        full_name="Administrator",
        role_name=admin_role.name
    )
    
    await async_db.commit()
    return admin


@pytest.fixture(scope="function")
def auth_headers(sample_user: User) -> dict:
    """生成认证头。"""
    from app.core.security import create_user_tokens
    
    user_data = {
        "username": sample_user.username,
        "email": sample_user.email,
        "role": sample_user.role.name if sample_user.role else "user",
        "permissions": sample_user.role.permissions if sample_user.role else "[]"
    }
    
    tokens = create_user_tokens(sample_user.id, user_data)
    
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture(scope="function")
def admin_headers(admin_user: User) -> dict:
    """生成管理员认证头。"""
    from app.core.security import create_user_tokens
    
    user_data = {
        "username": admin_user.username,
        "email": admin_user.email,
        "role": admin_user.role.name if admin_user.role else "admin",
        "permissions": admin_user.role.permissions if admin_user.role else "[]"
    }
    
    tokens = create_user_tokens(admin_user.id, user_data)
    
    return {
        "Authorization": f"Bearer {tokens['access_token']}"
    }


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """设置测试环境变量。"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")


# 测试数据清理
@pytest.fixture(autouse=True)
async def cleanup():
    """测试后清理。"""
    yield
    # 测试后清理逻辑
    if os.path.exists("test.db"):
        os.remove("test.db")