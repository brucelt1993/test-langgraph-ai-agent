#!/usr/bin/env python3
"""
后端API接口测试脚本

测试主要的API端点功能是否正常
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional

# API基础URL
BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_data = None
    
    def print_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """打印测试结果"""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        if data and isinstance(data, dict):
            print(f"   📄 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
        print()
    
    async def test_health_check(self):
        """测试健康检查接口"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_result("健康检查", True, "服务运行正常", data)
                    return True
                else:
                    self.print_result("健康检查", False, f"响应状态码: {response.status_code}")
                    return False
        except Exception as e:
            self.print_result("健康检查", False, f"连接失败: {str(e)}")
            return False
    
    async def test_register(self, username: str = "testuser", email: str = "test@example.com", password: str = "test123456"):
        """测试用户注册接口"""
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "username": username,
                    "email": email,
                    "password": password,
                    "full_name": "测试用户"
                }
                
                response = await client.post(f"{self.base_url}/api/v1/auth/register", json=data)
                
                if response.status_code == 201:
                    result = response.json()
                    self.user_data = result
                    self.token = result.get("access_token")
                    self.print_result("用户注册", True, "注册成功", result)
                    return True
                elif response.status_code == 400:
                    error_data = response.json()
                    if "already exists" in error_data.get("detail", ""):
                        self.print_result("用户注册", True, "用户已存在（正常情况）", error_data)
                        return True
                    else:
                        self.print_result("用户注册", False, f"注册失败: {error_data}")
                        return False
                else:
                    self.print_result("用户注册", False, f"响应状态码: {response.status_code}, 内容: {response.text}")
                    return False
        except Exception as e:
            self.print_result("用户注册", False, f"请求失败: {str(e)}")
            return False
    
    async def test_login(self, username: str = "testuser", password: str = "test123456"):
        """测试用户登录接口"""
        try:
            async with httpx.AsyncClient() as client:
                # 使用form data格式，符合OAuth2标准
                data = {
                    "username": username,
                    "password": password
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login", 
                    data=data,  # 使用form data而不是json
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.token = result.get("access_token")
                    self.user_data = result
                    self.print_result("用户登录", True, "登录成功", result)
                    return True
                else:
                    error_text = response.text
                    self.print_result("用户登录", False, f"登录失败 ({response.status_code}): {error_text}")
                    return False
        except Exception as e:
            self.print_result("用户登录", False, f"请求失败: {str(e)}")
            return False
    
    async def test_get_profile(self):
        """测试获取用户信息接口"""
        if not self.token:
            self.print_result("获取用户信息", False, "需要先登录")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = await client.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    self.print_result("获取用户信息", True, "获取成功", result)
                    return True
                else:
                    self.print_result("获取用户信息", False, f"获取失败 ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            self.print_result("获取用户信息", False, f"请求失败: {str(e)}")
            return False
    
    async def test_create_chat_session(self):
        """测试创建聊天会话接口"""
        if not self.token:
            self.print_result("创建聊天会话", False, "需要先登录")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    "title": "测试聊天会话",
                    "description": "这是一个API测试会话"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/chat/sessions", 
                    json=data, 
                    headers=headers
                )
                
                if response.status_code == 201:
                    result = response.json()
                    self.print_result("创建聊天会话", True, "创建成功", result)
                    return result.get("id")
                else:
                    self.print_result("创建聊天会话", False, f"创建失败 ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            self.print_result("创建聊天会话", False, f"请求失败: {str(e)}")
            return None
    
    async def test_send_message(self, session_id: str):
        """测试发送消息接口"""
        if not self.token:
            self.print_result("发送消息", False, "需要先登录")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    "content": "你好，这是一个API测试消息",
                    "message_type": "user"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/chat/sessions/{session_id}/messages", 
                    json=data, 
                    headers=headers
                )
                
                if response.status_code == 201:
                    result = response.json()
                    self.print_result("发送消息", True, "发送成功", result)
                    return True
                else:
                    self.print_result("发送消息", False, f"发送失败 ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            self.print_result("发送消息", False, f"请求失败: {str(e)}")
            return False
    
    async def test_get_sessions(self):
        """测试获取聊天会话列表接口"""
        if not self.token:
            self.print_result("获取会话列表", False, "需要先登录")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.token}"}
                response = await client.get(f"{self.base_url}/api/v1/chat/sessions", headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    self.print_result("获取会话列表", True, f"获取成功，共{len(result.get('items', []))}个会话", result)
                    return True
                else:
                    self.print_result("获取会话列表", False, f"获取失败 ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            self.print_result("获取会话列表", False, f"请求失败: {str(e)}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始后端API接口测试...\n")
        
        # 1. 健康检查
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ 后端服务未启动或无法访问，请先启动后端服务")
            return
        
        # 2. 测试注册
        await self.test_register()
        
        # 3. 测试登录
        login_ok = await self.test_login()
        if not login_ok:
            print("❌ 登录失败，尝试使用管理员账户")
            login_ok = await self.test_login("admin", "password123")
        
        if not login_ok:
            print("❌ 无法登录，跳过需要认证的测试")
            return
        
        # 4. 测试获取用户信息
        await self.test_get_profile()
        
        # 5. 测试聊天功能
        session_id = await self.test_create_chat_session()
        if session_id:
            await self.test_send_message(session_id)
        
        # 6. 测试获取会话列表
        await self.test_get_sessions()
        
        print("🎉 API测试完成！")

async def main():
    tester = APITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())