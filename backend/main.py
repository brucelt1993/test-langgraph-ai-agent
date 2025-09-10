"""
FastAPI Main Application

This module contains the FastAPI application setup and configuration.
"""

import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.startup import run_startup_checks
from app.core.database import create_tables
from app.services.stream_service import get_stream_service

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path("logs") / "app.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup validation
    logger.info("Starting AI Agent API...")
    
    # Run configuration and connectivity checks
    startup_success = await run_startup_checks(skip_external=settings.DEBUG)
    
    if not startup_success:
        logger.error("Startup checks failed. Exiting.")
        sys.exit(1)
    
    # Initialize database (will be implemented in next task)
    await create_tables()
    
    # Initialize streaming service
    stream_service = await get_stream_service()
    logger.info("✅ SSE流式服务已启动")
    
    logger.info("✅ AI Agent API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Agent API...")
    
    # Stop streaming service
    await stream_service.stop()
    logger.info("✅ SSE流式服务已停止")
    
    # await engine.dispose()
    logger.info("✅ AI Agent API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Agent API",
    description="AI Agent Backend with FastAPI and LangGraph",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Include routers when implemented
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.stream import router as stream_router

app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(stream_router, prefix="/api/stream", tags=["streaming"])
# app.include_router(agent.router, prefix="/api/agent", tags=["agent"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Agent API", 
        "version": "0.1.0",
        "status": "running",
        "config": settings.get_safe_config()
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Start server
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )