# API参考文档

## 概述

AI Agent API基于REST架构，支持JSON格式的请求和响应。所有API端点都需要适当的身份验证，除了公共端点如健康检查。

## 基础信息

- **基础URL**: `http://localhost:8000/api`
- **生产URL**: `https://yourdomain.com/api`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **编码**: UTF-8

## 认证

### JWT Token认证

大多数API端点需要JWT token进行身份验证。

#### 获取Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "username": "your_username",
    "email": "your_email@example.com",
    "full_name": "Your Full Name",
    "role": "user"
  }
}
```

#### 使用Token

在请求头中包含token：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API端点

### 认证接口

#### POST /auth/register

注册新用户。

**请求体:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string"
}
```

**响应:**
```json
{
  "message": "用户注册成功",
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST /auth/login

用户登录。

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

#### POST /auth/refresh

刷新访问token。

**请求体:**
```json
{
  "refresh_token": "string"
}
```

#### POST /auth/logout

用户登出。

**请求头:**
```http
Authorization: Bearer <access_token>
```

### 聊天接口

#### GET /chat/sessions

获取用户的聊天会话列表。

**查询参数:**
- `page`: int = 1 - 页码
- `size`: int = 10 - 每页大小
- `search`: str = None - 搜索关键词

**响应:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "聊天会话标题",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "message_count": 5
    }
  ],
  "total": 20,
  "page": 1,
  "size": 10,
  "pages": 2
}
```

#### POST /chat/sessions

创建新的聊天会话。

**请求体:**
```json
{
  "title": "会话标题"
}
```

**响应:**
```json
{
  "id": "uuid",
  "title": "会话标题",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "message_count": 0
}
```

#### GET /chat/sessions/{session_id}

获取特定聊天会话的详细信息。

**路径参数:**
- `session_id`: uuid - 会话ID

**响应:**
```json
{
  "id": "uuid",
  "title": "会话标题",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "messages": [
    {
      "id": "uuid",
      "content": "消息内容",
      "role": "user|assistant",
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": {}
    }
  ]
}
```

#### DELETE /chat/sessions/{session_id}

删除聊天会话。

#### GET /chat/sessions/{session_id}/messages

获取会话的消息列表。

**查询参数:**
- `page`: int = 1
- `size`: int = 20

#### POST /chat/sessions/{session_id}/messages

向会话发送新消息。

**请求体:**
```json
{
  "content": "用户消息内容",
  "metadata": {}
}
```

**响应:**
```json
{
  "id": "uuid",
  "content": "用户消息内容",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z",
  "session_id": "uuid",
  "metadata": {}
}
```

### 流式聊天接口

#### GET /chat/stream/{session_id}

建立SSE连接进行实时聊天。

**查询参数:**
- `message`: str - 用户消息

**响应格式 (Server-Sent Events):**

```
data: {"type": "thinking", "content": "AI正在思考..."}

data: {"type": "message_start", "message_id": "uuid"}

data: {"type": "content", "content": "AI响应的一部分"}

data: {"type": "content", "content": "AI响应的另一部分"}

data: {"type": "message_end", "message_id": "uuid"}

data: {"type": "done"}
```

### 用户接口

#### GET /users/me

获取当前用户信息。

**响应:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "string",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "profile": {
    "avatar_url": "string",
    "bio": "string",
    "preferences": {}
  }
}
```

#### PUT /users/me

更新当前用户信息。

**请求体:**
```json
{
  "full_name": "string",
  "email": "string",
  "profile": {
    "bio": "string",
    "preferences": {}
  }
}
```

#### PUT /users/me/password

修改用户密码。

**请求体:**
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

### 管理接口

#### GET /admin/users

获取所有用户列表（需要管理员权限）。

#### GET /admin/stats

获取系统统计信息（需要管理员权限）。

**响应:**
```json
{
  "total_users": 100,
  "active_users": 85,
  "total_sessions": 500,
  "total_messages": 2000,
  "api_calls_today": 150,
  "system_health": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  }
}
```

### 健康检查接口

#### GET /health

系统健康检查（无需认证）。

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  }
}
```

## 错误处理

### 错误格式

所有错误响应都遵循统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述信息",
    "details": "详细错误信息（可选）",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### HTTP状态码

- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证或token无效
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `422 Unprocessable Entity` - 数据验证失败
- `429 Too Many Requests` - 请求频率超限
- `500 Internal Server Error` - 服务器内部错误
- `503 Service Unavailable` - 服务暂时不可用

### 常见错误码

- `INVALID_CREDENTIALS` - 登录凭据无效
- `TOKEN_EXPIRED` - Token已过期
- `INSUFFICIENT_PERMISSIONS` - 权限不足
- `RESOURCE_NOT_FOUND` - 资源未找到
- `VALIDATION_ERROR` - 数据验证失败
- `RATE_LIMIT_EXCEEDED` - 请求频率超限
- `AI_SERVICE_ERROR` - AI服务错误
- `DATABASE_ERROR` - 数据库错误

## 速率限制

API实施了速率限制以防止滥用：

- 认证用户: 100 请求/分钟
- 未认证用户: 20 请求/分钟
- 聊天接口: 10 请求/分钟

超过限制时会返回429状态码，响应头包含限制信息：

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
```

## WebSocket接口

### 实时聊天WebSocket

建立WebSocket连接进行实时双向通信：

**连接URL:**
```
ws://localhost:8000/api/ws/chat/{session_id}?token={jwt_token}
```

**消息格式:**

发送消息：
```json
{
  "type": "message",
  "content": "用户消息",
  "metadata": {}
}
```

接收消息：
```json
{
  "type": "message",
  "id": "uuid",
  "content": "AI响应",
  "role": "assistant",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

系统消息：
```json
{
  "type": "system",
  "event": "thinking|typing|error",
  "data": {}
}
```

## SDK和代码示例

### JavaScript/TypeScript

```typescript
// 认证
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
});

const { access_token } = await loginResponse.json();

// 发送消息
const messageResponse = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    content: 'Hello, AI!'
  })
});

// SSE连接
const eventSource = new EventSource(`/api/chat/stream/${sessionId}?message=Hello&token=${access_token}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Python

```python
import requests
import json

# 认证
login_data = {
    "username": "your_username",
    "password": "your_password"
}

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json=login_data
)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 发送消息
message_data = {
    "content": "Hello, AI!"
}

response = requests.post(
    f"http://localhost:8000/api/chat/sessions/{session_id}/messages",
    headers=headers,
    json=message_data
)

print(response.json())
```

### cURL

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# 发送消息
curl -X POST http://localhost:8000/api/chat/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {your_token}" \
  -d '{"content": "Hello, AI!"}'

# 获取会话列表
curl -X GET http://localhost:8000/api/chat/sessions \
  -H "Authorization: Bearer {your_token}"
```

## 版本控制

API使用语义化版本控制，当前版本为v1。

### 版本兼容性

- 主版本号变更：不兼容的API修改
- 次版本号变更：向后兼容的功能添加
- 修订版本号变更：向后兼容的问题修复

### 版本迁移

当API版本升级时，我们会：

1. 提前通知用户即将到来的变更
2. 保持旧版本至少6个月的支持
3. 提供迁移指南和工具
4. 在响应头中包含弃用警告

## 支持和反馈

如果你在使用API时遇到问题或有建议，请通过以下方式联系我们：

- GitHub Issues: [项目仓库](https://github.com/your-org/ai-agent/issues)
- 邮件支持: api-support@yourdomain.com
- 文档反馈: docs@yourdomain.com

---

*本文档持续更新中，请关注最新版本。*