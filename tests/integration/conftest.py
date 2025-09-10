"""
集成测试配置和fixture。
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from testcontainers.postgres import PostgresContainer
import docker

from app.core.config import settings
from app.core.database import Base, get_async_db
from app.core.security import PasswordManager
from app.models.user import User, Role
from app.repositories.factory import RepositoryFactory
from main import app


class IntegrationTestConfig:
    """集成测试配置"""
    
    def __init__(self):
        self.postgres_container = None
        self.test_engine = None
        self.TestSessionLocal = None
        
    async def setup_database(self):
        """设置测试数据库"""
        # 启动PostgreSQL测试容器
        self.postgres_container = PostgresContainer("postgres:15-alpine")
        self.postgres_container.start()
        
        # 获取数据库连接信息
        db_url = self.postgres_container.get_connection_url().replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
        
        # 创建异步引擎
        self.test_engine = create_async_engine(
            db_url,
            echo=False,
            poolclass=StaticPool,
        )
        
        # 创建会话工厂
        self.TestSessionLocal = async_sessionmaker(
            self.test_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # 创建表结构
        async with self.test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def teardown_database(self):
        """清理测试数据库"""
        if self.test_engine:
            await self.test_engine.dispose()
        
        if self.postgres_container:
            self.postgres_container.stop()

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.TestSessionLocal() as session:
            yield session


# 全局测试配置实例
test_config = IntegrationTestConfig()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_integration_environment():
    """设置集成测试环境"""
    # 设置环境变量
    os.environ["ENVIRONMENT"] = "integration_test"
    os.environ["LOG_LEVEL"] = "INFO"
    
    # 启动测试数据库
    await test_config.setup_database()
    
    yield
    
    # 清理环境
    await test_config.teardown_database()


@pytest_asyncio.fixture
async def integration_db() -> AsyncGenerator[AsyncSession, None]:
    """集成测试数据库会话"""
    async with test_config.TestSessionLocal() as session:
        yield session
        # 测试后清理数据
        await session.rollback()


@pytest_asyncio.fixture
async def integration_client(integration_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """集成测试HTTP客户端"""
    
    # 重写数据库依赖
    async def override_get_db():
        yield integration_db
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    
    # 清理依赖重写
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def integration_repo_factory(integration_db: AsyncSession) -> RepositoryFactory:
    """集成测试仓库工厂"""
    return RepositoryFactory(integration_db)


@pytest_asyncio.fixture
async def test_user_with_role(integration_db: AsyncSession, integration_repo_factory: RepositoryFactory):
    """创建测试用户和角色"""
    # 创建用户角色
    role_repo = integration_repo_factory.get_role_repository()
    user_role = await role_repo.create_role(
        name="user",
        display_name="普通用户",
        permissions=[
            "chat:create", "chat:read", "chat:update", "chat:delete",
            "message:create", "message:read"
        ]
    )
    
    # 创建管理员角色
    admin_role = await role_repo.create_role(
        name="admin",
        display_name="管理员",
        permissions=["*"]
    )
    
    # 创建普通用户
    user_repo = integration_repo_factory.get_user_repository()
    password_hash = PasswordManager.hash_password("UserPassword123!")
    user = await user_repo.create_user(
        username="integrationuser",
        email="integration@example.com",
        password_hash=password_hash,
        full_name="Integration Test User",
        role_name=user_role.name
    )
    
    # 创建管理员用户
    admin_password_hash = PasswordManager.hash_password("AdminPassword123!")
    admin = await user_repo.create_user(
        username="integrationadmin",
        email="admin@integration.com",
        password_hash=admin_password_hash,
        full_name="Integration Test Admin",
        role_name=admin_role.name
    )
    
    await integration_db.commit()
    
    return {
        "user": user,
        "admin": admin,
        "user_role": user_role,
        "admin_role": admin_role
    }


@pytest.fixture
async def authenticated_user_client(integration_client: AsyncClient, test_user_with_role):
    """已认证的用户客户端"""
    # 登录用户
    login_response = await integration_client.post("/api/auth/login", json={
        "username": "integrationuser",
        "password": "UserPassword123!"
    })
    
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    # 设置认证header
    integration_client.headers.update({
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    
    return {
        "client": integration_client,
        "tokens": tokens,
        "user": test_user_with_role["user"]
    }


@pytest.fixture
async def authenticated_admin_client(integration_client: AsyncClient, test_user_with_role):
    """已认证的管理员客户端"""
    # 登录管理员
    login_response = await integration_client.post("/api/auth/login", json={
        "username": "integrationadmin",
        "password": "AdminPassword123!"
    })
    
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    # 设置认证header
    integration_client.headers.update({
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    
    return {
        "client": integration_client,
        "tokens": tokens,
        "user": test_user_with_role["admin"]
    }


@pytest.fixture
def integration_test_data():
    """集成测试数据"""
    return {
        "valid_chat_session": {
            "title": "集成测试会话",
            "agent_name": "weather_agent",
            "context": {
                "language": "zh",
                "location": "北京"
            }
        },
        "valid_message": {
            "content": "今天北京的天气怎么样？",
            "metadata": {
                "source": "integration_test"
            }
        },
        "weather_query": {
            "location": "北京",
            "language": "zh"
        }
    }


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self, db: AsyncSession, repo_factory: RepositoryFactory):
        self.db = db
        self.repo_factory = repo_factory
        self.created_entities = []
    
    async def create_chat_session(self, user_id: str, **kwargs):
        """创建测试聊天会话"""
        chat_service = self.repo_factory.get_chat_service()
        session = await chat_service.create_session(
            user_id=user_id,
            title=kwargs.get("title", "测试会话"),
            agent_name=kwargs.get("agent_name", "weather_agent"),
            context=kwargs.get("context", {})
        )
        self.created_entities.append(("chat_session", session.id))
        return session
    
    async def create_message(self, session_id: str, **kwargs):
        """创建测试消息"""
        message_repo = self.repo_factory.get_message_repository()
        message = await message_repo.create_message(
            session_id=session_id,
            type=kwargs.get("type", "user"),
            content=kwargs.get("content", "测试消息"),
            metadata=kwargs.get("metadata", {})
        )
        self.created_entities.append(("message", message.id))
        return message
    
    async def cleanup(self):
        """清理创建的测试数据"""
        for entity_type, entity_id in reversed(self.created_entities):
            try:
                if entity_type == "chat_session":
                    session_repo = self.repo_factory.get_chat_session_repository()
                    await session_repo.delete(entity_id)
                elif entity_type == "message":
                    message_repo = self.repo_factory.get_message_repository()
                    await message_repo.delete(entity_id)
            except Exception:
                pass  # 忽略删除错误
        
        await self.db.commit()
        self.created_entities.clear()


@pytest.fixture
async def test_data_manager(integration_db: AsyncSession, integration_repo_factory: RepositoryFactory):
    """测试数据管理器fixture"""
    manager = TestDataManager(integration_db, integration_repo_factory)
    yield manager
    await manager.cleanup()