"""
API package for FastAPI routers.

This package contains all API endpoints organized by functionality.
"""

# Import routers here when they are created
from .auth import router as auth_router
from .chat import router as chat_router  
# from .agent import router as agent_router

__all__ = [
    "auth_router",
    "chat_router", 
    # "agent_router",
]