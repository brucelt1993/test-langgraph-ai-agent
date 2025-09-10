"""
认证流程集成测试。

测试完整的用户认证工作流，包括注册、登录、权限验证等。
"""

import pytest
from httpx import AsyncClient


class TestAuthenticationFlow:
    """认证流程集成测试"""

    @pytest.mark.asyncio
    async def test_complete_user_registration_flow(self, integration_client: AsyncClient):
        """测试完整的用户注册流程"""
        
        # 1. 注册新用户
        registration_data = {
            "username": "newintegrationuser",
            "email": "new@integration.com",
            "password": "NewPassword123!",
            "full_name": "New Integration User"
        }
        
        register_response = await integration_client.post(
            "/api/auth/register", 
            json=registration_data
        )
        
        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["username"] == registration_data["username"]
        assert register_data["email"] == registration_data["email"]
        assert "user_id" in register_data
        
        # 2. 使用新注册的用户登录
        login_response = await integration_client.post("/api/auth/login", json={
            "username": registration_data["username"],
            "password": registration_data["password"]
        })
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # 3. 使用token获取用户信息
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_response = await integration_client.get("/api/auth/me", headers=auth_headers)
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["username"] == registration_data["username"]
        assert user_data["email"] == registration_data["email"]
        assert user_data["full_name"] == registration_data["full_name"]
        assert "role" in user_data

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, authenticated_user_client):
        """测试token刷新流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        initial_tokens = client_data["tokens"]
        
        # 1. 使用refresh token获取新的token
        refresh_response = await client.post("/api/auth/refresh", json={
            "refresh_token": initial_tokens["refresh_token"]
        })
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        
        # 2. 验证新token可以正常使用
        new_auth_headers = {"Authorization": f"Bearer {new_tokens['access_token']}"}
        user_response = await client.get("/api/auth/me", headers=new_auth_headers)
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["username"] == "integrationuser"

    @pytest.mark.asyncio
    async def test_password_change_flow(self, authenticated_user_client):
        """测试密码修改流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        
        # 1. 修改密码
        change_password_response = await client.post("/api/auth/change-password", json={
            "current_password": "UserPassword123!",
            "new_password": "NewUserPassword456!"
        })
        
        assert change_password_response.status_code == 200
        assert "successfully" in change_password_response.json()["message"]
        
        # 2. 使用旧密码登录应该失败
        old_login_response = await client.post("/api/auth/login", json={
            "username": "integrationuser",
            "password": "UserPassword123!"
        })
        
        assert old_login_response.status_code == 401
        
        # 3. 使用新密码登录应该成功
        new_login_response = await client.post("/api/auth/login", json={
            "username": "integrationuser", 
            "password": "NewUserPassword456!"
        })
        
        assert new_login_response.status_code == 200
        new_tokens = new_login_response.json()
        assert "access_token" in new_tokens

    @pytest.mark.asyncio
    async def test_session_management_flow(self, authenticated_user_client):
        """测试会话管理流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        
        # 1. 获取用户会话列表
        sessions_response = await client.get("/api/auth/sessions")
        
        assert sessions_response.status_code == 200
        sessions_data = sessions_response.json()
        assert "sessions" in sessions_data
        assert len(sessions_data["sessions"]) >= 1
        
        session_id = sessions_data["sessions"][0]["id"]
        
        # 2. 撤销特定会话
        revoke_response = await client.delete(f"/api/auth/sessions/{session_id}")
        
        assert revoke_response.status_code == 200
        assert "successfully" in revoke_response.json()["message"]

    @pytest.mark.asyncio
    async def test_logout_flow(self, authenticated_user_client):
        """测试登出流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        
        # 1. 登出
        logout_response = await client.post("/api/auth/logout")
        
        assert logout_response.status_code == 200
        assert "successfully" in logout_response.json()["message"]
        
        # 2. 登出后使用相同token应该失败
        user_response = await client.get("/api/auth/me")
        
        assert user_response.status_code == 401

    @pytest.mark.asyncio
    async def test_profile_update_flow(self, authenticated_user_client):
        """测试个人资料更新流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        
        # 1. 更新个人资料
        update_response = await client.put("/api/auth/me", json={
            "full_name": "Updated Integration User"
        })
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["full_name"] == "Updated Integration User"
        
        # 2. 验证更新是否持久化
        user_response = await client.get("/api/auth/me")
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["full_name"] == "Updated Integration User"


class TestAuthorizationFlow:
    """授权流程集成测试"""

    @pytest.mark.asyncio
    async def test_role_based_access_control(self, authenticated_user_client, authenticated_admin_client):
        """测试基于角色的访问控制"""
        user_client = authenticated_user_client["client"]
        admin_client = authenticated_admin_client["client"]
        
        # 用户应该能够访问用户级别的资源
        user_sessions_response = await user_client.get("/api/chat/sessions")
        assert user_sessions_response.status_code == 200
        
        # 管理员应该能够访问管理员级别的资源
        admin_sessions_response = await admin_client.get("/api/chat/sessions")
        assert admin_sessions_response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, integration_client: AsyncClient):
        """测试未授权访问"""
        # 未认证用户不应该能够访问受保护的资源
        response = await integration_client.get("/api/chat/sessions")
        assert response.status_code == 401
        
        response = await integration_client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_access(self, integration_client: AsyncClient):
        """测试无效token访问"""
        # 使用无效token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        response = await integration_client.get("/api/auth/me", headers=invalid_headers)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, authenticated_user_client):
        """测试过期token处理"""
        # 注意：这个测试在实际场景中需要等待token过期或模拟过期token
        # 这里我们主要测试刷新token的机制
        client_data = authenticated_user_client
        client = client_data["client"]
        tokens = client_data["tokens"]
        
        # 尝试刷新token
        refresh_response = await client.post("/api/auth/refresh", json={
            "refresh_token": tokens["refresh_token"]
        })
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert new_tokens["access_token"] != tokens["access_token"]