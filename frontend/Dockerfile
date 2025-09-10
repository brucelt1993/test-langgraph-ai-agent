# 前端生产环境多阶段构建
# 构建阶段
FROM node:22-alpine AS builder

# 设置工作目录
WORKDIR /app

# 优化npm安装
RUN npm config set registry https://registry.npmmirror.com/

# 复制package文件
COPY package*.json ./

# 安装依赖（优化缓存）
RUN --mount=type=cache,target=/root/.npm \
    npm ci --only=production --no-audit --no-fund

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 生产环境阶段
FROM nginx:1.25-alpine AS production

# 安装安全更新
RUN apk --no-cache upgrade

# 创建非root用户
RUN addgroup -g 1000 -S appuser \
    && adduser -u 1000 -D -S -G appuser appuser

# 创建目录并设置权限
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && chown -R appuser:appuser /var/cache/nginx /var/log/nginx /var/run \
    && chmod -R 755 /var/cache/nginx /var/log/nginx /var/run

# 复制构建结果
COPY --from=builder --chown=appuser:appuser /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY --chown=appuser:appuser nginx.conf /etc/nginx/nginx.conf
COPY --chown=appuser:appuser nginx.prod.conf /etc/nginx/conf.d/default.conf

# 设置正确的权限
RUN chown -R appuser:appuser /usr/share/nginx/html \
    && chmod -R 755 /usr/share/nginx/html

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]