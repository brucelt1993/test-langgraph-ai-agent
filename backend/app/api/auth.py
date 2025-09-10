"""
Authentication API endpoints.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
import logging

from app.core.security import (
    PasswordManager, TokenManager, SecurityMiddleware,
    create_user_tokens, verify_refresh_token, verify_token_payload
)
from app.core.config import settings
from app.repositories.factory import get_repository_factory
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: Dict[str, Any]
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, errors = PasswordManager.validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v


class UserLoginRequest(BaseModel):
    username: str  # Can be username or email
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse  # 添加用户信息


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, errors = PasswordManager.validate_password_strength(v)
        if not is_valid:
            raise ValueError('; '.join(errors))
        return v


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    http_request: Request
):
    """Register a new user."""
    try:
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            
            # Check if username exists
            if await user_repo.username_exists(request.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # Check if email exists  
            if await user_repo.email_exists(request.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            
            # Hash password
            password_hash = PasswordManager.hash_password(request.password)
            
            # Create user
            user = await user_repo.create_user(
                username=request.username,
                email=request.email,
                password_hash=password_hash,
                full_name=request.full_name,
                role_name="user",  # Default role
                is_verified=False  # Require email verification
            )
            
            await repo_factory.commit()
            
            logger.info(f"User registered: {user.username} ({user.email})")
            
            return {
                "message": "User registered successfully",
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLoginRequest,
    http_request: Request
):
    """Authenticate user and return JWT tokens."""
    try:
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            session_repo = repo_factory.get_user_session_repository()
            
            # Get user by username or email
            user = await user_repo.get_by_username_or_email(request.username)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not PasswordManager.verify_password(request.password, user.password_hash):
                logger.warning(f"Failed login attempt for: {request.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )
            
            # Update last login
            await user_repo.update_last_login(user.id)
            
            # Create tokens
            user_data = {
                "username": user.username,
                "email": user.email,
                "role": user.role.name,
                "permissions": user.role.permissions if user.role else "[]"
            }
            
            tokens = create_user_tokens(user.id, user_data)
            
            # Store session
            client_ip = SecurityMiddleware.get_client_ip(http_request)
            user_agent = SecurityMiddleware.get_user_agent(http_request)
            
            token_hash = TokenManager.get_token_hash(tokens["access_token"])
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            await session_repo.create_session(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                device_info=user_agent,
                ip_address=client_ip
            )
            
            await repo_factory.commit()
            
            logger.info(f"User logged in: {user.username}")
            
            # 构造用户响应数据
            user_response = UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                role=user.role.to_dict() if user.role else {"name": "user", "display_name": "用户"},
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
            
            return LoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user_response
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        user_id = verify_refresh_token(request.refresh_token)
        
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            
            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new tokens
            user_data = {
                "username": user.username,
                "email": user.email, 
                "role": user.role.name,
                "permissions": user.role.permissions if user.role else "[]"
            }
            
            tokens = create_user_tokens(user.id, user_data)
            
            logger.debug(f"Token refreshed for user: {user.username}")
            
            return TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(token_payload: Dict[str, Any] = Depends(verify_token_payload)):
    """Logout user and revoke session."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            session_repo = repo_factory.get_user_session_repository()
            
            # Revoke all user sessions
            revoked_count = await session_repo.revoke_user_sessions(user_id)
            
            await repo_factory.commit()
            
            logger.info(f"User logged out: {user_id}, revoked {revoked_count} sessions")
            
            return {"message": "Logged out successfully"}
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(token_payload: Dict[str, Any] = Depends(verify_token_payload)):
    """Get current authenticated user information."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            
            user = await user_repo.get_by_id(user_id, load_relations=True)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                role={
                    "id": user.role.id,
                    "name": user.role.name,
                    "display_name": user.role.display_name,
                    "permissions": user.role.permissions
                } if user.role else {},
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    full_name: Optional[str] = None,
    token_payload: Dict[str, Any] = Depends(verify_token_payload)
):
    """Update current user profile."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            
            # Update user profile
            updates = {}
            if full_name is not None:
                updates["full_name"] = full_name
            
            if updates:
                user = await user_repo.update(user_id, **updates)
                await repo_factory.commit()
                
                logger.info(f"Profile updated for user: {user_id}")
                
                # Reload with relations
                user = await user_repo.get_by_id(user_id, load_relations=True)
                
                return UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    role={
                        "id": user.role.id,
                        "name": user.role.name,
                        "display_name": user.role.display_name,
                        "permissions": user.role.permissions
                    } if user.role else {},
                    created_at=user.created_at,
                    last_login_at=user.last_login_at
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No updates provided"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    token_payload: Dict[str, Any] = Depends(verify_token_payload)
):
    """Change user password."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            session_repo = repo_factory.get_user_session_repository()
            
            # Get user
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not PasswordManager.verify_password(request.current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid current password"
                )
            
            # Hash new password
            new_password_hash = PasswordManager.hash_password(request.new_password)
            
            # Update password
            await user_repo.change_password(user_id, new_password_hash)
            
            # Revoke all existing sessions (force re-login)
            await session_repo.revoke_user_sessions(user_id)
            
            await repo_factory.commit()
            
            logger.info(f"Password changed for user: {user_id}")
            
            return {"message": "Password changed successfully. Please log in again."}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/sessions")
async def get_user_sessions(token_payload: Dict[str, Any] = Depends(verify_token_payload)):
    """Get user's active sessions."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            session_repo = repo_factory.get_user_session_repository()
            
            sessions = await session_repo.get_active_sessions(user_id)
            
            return {
                "sessions": [
                    {
                        "id": session.id,
                        "device_info": session.device_info,
                        "ip_address": session.ip_address,
                        "created_at": session.created_at,
                        "last_used_at": session.last_used_at,
                        "expires_at": session.expires_at
                    }
                    for session in sessions
                ]
            }
            
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    token_payload: Dict[str, Any] = Depends(verify_token_payload)
):
    """Revoke a specific user session."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            session_repo = repo_factory.get_user_session_repository()
            
            # Verify session belongs to user
            session = await session_repo.get_by_id(session_id)
            if not session or session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            # Revoke session
            success = await session_repo.revoke_session(session_id)
            
            if success:
                await repo_factory.commit()
                logger.info(f"Session revoked: {session_id} for user: {user_id}")
                return {"message": "Session revoked successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to revoke session"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )