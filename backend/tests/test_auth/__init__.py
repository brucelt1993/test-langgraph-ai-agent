"""
认证服务测试。
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
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user):
        """测试重复邮箱注册失败。"""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # 与sample_user相同
            "password": "Password123!",
            "full_name": "Different User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, client: AsyncClient):
        """测试弱密码注册失败。"""
        user_data = {
            "username": "weakpassuser",
            "email": "weak@example.com",
            "password": "123",  # 弱密码
            "full_name": "Weak Password User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 422
        assert "validation error" in response.text.lower()

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
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_login_with_email(self, client: AsyncClient, sample_user):
        """测试用邮箱登录成功。"""
        login_data = {
            "username": "test@example.com",  # 使用邮箱
            "password": "TestPassword123!"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user):
        """测试错误密码登录失败。"""
        login_data = {
            "username": "testuser",
            "password": "WrongPassword123!"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """测试不存在用户登录失败。"""
        login_data = {
            "username": "nonexistent",
            "password": "Password123!"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """测试获取当前用户信息。"""
        response = await client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "role" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """测试未授权获取用户信息失败。"""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, sample_user):
        """测试刷新Token成功。"""
        # 先登录获取Token
        login_data = {
            "username": "testuser", 
            "password": "TestPassword123!"
        }
        login_response = await client.post("/api/auth/login", json=login_data)
        tokens = login_response.json()
        
        # 使用refresh token获取新token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        response = await client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """测试无效refresh token失败。"""
        refresh_data = {
            "refresh_token": "invalid_token"
        }
        response = await client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, auth_headers):
        """测试用户登出成功。"""
        response = await client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

    @pytest.mark.asyncio 
    async def test_change_password_success(self, client: AsyncClient, auth_headers):
        """测试修改密码成功。"""
        change_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        }
        
        response = await client.post("/api/auth/change-password", json=change_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, auth_headers):
        """测试当前密码错误修改失败。"""
        change_data = {
            "current_password": "WrongPassword!",
            "new_password": "NewPassword456!"
        }
        
        response = await client.post("/api/auth/change-password", json=change_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "Invalid current password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_profile_success(self, client: AsyncClient, auth_headers):
        """测试更新个人资料成功。"""
        update_data = {
            "full_name": "Updated Test User"
        }
        
        response = await client.put("/api/auth/me", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Test User"

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, client: AsyncClient, auth_headers):
        """测试获取用户会话列表。"""
        response = await client.get("/api/auth/sessions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)