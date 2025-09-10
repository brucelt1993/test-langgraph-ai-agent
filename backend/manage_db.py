#!/usr/bin/env python3
"""
Database Management Tool

This script provides utilities for managing the database schema
and initial data setup.
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime, timezone
from uuid import uuid4

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import create_tables, drop_tables, AsyncSessionLocal, engine
from app.models import User, Role, ChatSession
from app.core.config import settings
from passlib.context import CryptContext
from sqlalchemy import text

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_initial_roles():
    """Create initial roles in the database."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if roles already exist
            existing_roles = await session.execute(
                text("SELECT COUNT(*) FROM roles")
            )
            if existing_roles.scalar() > 0:
                print("ℹ️  Roles already exist, skipping creation")
                return

            # Create admin role
            admin_role = Role(
                id=str(uuid4()),
                name="admin",
                display_name="Administrator",
                description="Full system access",
                permissions=json.dumps([
                    "user:create", "user:read", "user:update", "user:delete",
                    "role:create", "role:read", "role:update", "role:delete",
                    "chat:create", "chat:read", "chat:update", "chat:delete",
                    "admin:access", "system:manage"
                ])
            )

            # Create user role
            user_role = Role(
                id=str(uuid4()),
                name="user",
                display_name="Regular User",
                description="Standard user access",
                permissions=json.dumps([
                    "chat:create", "chat:read", "chat:update", "chat:delete",
                    "profile:read", "profile:update"
                ])
            )

            session.add(admin_role)
            session.add(user_role)
            await session.commit()
            
            print("✅ Initial roles created successfully")
            print(f"   - Admin role ID: {admin_role.id}")
            print(f"   - User role ID: {user_role.id}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating initial roles: {e}")
            raise


async def create_admin_user(username: str, email: str, password: str):
    """Create an admin user."""
    async with AsyncSessionLocal() as session:
        try:
            # Get admin role
            admin_role = await session.execute(
                text("SELECT * FROM roles WHERE name = 'admin' LIMIT 1")
            )
            admin_role = admin_role.fetchone()
            
            if not admin_role:
                print("❌ Admin role not found. Run create-roles first.")
                return False

            # Check if user already exists
            existing_user = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE username = :username OR email = :email"),
                {"username": username, "email": email}
            )
            if existing_user.scalar() > 0:
                print(f"❌ User with username '{username}' or email '{email}' already exists")
                return False

            # Create admin user
            user = User(
                id=str(uuid4()),
                username=username,
                email=email,
                full_name="System Administrator",
                password_hash=pwd_context.hash(password),
                role_id=admin_role[0],  # admin_role.id
                is_active=True,
                is_verified=True
            )

            session.add(user)
            await session.commit()
            
            print(f"✅ Admin user created successfully")
            print(f"   - Username: {username}")
            print(f"   - Email: {email}")
            print(f"   - User ID: {user.id}")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating admin user: {e}")
            return False


async def reset_database():
    """Reset the entire database."""
    print("⚠️  This will DELETE ALL DATA in the database!")
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm != "RESET":
        print("❌ Database reset cancelled")
        return False

    try:
        await drop_tables()
        await create_tables()
        print("✅ Database reset successfully")
        return True
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False


async def show_database_info():
    """Show database connection information."""
    print("📊 Database Information:")
    print(f"   URL: {settings.DATABASE_URL}")
    print(f"   Async URL: {settings.database_url_async}")
    print(f"   Echo: {settings.DATABASE_ECHO}")
    
    # Try to connect and get basic stats
    try:
        async with AsyncSessionLocal() as session:
            # Count tables
            users_count = await session.execute(text("SELECT COUNT(*) FROM users"))
            roles_count = await session.execute(text("SELECT COUNT(*) FROM roles")) 
            sessions_count = await session.execute(text("SELECT COUNT(*) FROM chat_sessions"))
            messages_count = await session.execute(text("SELECT COUNT(*) FROM messages"))
            
            print("📈 Database Statistics:")
            print(f"   Users: {users_count.scalar()}")
            print(f"   Roles: {roles_count.scalar()}")
            print(f"   Chat Sessions: {sessions_count.scalar()}")
            print(f"   Messages: {messages_count.scalar()}")
            
    except Exception as e:
        print(f"⚠️  Could not retrieve database statistics: {e}")


async def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Agent Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_db.py --init                     Initialize database with tables and roles
  python manage_db.py --create-admin admin admin@example.com password123
  python manage_db.py --reset                    Reset entire database (DANGEROUS!)
  python manage_db.py --info                     Show database information
  python manage_db.py --create-tables            Create database tables only
        """
    )
    
    parser.add_argument("--init", action="store_true", help="Initialize database with tables and roles")
    parser.add_argument("--create-tables", action="store_true", help="Create database tables")
    parser.add_argument("--create-roles", action="store_true", help="Create initial roles")
    parser.add_argument("--create-admin", nargs=3, metavar=("USERNAME", "EMAIL", "PASSWORD"), 
                       help="Create admin user")
    parser.add_argument("--reset", action="store_true", help="Reset entire database (DANGEROUS!)")
    parser.add_argument("--info", action="store_true", help="Show database information")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        # Initialize (tables + roles)
        if args.init:
            print("🚀 Initializing database...")
            await create_tables()
            await create_initial_roles()
            print("✅ Database initialized successfully!")

        # Create tables only
        if args.create_tables:
            await create_tables()

        # Create roles only
        if args.create_roles:
            await create_initial_roles()

        # Create admin user
        if args.create_admin:
            username, email, password = args.create_admin
            success = await create_admin_user(username, email, password)
            if not success:
                return 1

        # Reset database
        if args.reset:
            success = await reset_database()
            if not success:
                return 1

        # Show database info
        if args.info:
            await show_database_info()

        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)