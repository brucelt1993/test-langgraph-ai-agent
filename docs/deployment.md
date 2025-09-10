# AI Agent 部署指南

本文档提供了AI Agent应用的详细部署指南，涵盖开发、测试和生产环境的部署配置。

## 目录
- [环境准备](#环境准备)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [故障排除](#故障排除)

## 环境准备

### 系统要求

#### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB可用空间
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+

#### 推荐配置
- **CPU**: 4核心以上
- **内存**: 8GB RAM以上
- **存储**: 50GB可用空间（包含数据库和日志）
- **网络**: 稳定的互联网连接

### 软件依赖

#### 必需软件
```bash
# Docker和Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git
sudo apt update && sudo apt install git -y

# 可选：Node.js和Python（如果需要本地开发）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 22
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 开发环境部署

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd ai-agent
```

### 2. 环境配置

```bash
# 复制开发环境配置
cp .env.dev.example .env.dev

# 编辑配置文件
nano .env.dev
```

开发环境主要配置：
```bash
# 开发环境配置
POSTGRES_DB=ai_agent_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

REDIS_PASSWORD=devpassword

# 开发密钥（不要在生产环境使用）
SECRET_KEY=dev_secret_key_change_in_production

# AI配置
OPENAI_API_KEY=sk-your-openai-api-key-here
WEATHER_API_KEY=your-weather-api-key-here

# 开发模式
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 3. 启动开发环境

```bash
# 基础开发环境
docker-compose -f docker-compose.dev.yml up -d

# 包含管理工具的完整开发环境
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 测试服务
curl http://localhost:8000/health
curl http://localhost:3000
```

开发环境服务地址：
- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 数据库管理: http://localhost:5050 (pgAdmin)
- Redis管理: http://localhost:8081
- 邮件测试: http://localhost:8025 (MailHog)

## 生产环境部署

### 1. 服务器准备

#### Ubuntu/Debian服务器设置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl wget git htop

# 配置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 创建应用用户
sudo useradd -m -s /bin/bash aiagent
sudo usermod -aG docker aiagent
```

### 2. SSL证书配置（可选但推荐）

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com

# 或者使用现有证书
sudo mkdir -p /etc/ssl/certs/aiagent
# 复制你的证书文件到/etc/ssl/certs/aiagent/
```

### 3. 生产环境配置

```bash
# 创建生产配置文件
cp .env.production.example .env.production

# 编辑生产配置
sudo nano .env.production
```

生产环境关键配置：
```bash
# 数据库配置
POSTGRES_DB=ai_agent_prod
POSTGRES_USER=ai_agent_user
POSTGRES_PASSWORD=VERY_SECURE_PASSWORD_HERE

# Redis配置
REDIS_PASSWORD=VERY_SECURE_REDIS_PASSWORD

# 应用安全
SECRET_KEY=VERY_LONG_AND_SECURE_SECRET_KEY_HERE
ENVIRONMENT=production
LOG_LEVEL=INFO

# 域名和安全配置
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# AI配置
OPENAI_API_KEY=sk-your-production-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 外部服务
WEATHER_API_KEY=your-weather-api-key

# 端口配置
HTTP_PORT=80
HTTPS_PORT=443

# 监控配置
GRAFANA_PASSWORD=SECURE_GRAFANA_PASSWORD
```

### 4. 启动生产服务

```bash
# 拉取最新镜像
docker-compose -f docker-compose.prod.yml pull

# 启动生产服务
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 启动包含监控的完整服务
docker-compose -f docker-compose.prod.yml --env-file .env.production --profile monitoring up -d
```

### 5. 数据库初始化

```bash
# 等待数据库启动
sleep 30

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# 创建超级管理员用户（可选）
docker-compose -f docker-compose.prod.yml exec backend uv run python -m app.scripts.create_admin
```

### 6. 验证生产部署

```bash
# 检查所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查健康状态
curl https://yourdomain.com/health

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

## 监控和日志

### 启用监控服务

生产环境包含了完整的监控栈：

```bash
# 启动监控服务
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

### 监控服务地址

- **Prometheus**: http://yourdomain.com:9090
- **Grafana**: http://yourdomain.com:3001 (admin/你的grafana密码)

### 配置Grafana仪表板

1. 登录Grafana (admin/GRAFANA_PASSWORD)
2. 导入预配置的仪表板
3. 设置告警规则

### 日志管理

#### 查看实时日志
```bash
# 所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
```

#### 日志轮转配置
```bash
# 配置Docker日志轮转
sudo cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

## 备份和恢复

### 数据库备份

#### 自动备份脚本
```bash
#!/bin/bash
# 创建备份脚本 /home/aiagent/backup.sh

BACKUP_DIR="/home/aiagent/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 数据库备份
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ai_agent_user ai_agent_prod > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

#### 设置定时备份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /home/aiagent/backup.sh >> /home/aiagent/backup.log 2>&1
```

### 数据恢复

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 恢复数据库
gunzip -c /home/aiagent/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_agent_user ai_agent_prod

# 重启服务
docker-compose -f docker-compose.prod.yml up -d
```

## 更新和维护

### 应用更新

```bash
# 1. 备份当前数据
/home/aiagent/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 更新Docker镜像
docker-compose -f docker-compose.prod.yml pull

# 4. 滚动更新服务
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# 5. 运行数据库迁移（如果需要）
docker-compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# 6. 验证更新
curl https://yourdomain.com/health
```

### 系统维护

```bash
# 清理未使用的Docker资源
docker system prune -a --volumes

# 监控磁盘使用情况
df -h
docker system df

# 检查服务健康状态
docker-compose -f docker-compose.prod.yml ps
```

## 故障排除

### 常见问题

#### 1. 服务无法启动

```bash
# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看具体错误日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# 检查端口占用
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

#### 2. 数据库连接问题

```bash
# 检查数据库服务
docker-compose -f docker-compose.prod.yml logs postgres

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U ai_agent_user -d ai_agent_prod -c "SELECT 1;"

# 检查数据库配置
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

#### 3. API响应慢或超时

```bash
# 检查后端资源使用
docker stats

# 查看API响应时间
curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/health

# 检查数据库查询性能
docker-compose -f docker-compose.prod.yml exec postgres psql -U ai_agent_user -d ai_agent_prod -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

#### 4. 前端页面无法访问

```bash
# 检查Nginx配置
docker-compose -f docker-compose.prod.yml logs nginx

# 测试静态文件服务
curl -I https://yourdomain.com/

# 检查前端构建
docker-compose -f docker-compose.prod.yml logs frontend
```

### 性能优化建议

#### 数据库优化
```sql
-- 创建必要的索引
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
```

#### 缓存优化
```bash
# 增加Redis内存限制
echo "maxmemory 512mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
```

#### 应用性能调优
```bash
# 调整后端worker数量
# 在.env.production中设置
MAX_WORKERS=4
WORKER_TIMEOUT=120
```

## 安全加固

### SSL/TLS配置

```bash
# 使用强SSL配置
# 在nginx配置中添加安全头
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options DENY always;
add_header X-XSS-Protection "1; mode=block" always;
```

### 防火墙配置

```bash
# 配置iptables规则
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP

# 保存规则
sudo iptables-save > /etc/iptables/rules.v4
```

### 定期安全更新

```bash
# 创建安全更新脚本
#!/bin/bash
sudo apt update && sudo apt upgrade -y
docker pull $(docker images --format "table {{.Repository}}:{{.Tag}}" | grep -v REPOSITORY)
```

## 联系支持

如果遇到部署问题，可以通过以下方式获取帮助：

- 查看项目文档: [GitHub Repository](https://github.com/your-org/ai-agent)
- 提交Issue: [GitHub Issues](https://github.com/your-org/ai-agent/issues)
- 邮件联系: support@yourdomain.com

---

本部署指南将根据项目发展持续更新。建议定期查看最新版本。