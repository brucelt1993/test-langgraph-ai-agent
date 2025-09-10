"""
聊天流程集成测试。

测试完整的聊天工作流，包括会话管理、消息发送、AI交互等。
"""

import pytest
import asyncio
from httpx import AsyncClient


class TestChatSessionFlow:
    """聊天会话流程集成测试"""

    @pytest.mark.asyncio
    async def test_complete_chat_session_lifecycle(self, authenticated_user_client, integration_test_data):
        """测试完整的聊天会话生命周期"""
        client_data = authenticated_user_client
        client = client_data["client"]
        test_data = integration_test_data
        
        # 1. 创建聊天会话
        session_data = test_data["valid_chat_session"]
        create_response = await client.post("/api/chat/sessions", json=session_data)
        
        assert create_response.status_code == 200
        session = create_response.json()
        assert session["title"] == session_data["title"]
        assert session["agent_name"] == session_data["agent_name"]
        assert "id" in session
        session_id = session["id"]
        
        # 2. 获取会话列表，验证会话已创建
        list_response = await client.get("/api/chat/sessions")
        
        assert list_response.status_code == 200
        sessions_data = list_response.json()
        assert "sessions" in sessions_data
        assert len(sessions_data["sessions"]) >= 1
        
        # 查找我们创建的会话
        created_session = next(
            (s for s in sessions_data["sessions"] if s["id"] == session_id), 
            None
        )
        assert created_session is not None
        assert created_session["title"] == session_data["title"]
        
        # 3. 获取特定会话详情
        get_response = await client.get(f"/api/chat/sessions/{session_id}")
        
        assert get_response.status_code == 200
        session_detail = get_response.json()
        assert session_detail["id"] == session_id
        assert session_detail["title"] == session_data["title"]
        
        # 4. 更新会话
        update_data = {"title": "更新后的会话标题"}
        update_response = await client.put(f"/api/chat/sessions/{session_id}", json=update_data)
        
        assert update_response.status_code == 200
        updated_session = update_response.json()
        assert updated_session["title"] == update_data["title"]
        
        # 5. 获取会话统计信息
        stats_response = await client.get(f"/api/chat/sessions/{session_id}/stats")
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert "total_messages" in stats
        assert stats["total_messages"] == 0  # 新会话应该没有消息
        
        # 6. 删除会话
        delete_response = await client.delete(f"/api/chat/sessions/{session_id}")
        
        assert delete_response.status_code == 200
        
        # 7. 验证会话已被删除
        get_deleted_response = await client.get(f"/api/chat/sessions/{session_id}")
        assert get_deleted_response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_message_flow(self, authenticated_user_client, integration_test_data, test_data_manager):
        """测试聊天消息流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        user = client_data["user"]
        test_data = integration_test_data
        
        # 1. 创建聊天会话
        session = await test_data_manager.create_chat_session(
            user_id=user.id,
            **test_data["valid_chat_session"]
        )
        session_id = session.id
        
        # 2. 发送用户消息
        message_data = {
            "session_id": session_id,
            "content": test_data["valid_message"]["content"],
            "metadata": test_data["valid_message"]["metadata"]
        }
        
        send_response = await client.post(
            f"/api/chat/sessions/{session_id}/messages", 
            json=message_data
        )
        
        assert send_response.status_code == 200
        sent_message = send_response.json()
        assert sent_message["content"] == message_data["content"]
        assert sent_message["session_id"] == session_id
        assert sent_message["type"] == "user"
        
        # 3. 获取会话消息列表
        messages_response = await client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert messages_response.status_code == 200
        messages_data = messages_response.json()
        assert "data" in messages_data
        assert len(messages_data["data"]) >= 1
        
        # 找到我们发送的消息
        user_message = next(
            (m for m in messages_data["data"] if m["type"] == "user"),
            None
        )
        assert user_message is not None
        assert user_message["content"] == message_data["content"]
        
        # 4. 验证会话统计信息更新
        stats_response = await client.get(f"/api/chat/sessions/{session_id}/stats")
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_messages"] >= 1
        assert stats["user_message_count"] >= 1

    @pytest.mark.asyncio
    async def test_chat_pagination(self, authenticated_user_client, test_data_manager):
        """测试聊天分页功能"""
        client_data = authenticated_user_client
        client = client_data["client"]
        user = client_data["user"]
        
        # 1. 创建会话
        session = await test_data_manager.create_chat_session(
            user_id=user.id,
            title="分页测试会话"
        )
        session_id = session.id
        
        # 2. 创建多条消息用于分页测试
        message_count = 15
        for i in range(message_count):
            await test_data_manager.create_message(
                session_id=session_id,
                content=f"测试消息 {i + 1}",
                type="user"
            )
        
        # 3. 测试分页获取消息
        page1_response = await client.get(
            f"/api/chat/sessions/{session_id}/messages?page=1&size=10"
        )
        
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["data"]) == 10
        assert page1_data["total"] == message_count
        assert page1_data["page"] == 1
        assert page1_data["pages"] == 2
        
        # 4. 获取第二页
        page2_response = await client.get(
            f"/api/chat/sessions/{session_id}/messages?page=2&size=10"
        )
        
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["data"]) == 5  # 剩余的5条消息
        assert page2_data["page"] == 2

    @pytest.mark.asyncio
    async def test_multiple_user_isolation(self, integration_client: AsyncClient, test_user_with_role):
        """测试多用户数据隔离"""
        # 创建第二个用户
        user2_data = {
            "username": "integrationuser2",
            "email": "user2@integration.com",
            "password": "User2Password123!",
            "full_name": "Integration User 2"
        }
        
        register_response = await integration_client.post("/api/auth/register", json=user2_data)
        assert register_response.status_code == 201
        
        # 用户1登录
        user1_login = await integration_client.post("/api/auth/login", json={
            "username": "integrationuser",
            "password": "UserPassword123!"
        })
        user1_tokens = user1_login.json()
        user1_headers = {"Authorization": f"Bearer {user1_tokens['access_token']}"}
        
        # 用户2登录
        user2_login = await integration_client.post("/api/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        user2_tokens = user2_login.json()
        user2_headers = {"Authorization": f"Bearer {user2_tokens['access_token']}"}
        
        # 用户1创建会话
        session_data = {
            "title": "用户1的会话",
            "agent_name": "weather_agent"
        }
        user1_session_response = await integration_client.post(
            "/api/chat/sessions", 
            json=session_data, 
            headers=user1_headers
        )
        assert user1_session_response.status_code == 200
        user1_session = user1_session_response.json()
        
        # 用户2不应该能看到用户1的会话
        user2_sessions_response = await integration_client.get(
            "/api/chat/sessions", 
            headers=user2_headers
        )
        assert user2_sessions_response.status_code == 200
        user2_sessions = user2_sessions_response.json()
        
        # 验证用户2的会话列表中没有用户1的会话
        user2_session_ids = [s["id"] for s in user2_sessions["sessions"]]
        assert user1_session["id"] not in user2_session_ids
        
        # 用户2不应该能直接访问用户1的会话
        access_user1_session_response = await integration_client.get(
            f"/api/chat/sessions/{user1_session['id']}", 
            headers=user2_headers
        )
        assert access_user1_session_response.status_code == 404


class TestAIInteractionFlow:
    """AI交互流程集成测试"""

    @pytest.mark.asyncio  
    async def test_weather_agent_interaction(self, authenticated_user_client, test_data_manager, integration_test_data):
        """测试天气Agent交互流程"""
        client_data = authenticated_user_client
        client = client_data["client"]
        user = client_data["user"]
        test_data = integration_test_data
        
        # 1. 创建天气Agent会话
        session = await test_data_manager.create_chat_session(
            user_id=user.id,
            title="天气查询测试",
            agent_name="weather_agent",
            context={"language": "zh"}
        )
        session_id = session.id
        
        # 2. 发送天气查询消息
        weather_message = {
            "session_id": session_id,
            "content": "今天北京的天气怎么样？",
            "metadata": {"query_type": "weather"}
        }
        
        send_response = await client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=weather_message
        )
        
        assert send_response.status_code == 200
        user_message = send_response.json()
        assert user_message["content"] == weather_message["content"]
        
        # 3. 等待AI响应 (在实际实现中，这会触发异步的AI处理)
        # 这里我们主要测试消息是否正确创建和存储
        await asyncio.sleep(1)  # 模拟处理时间
        
        # 4. 检查消息历史
        messages_response = await client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert messages_response.status_code == 200
        messages_data = messages_response.json()
        assert len(messages_data["data"]) >= 1
        
        # 验证用户消息存在
        user_messages = [m for m in messages_data["data"] if m["type"] == "user"]
        assert len(user_messages) >= 1
        assert user_messages[0]["content"] == weather_message["content"]

    @pytest.mark.asyncio
    async def test_conversation_context_maintenance(self, authenticated_user_client, test_data_manager):
        """测试对话上下文维护"""
        client_data = authenticated_user_client
        client = client_data["client"]
        user = client_data["user"]
        
        # 1. 创建会话
        session = await test_data_manager.create_chat_session(
            user_id=user.id,
            title="上下文测试会话",
            agent_name="weather_agent"
        )
        session_id = session.id
        
        # 2. 发送多轮对话消息
        messages = [
            "你好，我想了解天气信息",
            "北京今天的天气如何？",
            "明天会下雨吗？",
            "这周的天气趋势怎么样？"
        ]
        
        sent_messages = []
        for content in messages:
            message_data = {
                "session_id": session_id,
                "content": content
            }
            
            send_response = await client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json=message_data
            )
            
            assert send_response.status_code == 200
            sent_messages.append(send_response.json())
        
        # 3. 验证消息顺序和完整性
        messages_response = await client.get(f"/api/chat/sessions/{session_id}/messages")
        
        assert messages_response.status_code == 200
        stored_messages = messages_response.json()["data"]
        
        # 验证所有用户消息都被正确存储
        user_messages = [m for m in stored_messages if m["type"] == "user"]
        assert len(user_messages) == len(messages)
        
        # 验证消息内容匹配
        for i, message in enumerate(messages):
            assert user_messages[i]["content"] == message

    @pytest.mark.asyncio
    async def test_concurrent_chat_sessions(self, authenticated_user_client, test_data_manager):
        """测试并发聊天会话"""
        client_data = authenticated_user_client
        client = client_data["client"]
        user = client_data["user"]
        
        # 1. 并发创建多个会话
        session_tasks = []
        for i in range(5):
            task = test_data_manager.create_chat_session(
                user_id=user.id,
                title=f"并发会话 {i + 1}",
                agent_name="weather_agent"
            )
            session_tasks.append(task)
        
        sessions = await asyncio.gather(*session_tasks)
        assert len(sessions) == 5
        
        # 2. 在每个会话中并发发送消息
        message_tasks = []
        for i, session in enumerate(sessions):
            message_data = {
                "session_id": session.id,
                "content": f"这是会话 {i + 1} 的消息"
            }
            
            task = client.post(
                f"/api/chat/sessions/{session.id}/messages",
                json=message_data
            )
            message_tasks.append(task)
        
        message_responses = await asyncio.gather(*message_tasks)
        
        # 3. 验证所有消息都成功发送
        for response in message_responses:
            assert response.status_code == 200
        
        # 4. 验证每个会话的消息数量
        for session in sessions:
            messages_response = await client.get(f"/api/chat/sessions/{session.id}/messages")
            assert messages_response.status_code == 200
            
            messages_data = messages_response.json()
            user_messages = [m for m in messages_data["data"] if m["type"] == "user"]
            assert len(user_messages) >= 1