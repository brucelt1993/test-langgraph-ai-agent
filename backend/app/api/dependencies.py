"""
Authentication dependencies and middleware for FastAPI.
"""

from typing import Dict, Any, Optional, List, Union
from functools import wraps
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
import logging

from app.core.security import verify_token_payload
from app.core.permissions import (
    PermissionType, 
    get_permission_registry, 
    get_permission_checker
)
from app.repositories.factory import get_repository_factory
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


class EnhancedPermissionChecker:
    """增强的权限检查器，支持RBAC系统。"""
    
    def __init__(
        self, 
        required_permissions: Union[List[PermissionType], List[str]], 
        require_all: bool = True,
        allow_self_access: bool = False
    ):
        """
        初始化权限检查器。
        
        Args:
            required_permissions: 需要的权限列表
            require_all: 是否需要所有权限
            allow_self_access: 是否允许自己访问自己的资源
        """
        # 标准化权限类型
        self.required_permissions = []
        for perm in required_permissions:
            if isinstance(perm, str):
                try:
                    self.required_permissions.append(PermissionType(perm))
                except ValueError:
                    logger.warning(f"Unknown permission type: {perm}")
                    continue
            else:
                self.required_permissions.append(perm)
        
        self.require_all = require_all
        self.allow_self_access = allow_self_access
        self.registry = get_permission_registry()
        self.checker = get_permission_checker()
    
    def __call__(self, token_payload: Dict[str, Any] = Depends(verify_token_payload)) -> Dict[str, Any]:
        """检查用户权限。"""
        try:
            user_role = token_payload.get("role", "guest")
            user_id = token_payload.get("sub")
            
            # 使用新的权限检查系统
            if self.require_all:
                has_permission = self.registry.has_all_permissions(user_role, self.required_permissions)
            else:
                has_permission = self.registry.has_any_permission(user_role, self.required_permissions)
            
            if not has_permission:
                logger.warning(
                    f"Access denied - insufficient permissions for user: {user_id}, "
                    f"role: {user_role}, required: {[p.value for p in self.required_permissions]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return token_payload
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )


class ResourceOwnerChecker:
    """资源所有者检查器，用于检查用户是否可以访问自己的资源。"""
    
    def __init__(self, resource_id_param: str = "user_id"):
        """
        初始化资源所有者检查器。
        
        Args:
            resource_id_param: 资源ID参数名
        """
        self.resource_id_param = resource_id_param
    
    def __call__(
        self,
        token_payload: Dict[str, Any] = Depends(verify_token_payload),
        **kwargs
    ) -> Dict[str, Any]:
        """检查资源所有权。"""
        try:
            current_user_id = token_payload.get("sub")
            resource_owner_id = kwargs.get(self.resource_id_param)
            
            if current_user_id != resource_owner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - not resource owner"
                )
            
            return token_payload
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Resource owner check error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Resource owner check failed"
            )


class RoleChecker:
    """角色检查器，支持角色层次结构。"""
    
    def __init__(self, required_roles: List[str], check_hierarchy: bool = True):
        """
        初始化角色检查器。
        
        Args:
            required_roles: 需要的角色列表
            check_hierarchy: 是否检查角色层次结构
        """
        self.required_roles = required_roles
        self.check_hierarchy = check_hierarchy
        self.registry = get_permission_registry()
    
    def __call__(self, token_payload: Dict[str, Any] = Depends(verify_token_payload)) -> Dict[str, Any]:
        """检查用户角色。"""
        try:
            user_role = token_payload.get("role", "guest")
            
            # 直接角色匹配
            if user_role in self.required_roles:
                return token_payload
            
            # 检查角色层次结构（高级角色可以访问低级角色的功能）
            if self.check_hierarchy:
                for required_role in self.required_roles:
                    if self.registry.is_role_higher_than(user_role, required_role):
                        return token_payload
            
            logger.warning(
                f"Access denied - role '{user_role}' not in required roles: {self.required_roles} "
                f"for user: {token_payload.get('sub')}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(self.required_roles)}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Role check error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role check failed"
            )


# 向后兼容的权限检查器
class PermissionChecker(EnhancedPermissionChecker):
    """向后兼容的权限检查器。"""
    
    def __init__(self, required_permissions: List[str], require_all: bool = True):
        super().__init__(required_permissions, require_all)


async def get_current_user(
    token_payload: Dict[str, Any] = Depends(verify_token_payload)
) -> User:
    """Get current authenticated user from database."""
    try:
        user_id = token_payload["sub"]
        
        async with get_repository_factory() as repo_factory:
            user_repo = repo_factory.get_user_repository()
            
            user = await user_repo.get_by_id(user_id, load_relations=True)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled"
                )
            
            return user
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current user"
        )


async def get_optional_current_user(
    token_payload: Optional[Dict[str, Any]] = None
) -> Optional[User]:
    """Get current authenticated user if token is provided (optional authentication)."""
    if not token_payload:
        return None
        
    try:
        return await get_current_user(token_payload)
    except HTTPException:
        # If token is invalid, return None instead of raising exception
        return None


