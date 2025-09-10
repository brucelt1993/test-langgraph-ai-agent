#!/usr/bin/env python3
"""
快速检查SQLite数据库内容
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = "ai_agent.db"

def check_database():
    """检查数据库内容"""
    db_file = Path(DB_PATH)
    
    print("🔍 SQLite数据库快速检查")
    print("=" * 40)
    
    if not db_file.exists():
        print(f"❌ 数据库文件不存在: {db_file.absolute()}")
        return
    
    print(f"✅ 数据库文件: {db_file.absolute()}")
    print(f"📁 文件大小: {db_file.stat().st_size / 1024:.2f} KB")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ 数据库中没有表")
            return
        
        print(f"\n📊 数据库表（共{len(tables)}个）:")
        print("-" * 30)
        
        for table in tables:
            table_name = table[0]
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"  📋 {table_name}:")
            print(f"     记录数: {count}")
            print(f"     字段数: {len(columns)}")
            
            if table_name == "users" and count > 0:
                # 显示用户信息
                cursor.execute("SELECT username, email, is_active FROM users LIMIT 3")
                users = cursor.fetchall()
                print("     用户预览:")
                for user in users:
                    username, email, is_active = user
                    status = "✅" if is_active else "❌"
                    print(f"       {status} {username} ({email})")
        
        conn.close()
        
        print("\n💡 连接方法:")
        print("1. 下载 DB Browser for SQLite: https://sqlitebrowser.org/")
        print("2. 直接打开文件: ai_agent.db")
        print("3. 或使用命令: python view_db.py")
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()