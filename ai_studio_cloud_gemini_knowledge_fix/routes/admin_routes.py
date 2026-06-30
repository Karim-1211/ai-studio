from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user

from database import db
from database.models import User, utcnow

from routes.auth_routes import admin_required
from services.audit_service import record_audit
from services.api_utils import error_response
from services.telemetry_service import (
    cleanup_orphan_uploads,
    get_admin_analytics,
    purge_telemetry,
)


admin_routes = Blueprint("admin", __name__)


@admin_routes.route("/admin/dashboard", methods=["GET"])
@admin_required
def dashboard():
    return render_template("admin_dashboard.html")


@admin_routes.route("/api/admin/analytics", methods=["GET"])
@admin_required
def analytics_api():
    try:
        days = int(request.args.get("days", 30))
    except (TypeError, ValueError):
        return error_response("days must be an integer.", 400, "invalid_days")

    data = get_admin_analytics(days=days)
    data["current_user_id"] = int(current_user.id)
    return jsonify(data)


@admin_routes.route("/api/admin/users/<int:user_id>/status", methods=["POST"])
@admin_required
def update_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error_response("User account not found.", 404, "user_not_found")
    if user.id == current_user.id:
        return error_response(
            "You cannot disable your own account.",
            400,
            "cannot_disable_current_user",
        )

    data = request.get_json(silent=True) or {}
    active = data.get("active")
    if not isinstance(active, bool):
        return error_response("active must be true or false.", 400, "invalid_active_value")

    user.active = active
    user.updated_at = utcnow()
    db.session.commit()
    record_audit(
        "admin.user_status_changed",
        target_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        details={"active": bool(user.active), "source": "admin_dashboard"},
    )
    return jsonify({
        "id": user.id,
        "active": bool(user.active),
        "message": "User status updated.",
    })


@admin_routes.route("/api/admin/cleanup/preview", methods=["GET"])
@admin_required
def cleanup_preview():
    result = cleanup_orphan_uploads(delete=False)
    return jsonify(result)


@admin_routes.route("/api/admin/cleanup/orphans", methods=["POST"])
@admin_required
def cleanup_orphans():
    data = request.get_json(silent=True) or {}
    if data.get("confirm") is not True:
        return error_response(
            "Set confirm to true before deleting orphan uploads.",
            400,
            "cleanup_confirmation_required",
        )

    result = cleanup_orphan_uploads(delete=True)
    record_audit(
        "storage.orphan_cleanup",
        entity_type="upload_storage",
        details={
            "removed_count": len(result.get("removed", [])),
            "failure_count": len(result.get("failures", [])),
        },
    )
    return jsonify(result)


@admin_routes.route("/api/admin/telemetry/purge", methods=["POST"])
@admin_required
def purge_telemetry_api():
    data = request.get_json(silent=True) or {}
    try:
        retention_days = int(data.get("retention_days", 90))
    except (TypeError, ValueError):
        return error_response(
            "retention_days must be an integer.",
            400,
            "invalid_retention_days",
        )

    result = purge_telemetry(retention_days)
    record_audit(
        "telemetry.purge",
        entity_type="telemetry",
        details=result,
    )
    return jsonify(result)
