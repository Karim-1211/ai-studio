import os
from datetime import timedelta

from flask import current_app
from sqlalchemy import case, func

from database import db
from database.models import (
    AuditLog,
    Chat,
    Document,
    GlobalDocument,
    HealthCheckEvent,
    Message,
    MessageAttachment,
    ModelUsageEvent,
    RequestMetric,
    SocialSource,
    User,
    WebsiteSource,
    user_social_sources,
    user_website_sources,
    utcnow,
)
from services.deletion_service import find_orphan_uploads, remove_orphan_uploads


def _safe_int(value):
    return int(value or 0)


def _storage_bytes_for_user(user_id):
    chat_document_bytes = db.session.query(func.coalesce(func.sum(Document.file_size), 0)).join(
        Chat, Document.chat_id == Chat.id
    ).filter(Chat.user_id == user_id).scalar()

    attachment_bytes = db.session.query(
        func.coalesce(func.sum(MessageAttachment.file_size), 0)
    ).join(Chat, MessageAttachment.chat_id == Chat.id).filter(
        Chat.user_id == user_id
    ).scalar()

    global_bytes = db.session.query(
        func.coalesce(func.sum(GlobalDocument.file_size), 0)
    ).filter(GlobalDocument.user_id == user_id).scalar()

    return _safe_int(chat_document_bytes) + _safe_int(attachment_bytes) + _safe_int(global_bytes)


