# AI Agent - 智能对话系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 22+](https://img.shields.io/badge/node-22+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

一个基于FastAPI + Vue.js的现代化AI对话系统，支持多轮对话、实时流式响应、AI思维过程可视化等功能。

## ✨ 核心特性

### 🔐 用户认证与授权
- **RBAC权限系统**：基于角色的访问控制
- **JWT认证**：安全的无状态身份验证
- **多角色支持**：管理员、普通用户等角色管理
- **密码安全**：bcrypt加密存储

### 💬 智能对话功能
- **多轮对话记忆**：支持10轮上下文记忆
- **实时流式响应**：基于SSE的实时消息推送
- **AI思维过程**：可视化AI的思考过程
- **会话管理**：创建、管理、历史查看

### 🤖 AI Agent能力
- **LangGraph集成**：强大的AI工作流引擎
- **OpenAI集成**：支持GPT-4等先进模型
- **工具调用**：天气查询、信息检索等工具
- **智能路由**：基于意图的对话路由

### 🎨 现代化界面
- **Vue 3 + TypeScript**：现代化前端技术栈
- **Tailwind CSS**：优雅的UI设计系统
- **shadcn/ui**：高质量组件库
- **响应式设计**：支持移动端和桌面端

### 🏗️ 企业级架构
- **微服务架构**：前后端分离设计
- **容器化部署**：Docker + Docker Compose
- **数据库支持**：PostgreSQL + Redis
- **监控告警**：集成Prometheus + Grafana

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 22+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-agent
```

### 2. 环境配置

复制并配置环境变量：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的配置信息（详见[环境变量配置](#环境变量配置)）。

### 3. 开发环境启动

使用Docker Compose快速启动开发环境：

```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml up -d

# 或者启动包含管理工具的完整环境
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

服务访问地址：
- 前端应用：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs
- 数据库管理：http://localhost:5050 (pgAdmin)
- Redis管理：http://localhost:8081

### 4. 手动开发环境（可选）

如果不使用Docker，可以手动启动：

#### 后端启动

```bash
cd backend

# 安装依赖
uv sync

# 运行数据库迁移
uv run alembic upgrade head

# 启动开发服务器
uv run uvicorn main:app --reload
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📦 生产环境部署

### 使用Docker Compose部署

```bash
# 1. 配置生产环境变量
cp .env.production.example .env.production

# 2. 启动生产服务
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 3. 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 4. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 部署后验证

- 应用访问：http://your-domain
- 健康检查：http://your-domain/health
- API文档：http://your-domain/api/docs

详细部署指南请参考 [deployment.md](docs/deployment.md)。

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
POSTGRES_DB=ai_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Redis配置
REDIS_PASSWORD=your_redis_password

# 应用安全
SECRET_KEY=your_very_secure_secret_key_here

# AI配置
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 外部服务
WEATHER_API_KEY=your_weather_api_key

# 生产环境配置
ALLOWED_HOSTS=your-domain.com,localhost
CORS_ORIGINS=https://your-domain.com
```

完整的环境变量说明请参考 [.env.example](.env.example)。

### 功能配置

主要配置文件位置：
- 后端配置：`backend/app/core/config.py`
- 前端配置：`frontend/src/config/`
- 数据库配置：`backend/alembic.ini`

## 🧪 测试

### 运行所有测试

```bash
# 运行完整测试套件
docker-compose -f docker-compose.test.yml up --build

# 或者单独运行测试类型
npm run test:unit        # 单元测试
npm run test:integration # 集成测试
npm run test:e2e        # E2E测试
```

### 代码质量检查

```bash
# 后端代码检查
cd backend
uv run black --check .
uv run isort --check-only .
uv run flake8 .
uv run mypy app/

# 前端代码检查
cd frontend
npm run lint
npm run type-check
npm run test:coverage
```

## 📋 API文档

### 接口文档

启动后端服务后，可以访问自动生成的API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

### 主API端点

| 端点 | 方法 | 描述 |
|------|------|---------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/chat/sessions` | GET | 获取会话列表 |
| `/api/chat/sessions` | POST | 创建新会话 |
| `/api/chat/messages` | POST | 发送消息 |
| `/api/chat/stream` | GET | SSE流式响应 |
| `/health` | GET | 健康检查 |

## 🏗️ 项目结构

```
ai-agent/
├── backend/                 # 后端服务
│   ├── app/                # 应用代码
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心配置
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── tests/             # 后端测试
│   ├── migrations/        # 数据库迁移
│   └── Dockerfile         # 容器配置
├── frontend/               # 前端应用
│   ├── src/               # 源代码
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   ├── stores/        # 状态管理
│   │   └── utils/         # 工具函数
│   ├── tests/             # 前端测试
│   └── Dockerfile         # 容器配置
├── tests/                  # 集成测试
│   ├── integration/       # 集成测试
│   └── e2e/              # E2E测试
├── docs/                   # 项目文档
├── nginx/                  # Nginx配置
├── monitoring/             # 监控配置
└── docker-compose.yml      # 容器编排
```

## 🔍 监控与日志

### 应用监控

生产环境集成了完整的监控方案：

```bash
# 启动监控服务
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

- **Prometheus**: http://localhost:9090 - 指标收集
- **Grafana**: http://localhost:3001 - 可视化监控
- **日志聚合**: 集中化日志管理

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看实时日志
docker-compose logs -f --tail=100 backend
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码规范

- Python代码遵循PEP 8规范
- TypeScript/Vue代码遵循ESLint配置
- 提交信息遵循Conventional Commits规范
- 所有新功能需要包含测试用例

## 📖 更多文档

- [部署指南](docs/deployment.md)
- [API参考](docs/api.md)
- [开发指南](docs/development.md)
- [架构设计](docs/architecture.md)
- [故障排除](docs/troubleshooting.md)

## 🐛 问题反馈

如果你发现了bug或有功能建议，请通过以下方式反馈：

- [GitHub Issues](https://github.com/your-org/ai-agent/issues)
- [功能请求](https://github.com/your-org/ai-agent/issues/new?template=feature_request.md)
- [Bug报告](https://github.com/your-org/ai-agent/issues/new?template=bug_report.md)

## 📄 许可证

本项目基于MIT许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI工作流引擎
- [OpenAI](https://openai.com/) - AI模型提供商
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的CSS框架

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！