"""
认证API测试。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.factory import RepositoryFactory
from app.core.security import PasswordManager


class TestAuthAPI:
    """认证API测试类。"""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, async_db: AsyncSession):
        """测试用户注册成功。"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "NewPassword123!",
            "full_name": "New User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, client: AsyncClient, sample_user):
        """测试重复用户名注册失败。"""
        user_data = {
            "username": "testuser",  # 与sample_user相同
            "email": "different@example.com",
            "password": "Password123!",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user):
        """测试用户登录成功。"""
        login_data = {
            "username": "testuser",
            "password": "TestPassword123!"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """测试获取当前用户信息。"""
        response = await client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"