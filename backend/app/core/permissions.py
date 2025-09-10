"""
RBAC权限管理核心模块。

提供完整的基于角色的访问控制系统，包括：
- 权限定义和管理
- 角色层次结构
- 权限检查缓存
- 动态权限验证
"""

from enum import Enum
from typing import Set, Dict, List, Optional, Any
from dataclasses import dataclass
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class PermissionType(str, Enum):
    """权限类型枚举。"""
    
    # 用户管理权限
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"
    
    # 聊天相关权限
    CHAT_READ = "chat:read"
    CHAT_CREATE = "chat:create"
    CHAT_UPDATE = "chat:update"
    CHAT_DELETE = "chat:delete"
    CHAT_ADMIN = "chat:admin"
    
    # AI Agent权限
    AGENT_USE = "agent:use"
    AGENT_CONFIG = "agent:config"
    AGENT_ADMIN = "agent:admin"
    
    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_ADMIN = "system:admin"
    
    # 角色管理权限
    ROLE_READ = "role:read"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_ADMIN = "role:admin"


@dataclass
class Permission:
    """权限定义。"""
    name: str
    display_name: str
    description: str
    category: str
    level: int = 1  # 权限级别，越高权限越大


@dataclass
class RoleDefinition:
    """角色定义。"""
    name: str
    display_name: str
    description: str
    permissions: Set[PermissionType]
    parent_roles: Set[str] = None
    level: int = 1


