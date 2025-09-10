"""
Application Configuration

This module provides secure configuration management with validation
for all environment variables used in the application.
"""

from typing import List, Optional, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict  
import secrets
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Basic App Configuration
    APP_NAME: str = "AI Agent API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Server port")
    
    # Security Configuration
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="Secret key for JWT signing"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        ge=1, 
        le=43200,  # Max 30 days
        description="JWT token expiration in minutes"
    )
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///./ai_agent.db",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        description="OpenAI API key - required for AI functionality"
    )
    OPENAI_API_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4",
        description="OpenAI model name"
    )
    OPENAI_MAX_TOKENS: int = Field(
        default=4096,
        ge=1,
        le=32768,
        description="Maximum tokens for OpenAI responses"
    )
    OPENAI_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="OpenAI temperature setting"
    )
    
    # Weather API Configuration
    WEATHER_API_KEY: str = Field(
        description="Weather API key - required for weather functionality"
    )
    WEATHER_API_URL: str = Field(
        default="http://api.openweathermap.org/data/2.5",
        description="Weather API base URL"
    )
    WEATHER_CACHE_TTL: int = Field(
        default=600,  # 10 minutes
        ge=60,
        description="Weather data cache TTL in seconds"
    )
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=1,
        description="Rate limit per minute per IP"
    )
    
    # Chat Configuration
    MAX_CONVERSATION_HISTORY: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum conversation rounds to keep in memory"
    )
    MAX_MESSAGE_LENGTH: int = Field(
        default=4000,
        ge=1,
        le=32000,
        description="Maximum length of a single message"
    )
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Maximum file upload size in bytes"
    )
    UPLOAD_DIR: Path = Field(
        default=Path("uploads"),
        description="Directory for file uploads"
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if not v:
            raise ValueError("OPENAI_API_KEY is required")
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        if len(v) < 20:
            raise ValueError("OPENAI_API_KEY appears to be invalid (too short)")
        return v
    
    @field_validator("WEATHER_API_KEY")
    @classmethod
    def validate_weather_api_key(cls, v: str) -> str:
        """Validate weather API key."""
        if not v:
            raise ValueError("WEATHER_API_KEY is required")
        if len(v) < 10:
            raise ValueError("WEATHER_API_KEY appears to be invalid (too short)")
        return v
    
    @field_validator("OPENAI_API_URL", "WEATHER_API_URL")
    @classmethod
    def validate_api_urls(cls, v: str) -> str:
        """Validate API URLs."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API URL must start with http:// or https://")
        return v.rstrip("/")
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper
    
    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins."""
        if not v:
            raise ValueError("At least one CORS origin must be specified")
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"CORS origin '{origin}' must start with http:// or https://")
        return v
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy."""
        if self.DATABASE_URL.startswith("sqlite:"):
            return self.DATABASE_URL.replace("sqlite:", "sqlite+aiosqlite:", 1)
        elif self.DATABASE_URL.startswith("postgresql:"):
            return self.DATABASE_URL.replace("postgresql:", "postgresql+asyncpg:", 1)
        return self.DATABASE_URL
    
    def get_safe_config(self) -> dict[str, Any]:
        """Get configuration dict with sensitive data masked."""
        config = self.model_dump()
        
        # Mask sensitive information
        sensitive_keys = [
            "SECRET_KEY", 
            "OPENAI_API_KEY", 
            "WEATHER_API_KEY",
            "DATABASE_URL"
        ]
        
        for key in sensitive_keys:
            if key in config and config[key]:
                # Show first 4 and last 4 characters with masking
                value = str(config[key])
                if len(value) > 8:
                    config[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    config[key] = "***masked***"
        
        return config
    
# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


# Validate required settings on import
def validate_required_settings() -> None:
    """Validate that all required settings are properly configured."""
    try:
        # This will trigger all validators
        settings_dict = settings.model_dump()
        
        # Additional runtime validations
        required_for_ai = ["OPENAI_API_KEY"]
        required_for_weather = ["WEATHER_API_KEY"]
        
        missing_ai = [key for key in required_for_ai if not getattr(settings, key, None)]
        missing_weather = [key for key in required_for_weather if not getattr(settings, key, None)]
        
        if missing_ai:
            raise ValueError(f"Missing required AI configuration: {', '.join(missing_ai)}")
        
        if missing_weather:
            raise ValueError(f"Missing required Weather API configuration: {', '.join(missing_weather)}")
            
        print("✅ All configuration settings validated successfully")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        raise


# Run validation on import
if __name__ != "__main__":
    validate_required_settings()