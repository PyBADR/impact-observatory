"""
Impact Observatory | مرصد الأثر — RBAC Service

Layer: Services (L4) — Role-Based Access Control for multi-tenant platform.

Architecture Decision:
  Tenant-scoped RBAC with system roles (ADMIN, Underwriter, Claims Adjuster,
  Analyst, Viewer) that are auto-seeded on tenant creation. Custom roles can be
  added per tenant. Permissions follow resource:action pattern.

Data Flow:
  JWT → TenantContext → RBACService.check_permission(tenant_id, user_id, resource, action)
  → DB lookup (roles + permissions) → allow/deny

System Roles (seeded per tenant):
  ADMIN            — Full platform access
  UNDERWRITER      — Create/manage underwriting workflows, approve risk assessments
  CLAIMS_ADJUSTER  — Create/manage claims workflows, approve payouts
  ANALYST          — Run simulations, view reports, read-only decisions
  VIEWER           — Read-only access to dashboards and reports
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enterprise import (
    Role, Permission, User, UserRole, Tenant,
    TenantStatus, UserStatus,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# System Role Definitions (seeded on tenant creation)
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_ROLES: dict[str, dict[str, Any]] = {
    "ADMIN": {
        "name_ar": "مدير النظام",
        "description": "Full platform access — user management, settings, all operations",
        "permissions": [
            ("tenant", "read"), ("tenant", "update"), ("tenant", "settings"),
            ("user", "create"), ("user", "read"), ("user", "update"), ("user", "delete"),
            ("role", "create"), ("role", "read"), ("role", "update"), ("role", "delete"),
            ("workflow", "create"), ("workflow", "read"), ("workflow", "update"), ("workflow", "delete"), ("workflow", "execute"),
            ("decision", "create"), ("decision", "read"), ("decision", "approve"), ("decision", "reject"), ("decision", "execute"),
            ("simulation", "create"), ("simulation", "read"),
            ("report", "executive"), ("report", "analyst"), ("report", "regulatory"),
            ("audit", "read"), ("audit", "stats"), ("audit", "export"),
            ("policy", "create"), ("policy", "read"), ("policy", "update"), ("policy", "delete"),
        ],
    },
    "UNDERWRITER": {
        "name_ar": "مكتتب",
        "description": "Manage underwriting workflows, approve risk assessments, view reports",
        "permissions": [
            ("workflow", "create"), ("workflow", "read"), ("workflow", "execute"),
            ("decision", "create"), ("decision", "read"), ("decision", "approve"), ("decision", "reject"),
            ("simulation", "create"), ("simulation", "read"),
            ("report", "analyst"),
            ("audit", "read"),
            ("policy", "read"),
        ],
    },
    "CLAIMS_ADJUSTER": {
        "name_ar": "مسؤول المطالبات",
        "description": "Manage claims workflows, approve payouts, investigate fraud flags",
        "permissions": [
            ("workflow", "create"), ("workflow", "read"), ("workflow", "execute"),
            ("decision", "create"), ("decision", "read"), ("decision", "approve"),
            ("simulation", "read"),
            ("report", "analyst"),
            ("audit", "read"),
            ("policy", "read"),
        ],
    },
    "ANALYST": {
        "name_ar": "محلل",
        "description": "Run simulations, view all reports, read-only decision access",
        "permissions": [
            ("simulation", "create"), ("simulation", "read"),
            ("decision", "read"),
            ("workflow", "read"),
            ("report", "executive"), ("report", "analyst"),
            ("audit", "read"), ("audit", "stats"),
            ("policy", "read"),
        ],
    },
    "VIEWER": {
        "name_ar": "مشاهد",
        "description": "Read-only access to dashboards, reports, and public data",
        "permissions": [
            ("simulation", "read"),
            ("decision", "read"),
            ("workflow", "read"),
            ("report", "analyst"),
            ("audit", "read"),
            ("policy", "read"),
        ],
    },
}


class RBACService:
    """Tenant-scoped Role-Based Access Control service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Tenant Management ─────────────────────────────────────────────────

    async def create_tenant(
        self,
        name: str,
        slug: str,
        *,
        name_ar: str | None = None,
        domain: str | None = None,
        tier: str = "standard",
        max_users: int = 50,
        max_workflows_per_month: int = 1000,
        settings_json: dict | None = None,
    ) -> Tenant:
        """Create a new tenant and seed system roles + permissions."""
        tenant = Tenant(
            name=name,
            name_ar=name_ar,
            slug=slug,
            domain=domain,
            tier=tier,
            status=TenantStatus.ACTIVE,
            max_users=max_users,
            max_workflows_per_month=max_workflows_per_month,
            settings_json=settings_json,
        )
        self.session.add(tenant)
        await self.session.flush()  # get tenant.id

        # Seed system roles
        await self._seed_system_roles(tenant.id)
        await self.session.flush()

        logger.info("Tenant created: %s (%s)", tenant.name, tenant.slug)
        return tenant

    async def get_tenant(self, tenant_id: str) -> Tenant | None:
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_tenants(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[Tenant], int]:
        count_q = select(func.count(Tenant.id))
        total = (await self.session.execute(count_q)).scalar() or 0

        q = (
            select(Tenant)
            .order_by(Tenant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update_tenant(self, tenant_id: str, **updates) -> Tenant | None:
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        for k, v in updates.items():
            if v is not None and hasattr(tenant, k):
                setattr(tenant, k, v)
        await self.session.flush()
        return tenant

    # ── Role Management ──────────────────────────────────────────────────

    async def _seed_system_roles(self, tenant_id: str) -> list[Role]:
        """Create the 5 system roles + permissions for a new tenant."""
        roles = []
        for role_name, role_def in SYSTEM_ROLES.items():
            role = Role(
                tenant_id=tenant_id,
                name=role_name,
                name_ar=role_def["name_ar"],
                description=role_def["description"],
                is_system=True,
            )
            self.session.add(role)
            await self.session.flush()

            for resource, action in role_def["permissions"]:
                perm = Permission(
                    role_id=role.id,
                    resource=resource,
                    action=action,
                )
                self.session.add(perm)

            roles.append(role)
        return roles

    async def create_role(
        self,
        tenant_id: str,
        name: str,
        *,
        name_ar: str | None = None,
        description: str | None = None,
        permissions: list[tuple[str, str]] | None = None,
    ) -> Role:
        """Create a custom role with permissions."""
        role = Role(
            tenant_id=tenant_id,
            name=name,
            name_ar=name_ar,
            description=description,
            is_system=False,
        )
        self.session.add(role)
        await self.session.flush()

        if permissions:
            for resource, action in permissions:
                perm = Permission(role_id=role.id, resource=resource, action=action)
                self.session.add(perm)

        logger.info("Role created: %s for tenant %s", name, tenant_id)
        return role

    async def get_roles(self, tenant_id: str) -> list[Role]:
        result = await self.session.execute(
            select(Role)
            .where(Role.tenant_id == tenant_id)
            .order_by(Role.is_system.desc(), Role.name)
        )
        return list(result.scalars().all())

    async def get_role_by_name(self, tenant_id: str, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role).where(
                and_(Role.tenant_id == tenant_id, Role.name == name)
            )
        )
        return result.scalar_one_or_none()

    async def delete_role(self, role_id: str) -> bool:
        """Delete a role. System roles cannot be deleted."""
        result = await self.session.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            return False
        if role.is_system:
            raise ValueError(f"Cannot delete system role: {role.name}")
        await self.session.delete(role)
        return True

    # ── User Management ──────────────────────────────────────────────────

    async def create_user(
        self,
        tenant_id: str,
        email: str,
        name: str,
        password_hash: str,
        *,
        name_ar: str | None = None,
        role_names: list[str] | None = None,
        mfa_enabled: bool = False,
        metadata_json: dict | None = None,
    ) -> User:
        """Create a user and assign roles."""
        # Check tenant user limit
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")

        user_count = (await self.session.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        )).scalar() or 0

        if user_count >= tenant.max_users:
            raise ValueError(
                f"Tenant user limit reached: {user_count}/{tenant.max_users}"
            )

        user = User(
            tenant_id=tenant_id,
            email=email,
            name=name,
            name_ar=name_ar,
            password_hash=password_hash,
            status=UserStatus.ACTIVE,
            mfa_enabled=mfa_enabled,
            metadata_json=metadata_json,
        )
        self.session.add(user)
        await self.session.flush()

        # Assign roles
        if role_names:
            for rn in role_names:
                role = await self.get_role_by_name(tenant_id, rn)
                if role:
                    ur = UserRole(user_id=user.id, role_id=role.id)
                    self.session.add(ur)

        logger.info("User created: %s in tenant %s", email, tenant_id)
        return user

    async def get_user(self, tenant_id: str, user_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                and_(User.tenant_id == tenant_id, User.id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, tenant_id: str, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                and_(User.tenant_id == tenant_id, User.email == email)
            )
        )
        return result.scalar_one_or_none()

    async def list_users(
        self, tenant_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        count_q = select(func.count(User.id)).where(User.tenant_id == tenant_id)
        total = (await self.session.execute(count_q)).scalar() or 0

        q = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def assign_role(
        self, user_id: str, role_id: str, assigned_by: str | None = None
    ) -> UserRole:
        ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        self.session.add(ur)
        return ur

    async def revoke_role(self, user_id: str, role_id: str) -> bool:
        result = await self.session.execute(
            select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            )
        )
        ur = result.scalar_one_or_none()
        if not ur:
            return False
        await self.session.delete(ur)
        return True

    # ── Permission Checks ────────────────────────────────────────────────

    async def get_user_permissions(
        self, tenant_id: str, user_id: str
    ) -> list[str]:
        """Get all resource:action permission strings for a user."""
        q = (
            select(Permission.resource, Permission.action)
            .join(Role, Permission.role_id == Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Role.tenant_id == tenant_id,
                )
            )
        )
        result = await self.session.execute(q)
        return [f"{r}:{a}" for r, a in result.all()]

    async def get_user_role_names(
        self, tenant_id: str, user_id: str
    ) -> list[str]:
        """Get all role names for a user in a tenant."""
        q = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Role.tenant_id == tenant_id,
                )
            )
        )
        result = await self.session.execute(q)
        return [r for (r,) in result.all()]

    async def check_permission(
        self, tenant_id: str, user_id: str, resource: str, action: str
    ) -> bool:
        """Check if a user has a specific permission in a tenant."""
        perms = await self.get_user_permissions(tenant_id, user_id)
        return f"{resource}:{action}" in perms

    # ── Auth Helper ──────────────────────────────────────────────────────

    async def build_token_claims(
        self, tenant_id: str, user_id: str
    ) -> dict[str, Any]:
        """Build JWT claims dict with roles and permissions for a user.

        Used by the auth endpoint after password verification to create
        a tenant-scoped JWT with full RBAC claims.
        """
        user = await self.get_user(tenant_id, user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")

        roles = await self.get_user_role_names(tenant_id, user_id)
        permissions = await self.get_user_permissions(tenant_id, user_id)

        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "tenant_id": tenant.id,
            "tenant_slug": tenant.slug,
            "tenant_name": tenant.name,
            "roles": roles,
            "permissions": permissions,
            "primary_role": roles[0] if roles else "VIEWER",
        }