class PermissionRegistry:
    """权限注册中心。"""
    
    def __init__(self):
        self._permissions: Dict[str, Permission] = {}
        self._roles: Dict[str, RoleDefinition] = {}
        self._permission_hierarchy: Dict[str, Set[str]] = {}
        self._role_hierarchy: Dict[str, Set[str]] = {}
        self._register_default_permissions()
        self._register_default_roles()
    
    def _register_default_permissions(self):
        """注册默认权限。"""
        default_permissions = [
            # 用户管理权限
            Permission("user:read", "查看用户", "查看用户基本信息", "用户管理", 1),
            Permission("user:create", "创建用户", "创建新用户账户", "用户管理", 2),
            Permission("user:update", "更新用户", "修改用户信息", "用户管理", 2),
            Permission("user:delete", "删除用户", "删除用户账户", "用户管理", 3),
            Permission("user:admin", "用户管理员", "完整用户管理权限", "用户管理", 4),
            
            # 聊天权限
            Permission("chat:read", "查看聊天", "查看聊天记录", "聊天管理", 1),
            Permission("chat:create", "创建聊天", "创建新的聊天会话", "聊天管理", 1),
            Permission("chat:update", "更新聊天", "修改聊天信息", "聊天管理", 2),
            Permission("chat:delete", "删除聊天", "删除聊天记录", "聊天管理", 2),
            Permission("chat:admin", "聊天管理员", "完整聊天管理权限", "聊天管理", 3),
            
            # AI Agent权限
            Permission("agent:use", "使用AI", "使用AI Agent功能", "AI功能", 1),
            Permission("agent:config", "配置AI", "配置AI Agent参数", "AI功能", 2),
            Permission("agent:admin", "AI管理员", "完整AI功能管理权限", "AI功能", 3),
            
            # 系统权限
            Permission("system:config", "系统配置", "修改系统配置", "系统管理", 3),
            Permission("system:logs", "系统日志", "查看系统日志", "系统管理", 2),
            Permission("system:admin", "系统管理员", "完整系统管理权限", "系统管理", 4),
            
            # 角色权限
            Permission("role:read", "查看角色", "查看角色信息", "角色管理", 2),
            Permission("role:create", "创建角色", "创建新角色", "角色管理", 3),
            Permission("role:update", "更新角色", "修改角色信息", "角色管理", 3),
            Permission("role:delete", "删除角色", "删除角色", "角色管理", 4),
            Permission("role:admin", "角色管理员", "完整角色管理权限", "角色管理", 4),
        ]
        
        for perm in default_permissions:
            self._permissions[perm.name] = perm
    
    def _register_default_roles(self):
        """注册默认角色。"""
        default_roles = [
            RoleDefinition(
                name="guest",
                display_name="游客",
                description="基础访问权限，只能查看公开内容",
                permissions=set(),
                level=0
            ),
            RoleDefinition(
                name="user",
                display_name="普通用户",
                description="标准用户权限，可以使用基本功能",
                permissions={
                    PermissionType.CHAT_READ,
                    PermissionType.CHAT_CREATE,
                    PermissionType.CHAT_UPDATE,
                    PermissionType.AGENT_USE,
                    PermissionType.USER_READ
                },
                level=1
            ),
            RoleDefinition(
                name="premium",
                display_name="高级用户", 
                description="高级用户权限，包含更多AI功能",
                permissions={
                    PermissionType.CHAT_READ,
                    PermissionType.CHAT_CREATE,
                    PermissionType.CHAT_UPDATE,
                    PermissionType.CHAT_DELETE,
                    PermissionType.AGENT_USE,
                    PermissionType.AGENT_CONFIG,
                    PermissionType.USER_READ,
                    PermissionType.USER_UPDATE
                },
                parent_roles={"user"},
                level=2
            ),
            RoleDefinition(
                name="moderator",
                display_name="版主",
                description="内容管理权限，可以管理用户内容",
                permissions={
                    PermissionType.CHAT_READ,
                    PermissionType.CHAT_CREATE,
                    PermissionType.CHAT_UPDATE,
                    PermissionType.CHAT_DELETE,
                    PermissionType.CHAT_ADMIN,
                    PermissionType.AGENT_USE,
                    PermissionType.AGENT_CONFIG,
                    PermissionType.USER_READ,
                    PermissionType.USER_UPDATE,
                    PermissionType.ROLE_READ
                },
                parent_roles={"premium"},
                level=3
            ),
            RoleDefinition(
                name="admin",
                display_name="管理员",
                description="完整管理权限，可以管理所有功能",
                permissions={
                    PermissionType.USER_READ,
                    PermissionType.USER_CREATE,
                    PermissionType.USER_UPDATE,
                    PermissionType.USER_DELETE,
                    PermissionType.USER_ADMIN,
                    PermissionType.CHAT_READ,
                    PermissionType.CHAT_CREATE,
                    PermissionType.CHAT_UPDATE,
                    PermissionType.CHAT_DELETE,
                    PermissionType.CHAT_ADMIN,
                    PermissionType.AGENT_USE,
                    PermissionType.AGENT_CONFIG,
                    PermissionType.AGENT_ADMIN,
                    PermissionType.SYSTEM_CONFIG,
                    PermissionType.SYSTEM_LOGS,
                    PermissionType.SYSTEM_ADMIN,
                    PermissionType.ROLE_READ,
                    PermissionType.ROLE_CREATE,
                    PermissionType.ROLE_UPDATE,
                    PermissionType.ROLE_DELETE,
                    PermissionType.ROLE_ADMIN
                },
                parent_roles={"moderator"},
                level=4
            ),
            RoleDefinition(
                name="superadmin",
                display_name="超级管理员",
                description="最高权限，拥有所有权限",
                permissions=set(PermissionType),
                parent_roles={"admin"},
                level=5
            )
        ]
        
        for role in default_roles:
            self._roles[role.name] = role
        
        self._build_role_hierarchy()
    
    def _build_role_hierarchy(self):
        """构建角色层次结构。"""
        for role_name, role_def in self._roles.items():
            if role_def.parent_roles:
                for parent in role_def.parent_roles:
                    if parent not in self._role_hierarchy:
                        self._role_hierarchy[parent] = set()
                    self._role_hierarchy[parent].add(role_name)
    
    def get_permission(self, name: str) -> Optional[Permission]:
        """获取权限定义。"""
        return self._permissions.get(name)
    
    def get_role(self, name: str) -> Optional[RoleDefinition]:
        """获取角色定义。"""
        return self._roles.get(name)
    
    def get_all_permissions(self) -> Dict[str, Permission]:
        """获取所有权限。"""
        return self._permissions.copy()
    
    def get_all_roles(self) -> Dict[str, RoleDefinition]:
        """获取所有角色。"""
        return self._roles.copy()
    
    @lru_cache(maxsize=128)
    def get_effective_permissions(self, role_name: str) -> Set[PermissionType]:
        """获取角色的有效权限（包括继承权限）。"""
        if role_name not in self._roles:
            return set()
        
        role = self._roles[role_name]
        permissions = role.permissions.copy()
        
        # 递归获取父角色权限
        if role.parent_roles:
            for parent_role in role.parent_roles:
                parent_permissions = self.get_effective_permissions(parent_role)
                permissions.update(parent_permissions)
        
        return permissions
    
    def has_permission(self, role_name: str, permission: PermissionType) -> bool:
        """检查角色是否有指定权限。"""
        effective_permissions = self.get_effective_permissions(role_name)
        return permission in effective_permissions
    
    def has_any_permission(self, role_name: str, permissions: List[PermissionType]) -> bool:
        """检查角色是否有任意一个指定权限。"""
        effective_permissions = self.get_effective_permissions(role_name)
        return any(perm in effective_permissions for perm in permissions)
    
    def has_all_permissions(self, role_name: str, permissions: List[PermissionType]) -> bool:
        """检查角色是否有所有指定权限。"""
        effective_permissions = self.get_effective_permissions(role_name)
        return all(perm in effective_permissions for perm in permissions)
    
    def is_role_higher_than(self, role1: str, role2: str) -> bool:
        """检查角色1是否比角色2权限更高。"""
        r1 = self._roles.get(role1)
        r2 = self._roles.get(role2)
        
        if not r1 or not r2:
            return False
        
        return r1.level > r2.level
    
    def get_permission_categories(self) -> Dict[str, List[Permission]]:
        """按类别获取权限。"""
        categories = {}
        for perm in self._permissions.values():
            if perm.category not in categories:
                categories[perm.category] = []
            categories[perm.category].append(perm)
        
        # 按权限级别排序
        for category in categories:
            categories[category].sort(key=lambda p: p.level)
        
        return categories


class PermissionChecker:
    """权限检查器。"""
    
    def __init__(self, registry: PermissionRegistry = None):
        self.registry = registry or permission_registry
    
    def check_permission(
        self, 
        user_role: str, 
        required_permission: PermissionType,
        resource_owner_id: Optional[str] = None,
        current_user_id: Optional[str] = None
    ) -> bool:
        """
        检查权限。
        
        Args:
            user_role: 用户角色
            required_permission: 需要的权限
            resource_owner_id: 资源拥有者ID（可选）
            current_user_id: 当前用户ID（可选）
            
        Returns:
            是否有权限
        """
        # 基础权限检查
        if self.registry.has_permission(user_role, required_permission):
            return True
        
        # 资源所有者检查（用户可以操作自己的资源）
        if resource_owner_id and current_user_id and resource_owner_id == current_user_id:
            # 检查是否是自己的资源的读写权限
            if required_permission in [
                PermissionType.USER_READ, 
                PermissionType.USER_UPDATE,
                PermissionType.CHAT_READ,
                PermissionType.CHAT_UPDATE,
                PermissionType.CHAT_DELETE
            ]:
                return True
        
        return False
    
    def check_multiple_permissions(
        self,
        user_role: str,
        required_permissions: List[PermissionType],
        require_all: bool = True
    ) -> bool:
        """
        检查多个权限。
        
        Args:
            user_role: 用户角色
            required_permissions: 需要的权限列表
            require_all: 是否需要所有权限
            
        Returns:
            是否有权限
        """
        if require_all:
            return self.registry.has_all_permissions(user_role, required_permissions)
        else:
            return self.registry.has_any_permission(user_role, required_permissions)


# 全局权限注册中心实例
permission_registry = PermissionRegistry()

# 全局权限检查器实例
permission_checker = PermissionChecker(permission_registry)


def get_permission_registry() -> PermissionRegistry:
    """获取权限注册中心。"""
    return permission_registry


def get_permission_checker() -> PermissionChecker:
    """获取权限检查器。"""
    return permission_checker