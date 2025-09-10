# 后端生产环境Dockerfile
FROM python:3.13-slim AS base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_CACHE_DIR=/tmp/uv-cache

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 编译依赖
    gcc \
    g++ \
    # 健康检查依赖
    curl \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

# 安装依赖（使用缓存挂载优化）
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev

# 复制应用代码
COPY --chown=appuser:appuser . .

# 创建日志和数据目录
RUN mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]