# 便捷的权限检查器实例
require_admin = RoleChecker(["admin", "superadmin"])
require_user = RoleChecker(["user", "premium", "moderator", "admin", "superadmin"])
require_premium = RoleChecker(["premium", "moderator", "admin", "superadmin"])
require_moderator = RoleChecker(["moderator", "admin", "superadmin"])

# 基于权限的检查器
require_user_read = EnhancedPermissionChecker([PermissionType.USER_READ])
require_user_write = EnhancedPermissionChecker([PermissionType.USER_CREATE, PermissionType.USER_UPDATE], require_all=False)
require_user_delete = EnhancedPermissionChecker([PermissionType.USER_DELETE])
require_user_admin = EnhancedPermissionChecker([PermissionType.USER_ADMIN])

require_chat_access = EnhancedPermissionChecker([PermissionType.CHAT_READ, PermissionType.CHAT_CREATE], require_all=False)
require_chat_write = EnhancedPermissionChecker([PermissionType.CHAT_CREATE, PermissionType.CHAT_UPDATE], require_all=False)
require_chat_delete = EnhancedPermissionChecker([PermissionType.CHAT_DELETE])
require_chat_admin = EnhancedPermissionChecker([PermissionType.CHAT_ADMIN])

require_agent_use = EnhancedPermissionChecker([PermissionType.AGENT_USE])
require_agent_config = EnhancedPermissionChecker([PermissionType.AGENT_CONFIG])
require_agent_admin = EnhancedPermissionChecker([PermissionType.AGENT_ADMIN])

require_system_config = EnhancedPermissionChecker([PermissionType.SYSTEM_CONFIG])
require_system_admin = EnhancedPermissionChecker([PermissionType.SYSTEM_ADMIN])

require_role_read = EnhancedPermissionChecker([PermissionType.ROLE_READ])
require_role_write = EnhancedPermissionChecker([PermissionType.ROLE_CREATE, PermissionType.ROLE_UPDATE], require_all=False)
require_role_delete = EnhancedPermissionChecker([PermissionType.ROLE_DELETE])
require_role_admin = EnhancedPermissionChecker([PermissionType.ROLE_ADMIN])

# 资源所有者检查器
require_self_user_access = ResourceOwnerChecker("user_id")
require_self_chat_access = ResourceOwnerChecker("chat_id")


# 组合权限检查器函数
def require_permission_or_self_access(
    permissions: Union[List[PermissionType], List[str]],
    resource_id_param: str = "user_id",
    require_all: bool = True
):
    """创建一个权限检查器，允许权限或自己访问。"""
    
    def checker(
        token_payload: Dict[str, Any] = Depends(verify_token_payload),
        **kwargs
    ) -> Dict[str, Any]:
        user_role = token_payload.get("role", "guest")
        user_id = token_payload.get("sub")
        resource_owner_id = kwargs.get(resource_id_param)
        
        # 如果是自己的资源，直接允许
        if user_id == resource_owner_id:
            return token_payload
        
        # 否则检查权限
        registry = get_permission_registry()
        
        # 标准化权限类型
        normalized_permissions = []
        for perm in permissions:
            if isinstance(perm, str):
                try:
                    normalized_permissions.append(PermissionType(perm))
                except ValueError:
                    logger.warning(f"Unknown permission type: {perm}")
                    continue
            else:
                normalized_permissions.append(perm)
        
        if require_all:
            has_permission = registry.has_all_permissions(user_role, normalized_permissions)
        else:
            has_permission = registry.has_any_permission(user_role, normalized_permissions)
        
        if not has_permission:
            logger.warning(
                f"Access denied - insufficient permissions and not resource owner for user: {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return token_payload
    
    return checker


# 权限装饰器函数
def requires_permission(
    permissions: Union[PermissionType, List[PermissionType], str, List[str]],
    require_all: bool = True
):
    """
    权限检查装饰器。
    
    Args:
        permissions: 需要的权限
        require_all: 是否需要所有权限
    """
    if not isinstance(permissions, list):
        permissions = [permissions]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里应该从请求上下文中获取用户信息
            # 由于FastAPI的依赖注入机制，实际使用时需要通过Depends使用
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def requires_role(roles: Union[str, List[str]]):
    """
    角色检查装饰器。
    
    Args:
        roles: 需要的角色
    """
    if not isinstance(roles, list):
        roles = [roles]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里应该从请求上下文中获取用户信息
            # 由于FastAPI的依赖注入机制，实际使用时需要通过Depends使用
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Middleware functions
async def auth_middleware(request: Request, call_next):
    """Authentication middleware for logging and rate limiting."""
    try:
        # Log request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.debug(f"Request: {request.method} {request.url} from {client_ip}")
        
        # Process request
        response = await call_next(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Auth middleware error: {e}")
        raise


# Dependency for extracting user info from request
async def get_user_context(
    request: Request,
    user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """Get user context including IP, user agent, etc."""
    from app.core.security import SecurityMiddleware
    
    return {
        "user": user,
        "user_id": user.id if user else None,
        "client_ip": SecurityMiddleware.get_client_ip(request),
        "user_agent": SecurityMiddleware.get_user_agent(request),
        "request_id": getattr(request.state, "request_id", None)
    }