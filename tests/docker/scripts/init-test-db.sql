-- 初始化测试数据库
-- 创建必要的扩展和初始数据

-- 创建UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建基础角色数据
INSERT INTO roles (id, name, display_name, permissions, created_at, updated_at) 
VALUES 
  (uuid_generate_v4(), 'admin', '管理员', '["*"]', NOW(), NOW()),
  (uuid_generate_v4(), 'user', '普通用户', '["chat:create", "chat:read", "chat:update", "chat:delete", "message:create", "message:read"]', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- 创建测试用户（仅用于E2E测试）
DO $$
DECLARE
    user_role_id uuid;
    admin_role_id uuid;
BEGIN
    -- 获取角色ID
    SELECT id INTO user_role_id FROM roles WHERE name = 'user';
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin';
    
    -- 创建E2E测试用户（密码: E2ETestPassword123!）
    INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active, is_verified, created_at, updated_at)
    VALUES (
        uuid_generate_v4(),
        'e2etestuser',
        'e2etest@example.com',
        '$2b$12$LQ8Zz5.VYc1dF8dYcGkYB.Y8GnG8Y8GnG8Y8GnG8Y8GnG8Y8GnG8Ye', -- E2ETestPassword123!
        'E2E Test User',
        user_role_id,
        true,
        true,
        NOW(),
        NOW()
    ) ON CONFLICT (username) DO NOTHING;
    
    -- 创建E2E测试管理员（密码: AdminPassword123!）
    INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active, is_verified, created_at, updated_at)
    VALUES (
        uuid_generate_v4(),
        'e2etestadmin',
        'admin@e2etest.com',
        '$2b$12$LQ8Zz5.VYc1dF8dYcGkYB.X9FmF9X9FmF9X9FmF9X9FmF9X9FmF9Xe', -- AdminPassword123!
        'E2E Test Admin',
        admin_role_id,
        true,
        true,
        NOW(),
        NOW()
    ) ON CONFLICT (username) DO NOTHING;
END $$;