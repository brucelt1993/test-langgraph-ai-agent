"""
认证服务层。

提供高级别的认证和授权服务，包括：
- 用户认证管理
- 权限验证服务
- 角色管理服务
- 会话管理
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
import logging

from app.core.security import (
    PasswordManager, TokenManager, create_user_tokens,
    verify_refresh_token, verify_token_payload
)
from app.core.permissions import (
    PermissionType, get_permission_registry, get_permission_checker,
    PermissionRegistry, PermissionChecker
)
from app.core.config import settings
from app.repositories.factory import get_repository_factory
from app.models.user import User, Role, UserSession
from fastapi import HTTPException, status, Request

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类。"""
    
    def __init__(self):
        self.permission_registry = get_permission_registry()
        self.permission_checker = get_permission_checker()
    
    async def authenticate_user(
        self, 
        username_or_email: str, 
        password: str,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        用户认证。
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            request: HTTP请求对象
            
        Returns:
            包含用户信息和令牌的字典
            
        Raises:
            HTTPException: 认证失败时抛出
        """
        try:
            async with get_repository_factory() as repo_factory:
                user_repo = repo_factory.get_user_repository()
                session_repo = repo_factory.get_user_session_repository()
                
                # 获取用户
                user = await user_repo.get_by_username_or_email(username_or_email)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
                
                # 验证密码
                if not PasswordManager.verify_password(password, user.password_hash):
                    logger.warning(f"Failed login attempt for: {username_or_email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
                
                # 检查账户状态
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Account is disabled"
                    )
                
                # 更新最后登录时间
                await user_repo.update_last_login(user.id)
                
                # 创建令牌
                user_data = self._get_user_token_data(user)
                tokens = create_user_tokens(user.id, user_data)
                
                # 记录会话
                if request:
                    await self._create_user_session(user.id, tokens["access_token"], request, session_repo)
                
                await repo_factory.commit()
                
                logger.info(f"User authenticated successfully: {user.username}")
                
                return {
                    "user": self._get_user_response_data(user),
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens["refresh_token"],
                    "token_type": "bearer",
                    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role_name: str = "user"
    ) -> Dict[str, Any]:
        """
        用户注册。
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            full_name: 全名
            role_name: 角色名称
            
        Returns:
            注册成功的用户信息
            
        Raises:
            HTTPException: 注册失败时抛出
        """
        try:
            async with get_repository_factory() as repo_factory:
                user_repo = repo_factory.get_user_repository()
                
                # 检查用户名是否存在
                if await user_repo.username_exists(username):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
                
                # 检查邮箱是否存在
                if await user_repo.email_exists(email):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
                
                # 验证密码强度
                is_valid, errors = PasswordManager.validate_password_strength(password)
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="; ".join(errors)
                    )
                
                # 哈希密码
                password_hash = PasswordManager.hash_password(password)
                
                # 创建用户
                user = await user_repo.create_user(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    role_name=role_name,
                    is_verified=False
                )
                
                await repo_factory.commit()
                
                logger.info(f"User registered: {user.username} ({user.email})")
                
                return {
                    "message": "User registered successfully",
                    "user": self._get_user_response_data(user)
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def refresh_user_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新用户令牌。
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的令牌信息
            
        Raises:
            HTTPException: 刷新失败时抛出
        """
        try:
            # 验证刷新令牌
            user_id = verify_refresh_token(refresh_token)
            
            async with get_repository_factory() as repo_factory:
                user_repo = repo_factory.get_user_repository()
                
                # 获取用户
                user = await user_repo.get_by_id(user_id, load_relations=True)
                if not user or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                # 创建新令牌
                user_data = self._get_user_token_data(user)
                tokens = create_user_tokens(user.id, user_data)
                
                logger.debug(f"Token refreshed for user: {user.username}")
                
                return {
                    "access_token": tokens["access_token"],
                    "refresh_token": tokens["refresh_token"],
                    "token_type": "bearer",
                    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """
        用户登出。
        
        Args:
            user_id: 用户ID
            
        Returns:
            登出结果
        """
        try:
            async with get_repository_factory() as repo_factory:
                session_repo = repo_factory.get_user_session_repository()
                
                # 撤销所有用户会话
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
    
    async def change_user_password(
        self, 
        user_id: str, 
        current_password: str, 
        new_password: str
    ) -> Dict[str, Any]:
        """
        修改用户密码。
        
        Args:
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Returns:
            修改结果
        """
        try:
            async with get_repository_factory() as repo_factory:
                user_repo = repo_factory.get_user_repository()
                session_repo = repo_factory.get_user_session_repository()
                
                # 获取用户
                user = await user_repo.get_by_id(user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                # 验证当前密码
                if not PasswordManager.verify_password(current_password, user.password_hash):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid current password"
                    )
                
                # 验证新密码强度
                is_valid, errors = PasswordManager.validate_password_strength(new_password)
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="; ".join(errors)
                    )
                
                # 更新密码
                new_password_hash = PasswordManager.hash_password(new_password)
                await user_repo.change_password(user_id, new_password_hash)
                
                # 撤销所有现有会话（强制重新登录）
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
    
    async def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户权限信息。
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户权限信息
        """
        try:
            async with get_repository_factory() as repo_factory:
                user_repo = repo_factory.get_user_repository()
                
                user = await user_repo.get_by_id(user_id, load_relations=True)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                role_name = user.role.name if user.role else "guest"
                effective_permissions = self.permission_registry.get_effective_permissions(role_name)
                
                return {
                    "user_id": user_id,
                    "role": {
                        "name": role_name,
                        "display_name": user.role.display_name if user.role else "游客",
                        "level": self.permission_registry.get_role(role_name).level if self.permission_registry.get_role(role_name) else 0
                    },
                    "permissions": [perm.value for perm in effective_permissions],
                    "permission_details": [
                        {
                            "name": perm.value,
                            "display_name": self.permission_registry.get_permission(perm.value).display_name,
                            "description": self.permission_registry.get_permission(perm.value).description,
                            "category": self.permission_registry.get_permission(perm.value).category
                        }
                        for perm in effective_permissions
                        if self.permission_registry.get_permission(perm.value)
                    ]
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user permissions error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user permissions"
            )
    
    def check_user_permission(
        self, 
        user_role: str, 
        permission: Union[PermissionType, str],
        resource_owner_id: Optional[str] = None,
        current_user_id: Optional[str] = None
    ) -> bool:
        """
        检查用户权限。
        
        Args:
            user_role: 用户角色
            permission: 权限
            resource_owner_id: 资源拥有者ID
            current_user_id: 当前用户ID
            
        Returns:
            是否有权限
        """
        if isinstance(permission, str):
            try:
                permission = PermissionType(permission)
            except ValueError:
                logger.warning(f"Unknown permission type: {permission}")
                return False
        
        return self.permission_checker.check_permission(
            user_role, permission, resource_owner_id, current_user_id
        )
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户会话列表。
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户会话列表
        """
        try:
            async with get_repository_factory() as repo_factory:
                session_repo = repo_factory.get_user_session_repository()
                
                sessions = await session_repo.get_active_sessions(user_id)
                
                return [
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
                
        except Exception as e:
            logger.error(f"Get user sessions error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user sessions"
            )
    
    async def revoke_user_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        撤销用户会话。
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            撤销结果
        """
        try:
            async with get_repository_factory() as repo_factory:
                session_repo = repo_factory.get_user_session_repository()
                
                # 验证会话归属
                session = await session_repo.get_by_id(session_id)
                if not session or session.user_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Session not found"
                    )
                
                # 撤销会话
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
    
    def _get_user_token_data(self, user: User) -> Dict[str, Any]:
        """获取用户令牌数据。"""
        return {
            "username": user.username,
            "email": user.email,
            "role": user.role.name if user.role else "guest",
            "permissions": str([p.value for p in self.permission_registry.get_effective_permissions(
                user.role.name if user.role else "guest"
            )])
        }
    
    def _get_user_response_data(self, user: User) -> Dict[str, Any]:
        """获取用户响应数据。"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "role": {
                "id": user.role.id,
                "name": user.role.name,
                "display_name": user.role.display_name,
                "permissions": str([p.value for p in self.permission_registry.get_effective_permissions(user.role.name)])
            } if user.role else {},
            "created_at": user.created_at,
            "last_login_at": user.last_login_at
        }
    
    async def _create_user_session(
        self, 
        user_id: str, 
        access_token: str, 
        request: Request, 
        session_repo
    ):
        """创建用户会话记录。"""
        from app.core.security import SecurityMiddleware
        
        client_ip = SecurityMiddleware.get_client_ip(request)
        user_agent = SecurityMiddleware.get_user_agent(request)
        
        token_hash = TokenManager.get_token_hash(access_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        await session_repo.create_session(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=user_agent,
            ip_address=client_ip
        )


class RoleService:
    """角色管理服务。"""
    
    def __init__(self):
        self.permission_registry = get_permission_registry()
    
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色。"""
        roles = self.permission_registry.get_all_roles()
        return [
            {
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "level": role.level,
                "permissions": [p.value for p in role.permissions],
                "parent_roles": list(role.parent_roles) if role.parent_roles else [],
                "effective_permissions": [p.value for p in self.permission_registry.get_effective_permissions(role.name)]
            }
            for role in roles.values()
        ]
    
    async def get_role_info(self, role_name: str) -> Dict[str, Any]:
        """获取角色信息。"""
        role = self.permission_registry.get_role(role_name)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return {
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "level": role.level,
            "permissions": [p.value for p in role.permissions],
            "parent_roles": list(role.parent_roles) if role.parent_roles else [],
            "effective_permissions": [p.value for p in self.permission_registry.get_effective_permissions(role.name)]
        }
    
    async def get_all_permissions(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有权限（按类别分组）。"""
        return {
            category: [
                {
                    "name": perm.name,
                    "display_name": perm.display_name,
                    "description": perm.description,
                    "level": perm.level
                }
                for perm in permissions
            ]
            for category, permissions in self.permission_registry.get_permission_categories().items()
        }


# 创建全局服务实例
auth_service = AuthService()
role_service = RoleService()


def get_auth_service() -> AuthService:
    """获取认证服务实例。"""
    return auth_service


def get_role_service() -> RoleService:
    """获取角色服务实例。"""
    return role_service