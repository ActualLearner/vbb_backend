"""Helper for writing audit entries (SRS NFR-SEC-006)."""

from __future__ import annotations

from .models import AuditLog


def record_audit(actor, action, target=None, target_type="", metadata=None):
    """Persist an :class:`AuditLog` entry.

    ``target`` may be a model instance (its pk/class are recorded) or omitted.
    Failures are swallowed deliberately: auditing must never break the action
    being audited.
    """
    try:
        target_id = ""
        if target is not None:
            target_id = str(getattr(target, "pk", "") or "")
            if not target_type:
                target_type = target.__class__.__name__
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
        )
    except Exception:  # pragma: no cover - defensive
        return None
