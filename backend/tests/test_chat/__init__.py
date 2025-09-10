"""
聊天API测试。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.repositories.factory import RepositoryFactory


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
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_chat_sessions(self, client: AsyncClient, auth_headers):
        """测试获取聊天会话列表。"""
        # 先创建一个会话
        session_data = {
            "title": "列表测试会话",
            "agent_name": "weather_agent"
        }
        await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        
        # 获取列表
        response = await client.get("/api/chat/sessions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1
        assert data["sessions"][0]["title"] == "列表测试会话"

    @pytest.mark.asyncio
    async def test_get_chat_session(self, client: AsyncClient, auth_headers):
        """测试获取特定聊天会话。"""
        # 先创建一个会话
        session_data = {
            "title": "获取测试会话",
            "agent_name": "weather_agent"
        }
        create_response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        session_id = create_response.json()["id"]
        
        # 获取会话
        response = await client.get(f"/api/chat/sessions/{session_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["title"] == "获取测试会话"

    @pytest.mark.asyncio
    async def test_update_chat_session(self, client: AsyncClient, auth_headers):
        """测试更新聊天会话。"""
        # 先创建一个会话
        session_data = {
            "title": "更新前标题",
            "agent_name": "weather_agent"
        }
        create_response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        session_id = create_response.json()["id"]
        
        # 更新会话
        update_data = {
            "title": "更新后标题"
        }
        response = await client.put(f"/api/chat/sessions/{session_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后标题"

    @pytest.mark.asyncio
    async def test_delete_chat_session(self, client: AsyncClient, auth_headers):
        """测试删除聊天会话。"""
        # 先创建一个会话
        session_data = {
            "title": "删除测试会话",
            "agent_name": "weather_agent"
        }
        create_response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        session_id = create_response.json()["id"]
        
        # 删除会话
        response = await client.delete(f"/api/chat/sessions/{session_id}", headers=auth_headers)
        
        assert response.status_code == 200
        
        # 验证会话已被删除
        get_response = await client.get(f"/api/chat/sessions/{session_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message(self, client: AsyncClient, auth_headers):
        """测试发送消息。"""
        # 先创建一个会话
        session_data = {
            "title": "消息测试会话",
            "agent_name": "weather_agent"
        }
        create_response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        session_id = create_response.json()["id"]
        
        # 发送消息
        message_data = {
            "session_id": session_id,
            "content": "今天北京的天气怎么样？"
        }
        response = await client.post(f"/api/chat/sessions/{session_id}/messages", json=message_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "今天北京的天气怎么样？"
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_get_messages(self, client: AsyncClient, auth_headers):
        """测试获取消息列表。"""
        # 先创建会话和消息
        session_data = {
            "title": "消息列表测试",
            "agent_name": "weather_agent"
        }
        create_response = await client.post("/api/chat/sessions", json=session_data, headers=auth_headers)
        session_id = create_response.json()["id"]
        
        message_data = {
            "session_id": session_id,
            "content": "测试消息"
        }
        await client.post(f"/api/chat/sessions/{session_id}/messages", json=message_data, headers=auth_headers)
        
        # 获取消息列表
        response = await client.get(f"/api/chat/sessions/{session_id}/messages", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """测试未授权访问。"""
        # 尝试无认证创建会话
        session_data = {
            "title": "未授权会话",
            "agent_name": "weather_agent"
        }
        response = await client.post("/api/chat/sessions", json=session_data)
        
        assert response.status_code == 401