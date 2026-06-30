from flask import has_request_context
from flask_login import current_user

from database import db
from database.models import AuditLog


def record_audit(
    action,
    *,
    actor_user_id=None,
    target_user_id=None,
    entity_type=None,
    entity_id=None,
    details=None,
    commit=True,
):
    if actor_user_id is None and has_request_context() and current_user.is_authenticated:
        actor_user_id = int(current_user.id)

    entry = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=str(action)[:120],
        entity_type=(str(entity_type)[:80] if entity_type else None),
        entity_id=(str(entity_id)[:120] if entity_id is not None else None),
        details=dict(details or {}),
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry
