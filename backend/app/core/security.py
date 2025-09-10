"""
Security utilities for JWT authentication and password hashing.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, Request
import hashlib
import secrets
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
security = HTTPBearer(auto_error=False)


class SecurityError(Exception):
    """Custom security exception."""
    pass


class TokenManager:
    """JWT token management utility."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        try:
            to_encode = data.copy()
            
            # Set expiration
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access"
            })
            
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
            
            logger.debug(f"Created access token for subject: {data.get('sub')}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise SecurityError(f"Failed to create access token: {e}")
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        try:
            to_encode = data.copy()
            
            # Refresh tokens have longer expiration (7 days)
            expire = datetime.now(timezone.utc) + timedelta(days=7)
            
            to_encode.update({
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "refresh"
            })
            
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            
            logger.debug(f"Created refresh token for subject: {data.get('sub')}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise SecurityError(f"Failed to create refresh token: {e}")
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise SecurityError(f"Invalid token type. Expected: {token_type}")
            
            # Verify expiration
            exp = payload.get("exp")
            if exp is None:
                raise SecurityError("Token missing expiration")
            
            if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise SecurityError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise SecurityError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise SecurityError(f"Token verification failed: {e}")
    
    @staticmethod
    def get_token_hash(token: str) -> str:
        """Get hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def extract_token_data(token: str) -> Optional[Dict[str, Any]]:
        """Extract data from token without verification (for debugging)."""
        try:
            # Decode without verification (for debugging only)
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Error extracting token data: {e}")
            return None


class PasswordManager:
    """Password hashing and verification utility."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise SecurityError(f"Failed to hash password: {e}")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Generate a random password."""
        import string
        
        if length < 8:
            length = 8
        
        # Ensure password has at least one of each character type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase), 
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(
                string.ascii_letters + string.digits + "!@#$%^&*"
            ))
        
        # Shuffle and join
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = ["123456", "password", "qwerty", "abc123"]
        if any(pattern in password.lower() for pattern in common_patterns):
            errors.append("Password contains common patterns")
        
        return len(errors) == 0, errors


class SecurityMiddleware:
    """Security middleware utilities."""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def get_user_agent(request: Request) -> str:
        """Extract user agent from request."""
        return request.headers.get("User-Agent", "unknown")
    
    @staticmethod
    def is_rate_limited(
        identifier: str, 
        max_requests: int = 60,
        window_minutes: int = 1
    ) -> bool:
        """Simple in-memory rate limiting (production should use Redis)."""
        # This is a basic implementation - production should use Redis
        # For now, we'll implement a simple time-based check
        import time
        
        current_time = int(time.time())
        window_start = current_time - (window_minutes * 60)
        
        # In production, store this in Redis with expiration
        # For now, return False (no rate limiting)
        return False


# Authentication dependencies
async def get_current_user_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract JWT token from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


async def verify_token_payload(token: str = Depends(get_current_user_token)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = TokenManager.verify_token(token)
        
        # Verify required claims
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        
        return payload
        
    except SecurityError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_payload: Dict[str, Any] = Depends(verify_token_payload)):
    """Get current user from JWT token payload."""
    from app.repositories.factory import get_repository_factory
    
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )
    
    try:
        # Get user from database
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                )
            
            return user
            
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


# Token utilities
def create_user_tokens(user_id: str, user_data: Dict[str, Any]) -> Dict[str, str]:
    """Create both access and refresh tokens for a user."""
    token_data = {
        "sub": user_id,
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "role": user_data.get("role"),
        "permissions": user_data.get("permissions", [])
    }
    
    access_token = TokenManager.create_access_token(token_data)
    refresh_token = TokenManager.create_refresh_token({"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def verify_refresh_token(token: str) -> str:
    """Verify refresh token and return user ID."""
    try:
        payload = TokenManager.verify_token(token, token_type="refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise SecurityError("Invalid refresh token: missing user ID")
        
        return user_id
        
    except SecurityError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )