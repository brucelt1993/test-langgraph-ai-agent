#!/usr/bin/env python3
"""
SQLite数据库查看脚本

用于查看和管理SQLite数据库中的数据
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "ai_agent.db"

class SQLiteViewer:
    def __init__(self):
        self.db_path = Path(DB_PATH)
        if not self.db_path.exists():
            print(f"❌ 数据库文件不存在: {self.db_path.absolute()}")
            return
        print(f"📁 数据库文件: {self.db_path.absolute()}")
    
    def connect(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)
    
    def show_tables(self):
        """显示所有表"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("\n📋 数据库表列表:")
            print("-" * 40)
            for table in tables:
                table_name = table[0]
                
                # 获取表的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                print(f"  📊 {table_name:<20} ({count} 条记录)")
            
            conn.close()
            return [table[0] for table in tables]
            
        except Exception as e:
            print(f"❌ 获取表列表失败: {e}")
            return []
    
    def show_table_schema(self, table_name):
        """显示表结构"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\n🏗️  表 '{table_name}' 结构:")
            print("-" * 60)
            print(f"{'列名':<20} {'类型':<15} {'非空':<8} {'默认值':<15} {'主键'}")
            print("-" * 60)
            
            for col in columns:
                cid, name, type_, notnull, default, pk = col
                null_str = "NOT NULL" if notnull else "NULL"
                pk_str = "PRIMARY" if pk else ""
                default_str = str(default) if default else ""
                
                print(f"{name:<20} {type_:<15} {null_str:<8} {default_str:<15} {pk_str}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 获取表结构失败: {e}")
    
    def show_table_data(self, table_name, limit=10):
        """显示表数据"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            
            # 获取列名
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"\n📄 表 '{table_name}' 数据（前{limit}条）:")
            print("-" * 80)
            
            if not rows:
                print("  (空表)")
            else:
                # 打印列标题
                print(f"{'ID':<5} " + " | ".join(f"{col:<15}" for col in columns[:6]))
                print("-" * 80)
                
                # 打印数据行
                for i, row in enumerate(rows, 1):
                    row_str = f"{i:<5} "
                    for j, value in enumerate(row[:6]):  # 只显示前6列
                        if isinstance(value, str) and len(value) > 15:
                            value = value[:12] + "..."
                        row_str += f"{str(value):<15} | "
                    print(row_str[:-3])  # 移除最后的 " | "
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 获取表数据失败: {e}")
    
    def query_users(self):
        """专门查询用户表"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, full_name, is_active, is_verified, 
                       role_id, created_at, last_login_at 
                FROM users 
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            print(f"\n👥 用户列表 (共{len(users)}个用户):")
            print("-" * 100)
            print(f"{'ID':<8} {'用户名':<15} {'邮箱':<25} {'姓名':<15} {'激活':<6} {'验证':<6} {'角色ID':<10} {'创建时间'}")
            print("-" * 100)
            
            for user in users:
                user_id, username, email, full_name, is_active, is_verified, role_id, created_at, last_login = user
                
                # 格式化时间
                if created_at:
                    try:
                        if 'T' in created_at:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_str = dt.strftime('%m-%d %H:%M')
                        else:
                            created_str = created_at[:16]
                    except:
                        created_str = str(created_at)[:16]
                else:
                    created_str = "未知"
                
                print(f"{str(user_id)[:8]:<8} {username:<15} {email:<25} {(full_name or 'N/A'):<15} "
                      f"{'是' if is_active else '否':<6} {'是' if is_verified else '否':<6} "
                      f"{str(role_id)[:10]:<10} {created_str}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 查询用户失败: {e}")
    
    def query_roles(self):
        """查询角色表"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, display_name, description, permissions FROM roles")
            roles = cursor.fetchall()
            
            print(f"\n🎭 角色列表 (共{len(roles)}个角色):")
            print("-" * 80)
            
            for role in roles:
                role_id, name, display_name, description, permissions = role
                print(f"  🏷️  ID: {role_id}")
                print(f"      名称: {name}")
                print(f"      显示名: {display_name}")
                print(f"      描述: {description}")
                
                # 解析权限
                if permissions:
                    try:
                        perms = json.loads(permissions)
                        print(f"      权限: {', '.join(perms)}")
                    except:
                        print(f"      权限: {permissions}")
                print()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 查询角色失败: {e}")
    
    def query_chat_sessions(self):
        """查询聊天会话"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT cs.id, cs.title, cs.description, cs.user_id, cs.created_at,
                       u.username
                FROM chat_sessions cs
                LEFT JOIN users u ON cs.user_id = u.id
                ORDER BY cs.created_at DESC
                LIMIT 10
            """)
            sessions = cursor.fetchall()
            
            print(f"\n💬 聊天会话列表 (最近10个):")
            print("-" * 80)
            
            if not sessions:
                print("  (暂无聊天会话)")
            else:
                for session in sessions:
                    session_id, title, desc, user_id, created_at, username = session
                    print(f"  📝 [{session_id[:8]}] {title}")
                    print(f"      用户: {username} | 创建: {created_at[:16] if created_at else 'N/A'}")
                    if desc:
                        print(f"      描述: {desc}")
                    print()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 查询聊天会话失败: {e}")

def main():
    print("🗄️  SQLite数据库查看器")
    print("=" * 50)
    
    viewer = SQLiteViewer()
    if not viewer.db_path.exists():
        return
    
    # 显示所有表
    tables = viewer.show_tables()
    
    if not tables:
        print("❌ 数据库中没有表")
        return
    
    # 显示用户数据
    if "users" in tables:
        viewer.query_users()
    
    # 显示角色数据
    if "roles" in tables:
        viewer.query_roles()
    
    # 显示聊天会话
    if "chat_sessions" in tables:
        viewer.query_chat_sessions()
    
    # 交互式查询
    print("\n" + "=" * 50)
    print("💡 你也可以手动查询特定表:")
    for table in tables:
        print(f"   python view_db.py {table}")

if __name__ == "__main__":
    main()