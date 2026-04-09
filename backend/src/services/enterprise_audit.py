"""
Impact Observatory | مرصد الأثر — Enterprise Audit & Governance Service

Layer: Services (L4) — Immutable audit log with SHA-256 hash chain.

Architecture Decision:
  Every tenant gets its own hash chain (sequence of SHA-256 hashes).
  Each AuditEvent computes event_hash from its fields + prev_hash,
  forming a tamper-evident ledger. The chain can be verified to detect
  any deletion or modification of audit records.

Data Flow:
  Service action → AuditService.log(tenant_id, actor, action, ...)
  → compute hash from payload + prev_hash → INSERT audit_events
  → return AuditEvent with hash chain link

Verification:
  AuditService.verify_chain(tenant_id) → walk all events in sequence
  → recompute each hash → compare → report first break (if any)

Observability:
  - Hash chain integrity check: GET /api/v1/audit/verify/{tenant_id}
  - Audit event query: GET /api/v1/audit/events?action=...&date_from=...
  - Audit stats: GET /api/v1/audit/stats

Note:
  This replaces the legacy in-memory audit_service.py for enterprise tenants.
  The legacy module remains for backward compatibility with existing simulation routes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enterprise import AuditEvent, AuditAction

logger = logging.getLogger(__name__)


class EnterpriseAuditService:
    """Immutable audit log with SHA-256 hash chain per tenant."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        tenant_id: str,
        action: str,
        *,
        actor_id: str | None = None,
        actor_email: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        description: str | None = None,
        before_json: dict | None = None,
        after_json: dict | None = None,
        metadata_json: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        """Record an audit event with hash chain linkage.

        This is the primary entry point. Every significant action in the
        platform should call this method.
        """
        # Get the previous event in this tenant's chain
        prev = await self._get_last_event(tenant_id)
        prev_hash = prev.event_hash if prev else None
        sequence = (prev.sequence + 1) if prev else 1

        # Compute timestamp and hash
        now = datetime.now(timezone.utc)
        event_hash = AuditEvent.compute_hash(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            prev_hash=prev_hash,
            timestamp=now.isoformat(),
        )

        event = AuditEvent(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
            ip_address=ip_address,
            user_agent=user_agent,
            event_hash=event_hash,
            prev_hash=prev_hash,
            sequence=sequence,
            created_at=now,
        )
        self.session.add(event)
        await self.session.flush()

        logger.debug(
            "Audit[%s] seq=%d action=%s resource=%s/%s hash=%s",
            tenant_id[:8], sequence, action,
            resource_type, resource_id, event_hash[:12],
        )
        return event

    async def query(
        self,
        tenant_id: str,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditEvent], int]:
        """Query audit events with filters."""
        q = select(AuditEvent).where(AuditEvent.tenant_id == tenant_id)

        if action:
            q = q.where(AuditEvent.action == action)
        if resource_type:
            q = q.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            q = q.where(AuditEvent.resource_id == resource_id)
        if actor_id:
            q = q.where(AuditEvent.actor_id == actor_id)
        if date_from:
            q = q.where(AuditEvent.created_at >= date_from)
        if date_to:
            q = q.where(AuditEvent.created_at <= date_to)

        # Count
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        # Paginate
        q = q.order_by(desc(AuditEvent.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        events = list(result.scalars().all())

        return events, total

    async def verify_chain(self, tenant_id: str) -> dict[str, Any]:
        """Walk the entire audit chain for a tenant and verify hash integrity.

        Returns verification report:
          - total_events: number of events in the chain
          - verified_events: number successfully verified
          - chain_valid: True if entire chain is intact
          - first_break_at: sequence number where chain breaks (None if valid)
          - verified_at: timestamp of verification
        """
        q = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.sequence.asc())
        )
        result = await self.session.execute(q)
        events = list(result.scalars().all())

        total = len(events)
        verified = 0
        first_break = None

        for event in events:
            expected_hash = AuditEvent.compute_hash(
                tenant_id=event.tenant_id,
                actor_id=event.actor_id,
                action=event.action,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                prev_hash=event.prev_hash,
                timestamp=event.created_at.isoformat(),
            )
            if expected_hash == event.event_hash:
                verified += 1
            else:
                if first_break is None:
                    first_break = event.sequence
                    logger.warning(
                        "Audit chain break at seq=%d for tenant %s: "
                        "expected=%s got=%s",
                        event.sequence, tenant_id[:8],
                        expected_hash[:12], event.event_hash[:12],
                    )

        chain_valid = verified == total and total > 0
        return {
            "tenant_id": tenant_id,
            "total_events": total,
            "verified_events": verified,
            "chain_valid": chain_valid,
            "first_break_at": first_break,
            "verified_at": datetime.now(timezone.utc),
        }

    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get audit statistics for a tenant."""
        total_q = select(func.count(AuditEvent.id)).where(AuditEvent.tenant_id == tenant_id)
        total = (await self.session.execute(total_q)).scalar() or 0

        # Action breakdown
        action_q = (
            select(AuditEvent.action, func.count(AuditEvent.id))
            .where(AuditEvent.tenant_id == tenant_id)
            .group_by(AuditEvent.action)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(20)
        )
        action_result = await self.session.execute(action_q)
        action_counts = {action: count for action, count in action_result.all()}

        # Latest event
        latest_q = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(desc(AuditEvent.sequence))
            .limit(1)
        )
        latest_result = await self.session.execute(latest_q)
        latest = latest_result.scalar_one_or_none()

        return {
            "tenant_id": tenant_id,
            "total_events": total,
            "action_breakdown": action_counts,
            "latest_sequence": latest.sequence if latest else 0,
            "latest_hash": latest.event_hash if latest else None,
            "latest_timestamp": latest.created_at.isoformat() if latest else None,
        }

    async def _get_last_event(self, tenant_id: str) -> AuditEvent | None:
        """Get the most recent audit event for hash chain linking."""
        q = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(desc(AuditEvent.sequence))
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()


# ══════════════════════════════════════════════════════════════════════════════
# Convenience: log audit from request context
# ══════════════════════════════════════════════════════════════════════════════

async def log_audit_event(
    session: AsyncSession,
    tenant_id: str,
    action: str,
    *,
    actor_id: str | None = None,
    actor_email: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    description: str | None = None,
    before_json: dict | None = None,
    after_json: dict | None = None,
    request: Any = None,
) -> AuditEvent:
    """Module-level convenience function for logging audit events.

    Extracts IP/user-agent from request if provided.
    """
    ip = None
    ua = None
    if request:
        ip = request.client.host if hasattr(request, "client") and request.client else None
        ua = request.headers.get("User-Agent") if hasattr(request, "headers") else None

    svc = EnterpriseAuditService(session)
    return await svc.log(
        tenant_id=tenant_id,
        action=action,
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        before_json=before_json,
        after_json=after_json,
        ip_address=ip,
        user_agent=ua,
    )
