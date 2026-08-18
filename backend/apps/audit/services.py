from .models import AuditLog


def record(*, actor, action: str, description: str, request=None) -> AuditLog:
    """Persist a minimal audit event without request bodies or sensitive content."""
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        description=description[:255],
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:255] if request else ""),
    )
