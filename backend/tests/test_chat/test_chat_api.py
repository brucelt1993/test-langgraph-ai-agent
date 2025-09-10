"""
聊天API测试。
"""

import pytest
from httpx import AsyncClient


class TestChatAPI:
    """聊天API测试类。"""

    @pytest.mark.asyncio
    async def test_create_chat_session(self, client: AsyncClient, auth_headers):
        """测试创建聊天会话。"""
        session_data = {
            "title": "测试会话",
            "agent_name": "weather_agent",
            "context": {"language": "zh"}
        }
        
        response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试会话"
        assert data["agent_name"] == "weather_agent"

    @pytest.mark.asyncio
    async def test_list_chat_sessions(self, client: AsyncClient, auth_headers):
        """测试获取聊天会话列表。"""
        response = await client.get("/api/chat/sessions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问。"""
        response = await client.post("/api/chat/sessions", json={})
        assert response.status_code == 401