def get_admin_analytics(days=30):
    days = max(1, min(365, int(days)))
    since = utcnow() - timedelta(days=days)

    users = User.query.order_by(User.created_at.asc()).all()
    per_user = []
    for user in users:
        chat_count = Chat.query.filter(Chat.user_id == user.id).count()
        message_count = db.session.query(func.count(Message.id)).join(
            Chat, Message.chat_id == Chat.id
        ).filter(Chat.user_id == user.id).scalar()
        document_count = db.session.query(func.count(Document.id)).join(
            Chat, Document.chat_id == Chat.id
        ).filter(Chat.user_id == user.id).scalar()
        attachment_count = db.session.query(func.count(MessageAttachment.id)).join(
            Chat, MessageAttachment.chat_id == Chat.id
        ).filter(Chat.user_id == user.id).scalar()
        global_count = GlobalDocument.query.filter(GlobalDocument.user_id == user.id).count()
        website_count = db.session.query(func.count(user_website_sources.c.website_source_id)).filter(
            user_website_sources.c.user_id == user.id
        ).scalar()
        social_count = db.session.query(func.count(user_social_sources.c.social_source_id)).filter(
            user_social_sources.c.user_id == user.id
        ).scalar()
        per_user.append({
            "id": user.id,
            "display_name": user.display_name,
            "email": user.email,
            "active": bool(user.active),
            "is_admin": bool(user.is_admin),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "chat_count": _safe_int(chat_count),
            "message_count": _safe_int(message_count),
            "document_count": _safe_int(document_count) + _safe_int(global_count),
            "attachment_count": _safe_int(attachment_count),
            "website_count": _safe_int(website_count),
            "social_count": _safe_int(social_count),
            "storage_bytes": _storage_bytes_for_user(user.id),
        })

    model_rows = db.session.query(
        ModelUsageEvent.model,
        func.count(ModelUsageEvent.id),
        func.avg(ModelUsageEvent.duration_ms),
        func.sum(case((ModelUsageEvent.success.is_(False), 1), else_=0)),
    ).filter(ModelUsageEvent.created_at >= since).group_by(
        ModelUsageEvent.model
    ).order_by(func.count(ModelUsageEvent.id).desc()).all()

    model_usage = [
        {
            "model": row[0],
            "requests": _safe_int(row[1]),
            "average_duration_ms": round(float(row[2] or 0), 1),
            "failures": _safe_int(row[3]),
        }
        for row in model_rows
    ]

    request_total = RequestMetric.query.filter(RequestMetric.created_at >= since).count()
    failed_request_count = RequestMetric.query.filter(
        RequestMetric.created_at >= since,
        RequestMetric.is_error.is_(True),
    ).count()
    average_request_duration = db.session.query(func.avg(RequestMetric.duration_ms)).filter(
        RequestMetric.created_at >= since
    ).scalar()
    average_model_duration = db.session.query(func.avg(ModelUsageEvent.duration_ms)).filter(
        ModelUsageEvent.created_at >= since,
        ModelUsageEvent.success.is_(True),
    ).scalar()

    recent_failures = RequestMetric.query.filter(
        RequestMetric.is_error.is_(True),
        RequestMetric.created_at >= since,
    ).order_by(RequestMetric.created_at.desc()).limit(25).all()

    recent_health = HealthCheckEvent.query.filter(
        HealthCheckEvent.created_at >= since
    ).order_by(HealthCheckEvent.created_at.desc()).limit(25).all()

    recent_audit = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(40).all()

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    orphan_paths = find_orphan_uploads(upload_folder)
    upload_disk_bytes = 0
    if os.path.isdir(upload_folder):
        for root, _dirs, files in os.walk(upload_folder):
            for filename in files:
                path = os.path.join(root, filename)
                try:
                    upload_disk_bytes += os.path.getsize(path)
                except OSError:
                    pass

    return {
        "days": days,
        "summary": {
            "users": len(users),
            "active_users": sum(1 for user in users if user.active),
            "disabled_users": sum(1 for user in users if not user.active),
            "chats": Chat.query.count(),
            "messages": Message.query.count(),
            "global_documents": GlobalDocument.query.count(),
            "websites": WebsiteSource.query.count(),
            "social_sources": SocialSource.query.count(),
            "request_count": request_total,
            "failed_requests": failed_request_count,
            "average_request_duration_ms": round(float(average_request_duration or 0), 1),
            "average_model_duration_ms": round(float(average_model_duration or 0), 1),
            "upload_disk_bytes": upload_disk_bytes,
            "orphan_uploads": len(orphan_paths),
        },
        "users": per_user,
        "model_usage": model_usage,
        "recent_failures": [
            {
                "request_id": item.request_id,
                "method": item.method,
                "path": item.path,
                "status_code": item.status_code,
                "duration_ms": item.duration_ms,
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_failures
        ],
        "health_history": [
            {
                "status": item.status,
                "ready": item.ready,
                "duration_ms": item.duration_ms,
                "components": item.components,
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_health
        ],
        "audit_log": [
            {
                "id": item.id,
                "actor_user_id": item.actor_user_id,
                "target_user_id": item.target_user_id,
                "action": item.action,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "details": item.details or {},
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_audit
        ],
    }


def purge_telemetry(retention_days):
    retention_days = max(7, min(3650, int(retention_days)))
    cutoff = utcnow() - timedelta(days=retention_days)
    request_count = RequestMetric.query.filter(RequestMetric.created_at < cutoff).delete(
        synchronize_session=False
    )
    health_count = HealthCheckEvent.query.filter(HealthCheckEvent.created_at < cutoff).delete(
        synchronize_session=False
    )
    model_count = ModelUsageEvent.query.filter(ModelUsageEvent.created_at < cutoff).delete(
        synchronize_session=False
    )
    db.session.commit()
    return {
        "request_metrics": request_count,
        "health_events": health_count,
        "model_events": model_count,
        "retention_days": retention_days,
    }


def cleanup_orphan_uploads(delete=False):
    if delete:
        result = remove_orphan_uploads(current_app.config["UPLOAD_FOLDER"])
        return {
            "removed": [os.path.basename(path) for path in result.get("removed", [])],
            "failures": [
                {
                    "path": os.path.basename(item.get("path", "")),
                    "error": item.get("error", "Unknown error"),
                }
                for item in result.get("failures", [])
            ],
        }
    paths = find_orphan_uploads(current_app.config["UPLOAD_FOLDER"])
    return {
        "files": [os.path.basename(path) for path in paths],
        "count": len(paths),
    }


def record_request_metric(
    *,
    request_id,
    method,
    path,
    endpoint,
    status_code,
    duration_ms,
    user_id=None,
):
    values = {
        "user_id": user_id,
        "request_id": str(request_id)[:64],
        "method": str(method)[:12],
        "path": str(path)[:512],
        "endpoint": (str(endpoint)[:160] if endpoint else None),
        "status_code": int(status_code),
        "duration_ms": float(duration_ms) if duration_ms is not None else None,
        "is_error": int(status_code) >= 400,
        "created_at": utcnow(),
    }
    try:
        with db.engine.begin() as connection:
            result = connection.execute(RequestMetric.__table__.insert().values(**values))
        return result.inserted_primary_key[0] if result.inserted_primary_key else None
    except Exception:
        return None


def record_model_usage(
    *,
    model,
    mode=None,
    duration_ms=None,
    success=True,
    used_rag=False,
    source_count=0,
    error_message=None,
    request_id=None,
    chat_id=None,
    user_id=None,
):
    values = {
        "user_id": user_id,
        "chat_id": chat_id,
        "request_id": (str(request_id)[:64] if request_id else None),
        "model": str(model)[:200],
        "mode": (str(mode)[:50] if mode else None),
        "duration_ms": float(duration_ms) if duration_ms is not None else None,
        "success": bool(success),
        "used_rag": bool(used_rag),
        "source_count": max(0, int(source_count or 0)),
        "error_message": (str(error_message)[:500] if error_message else None),
        "created_at": utcnow(),
    }
    try:
        with db.engine.begin() as connection:
            result = connection.execute(ModelUsageEvent.__table__.insert().values(**values))
        return result.inserted_primary_key[0] if result.inserted_primary_key else None
    except Exception:
        return None


def record_health_event(result, duration_ms=None, minimum_interval_seconds=300):
    try:
        latest = HealthCheckEvent.query.order_by(
            HealthCheckEvent.created_at.desc()
        ).first()
        now = utcnow()
        should_record = latest is None
        if latest is not None:
            age = (now - latest.created_at).total_seconds()
            should_record = (
                age >= max(30, int(minimum_interval_seconds))
                or latest.status != result.get("status")
                or bool(latest.ready) != bool(result.get("ready"))
            )
        if not should_record:
            return latest.id

        components = {
            name: {
                "ok": bool(component.get("ok")),
                "status": component.get("status"),
                "latency_ms": component.get("latency_ms"),
            }
            for name, component in (result.get("components") or {}).items()
        }
        values = {
            "status": str(result.get("status") or "unknown")[:30],
            "ready": bool(result.get("ready")),
            "duration_ms": float(duration_ms) if duration_ms is not None else None,
            "components": components,
            "created_at": now,
        }
        with db.engine.begin() as connection:
            inserted = connection.execute(
                HealthCheckEvent.__table__.insert().values(**values)
            )
        return inserted.inserted_primary_key[0] if inserted.inserted_primary_key else None
    except Exception:
        return None

