"""
Configuration utilities and startup checks.
"""

import os
import sys
from typing import Dict, List, Tuple
from pathlib import Path
import asyncio
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings


class ConfigurationError(Exception):
    """Configuration validation error."""
    pass


async def check_openai_connection() -> Tuple[bool, str]:
    """Check OpenAI API connectivity and authentication."""
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.OPENAI_API_URL}/models",
                headers=headers
            )
            
        if response.status_code == 200:
            models = response.json()
            available_models = [model["id"] for model in models.get("data", [])]
            
            if settings.OPENAI_MODEL in available_models:
                return True, f"✅ OpenAI API connection successful. Model '{settings.OPENAI_MODEL}' is available."
            else:
                return False, f"❌ Model '{settings.OPENAI_MODEL}' not available. Available models: {', '.join(available_models[:5])}"
                
        elif response.status_code == 401:
            return False, "❌ OpenAI API authentication failed. Check your API key."
        else:
            return False, f"❌ OpenAI API connection failed. Status: {response.status_code}"
            
    except httpx.TimeoutException:
        return False, "❌ OpenAI API connection timeout. Check network connectivity."
    except Exception as e:
        return False, f"❌ OpenAI API connection error: {str(e)}"


async def check_weather_api_connection() -> Tuple[bool, str]:
    """Check Weather API connectivity."""
    try:
        params = {
            "q": "London",
            "appid": settings.WEATHER_API_KEY,
            "units": "metric"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.WEATHER_API_URL}/weather",
                params=params
            )
            
        if response.status_code == 200:
            return True, "✅ Weather API connection successful."
        elif response.status_code == 401:
            return False, "❌ Weather API authentication failed. Check your API key."
        else:
            return False, f"❌ Weather API connection failed. Status: {response.status_code}"
            
    except httpx.TimeoutException:
        return False, "❌ Weather API connection timeout. Check network connectivity."
    except Exception as e:
        return False, f"❌ Weather API connection error: {str(e)}"


def check_database_connection() -> Tuple[bool, str]:
    """Check database connectivity."""
    try:
        # Create synchronous engine for connection test
        if settings.DATABASE_URL.startswith("sqlite"):
            # For SQLite, just check if we can create the file
            db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            engine = create_engine(settings.DATABASE_URL, echo=False)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True, f"✅ SQLite database connection successful: {db_path}"
            
        else:
            # For PostgreSQL and other databases
            engine = create_engine(settings.DATABASE_URL, echo=False)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0] if result else "Unknown"
            
            return True, f"✅ Database connection successful: {version}"
            
    except SQLAlchemyError as e:
        return False, f"❌ Database connection failed: {str(e)}"
    except Exception as e:
        return False, f"❌ Database connection error: {str(e)}"


def check_file_permissions() -> Tuple[bool, str]:
    """Check file system permissions for uploads and logs."""
    try:
        # Check upload directory
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = upload_dir / ".permission_test"
        test_file.write_text("test")
        test_file.unlink()
        
        # Check logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        test_log = logs_dir / ".permission_test"
        test_log.write_text("test")
        test_log.unlink()
        
        return True, "✅ File system permissions OK."
        
    except PermissionError as e:
        return False, f"❌ File system permission error: {str(e)}"
    except Exception as e:
        return False, f"❌ File system error: {str(e)}"


def validate_environment() -> Dict[str, Tuple[bool, str]]:
    """Validate all environment requirements."""
    checks = {}
    
    # Basic configuration validation
    try:
        # This will trigger pydantic validators
        settings.dict()
        checks["config_validation"] = (True, "✅ Configuration validation passed.")
    except Exception as e:
        checks["config_validation"] = (False, f"❌ Configuration validation failed: {str(e)}")
    
    # File permissions check
    checks["file_permissions"] = check_file_permissions()
    
    # Database connection check
    checks["database"] = check_database_connection()
    
    return checks


async def validate_external_services() -> Dict[str, Tuple[bool, str]]:
    """Validate external service connections."""
    checks = {}
    
    # OpenAI API check
    checks["openai"] = await check_openai_connection()
    
    # Weather API check  
    checks["weather"] = await check_weather_api_connection()
    
    return checks


async def run_startup_checks(skip_external: bool = False) -> bool:
    """Run all startup checks and return success status."""
    print("🔍 Running startup configuration checks...")
    
    # Environment checks
    env_checks = validate_environment()
    
    # External service checks (can be skipped for development)
    if not skip_external:
        external_checks = await validate_external_services()
        all_checks = {**env_checks, **external_checks}
    else:
        all_checks = env_checks
        print("⚠️  Skipping external service checks...")
    
    # Print results
    success_count = 0
    total_count = len(all_checks)
    
    for check_name, (success, message) in all_checks.items():
        print(f"  {check_name}: {message}")
        if success:
            success_count += 1
    
    # Summary
    if success_count == total_count:
        print(f"✅ All checks passed ({success_count}/{total_count})")
        return True
    else:
        print(f"❌ {total_count - success_count} checks failed ({success_count}/{total_count})")
        return False


def create_env_template() -> None:
    """Create .env.example template with all required variables."""
    template_content = f"""# AI Agent Configuration Template
# Copy this file to .env and fill in your actual values

# Database Configuration
DATABASE_URL=sqlite:///./ai_agent.db
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_agent

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_API_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# Weather API Configuration (REQUIRED)  
WEATHER_API_KEY=your_weather_api_key_here
WEATHER_API_URL=http://api.openweathermap.org/data/2.5
WEATHER_CACHE_TTL=600

# Security Configuration
SECRET_KEY=your_super_secret_key_here_change_in_production_min_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration (comma-separated)
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Chat Configuration
MAX_CONVERSATION_HISTORY=10
MAX_MESSAGE_LENGTH=4000

# File Upload Configuration
MAX_UPLOAD_SIZE={10 * 1024 * 1024}
UPLOAD_DIR=uploads

# Database Configuration
DATABASE_ECHO=False
"""
    
    env_example_path = Path("backend/.env.example")
    env_example_path.write_text(template_content.strip())
    print(f"✅ Created {env_example_path}")


if __name__ == "__main__":
    """CLI interface for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agent Configuration Management")
    parser.add_argument("--check", action="store_true", help="Run configuration checks")
    parser.add_argument("--skip-external", action="store_true", help="Skip external service checks")
    parser.add_argument("--create-template", action="store_true", help="Create .env.example template")
    
    args = parser.parse_args()
    
    if args.create_template:
        create_env_template()
    
    if args.check:
        success = asyncio.run(run_startup_checks(skip_external=args.skip_external))
        sys.exit(0 if success else 1)
    
    if not any(vars(args).values()):
        parser.print_help()