import os
from datetime import datetime

from flask import Blueprint, current_app, request, send_file
from flask_login import current_user

from services.api_utils import error_response
from services.audit_service import record_audit
from services.workspace_service import (
    WorkspaceBackupError,
    build_workspace_backup,
    restore_workspace_backup,
)


workspace_routes = Blueprint("workspace_routes", __name__)


@workspace_routes.route("/api/workspace/backup", methods=["GET"])
def download_workspace_backup():
    if not current_user.is_authenticated:
        return error_response(
            "Sign in to download a workspace backup.",
            401,
            "authentication_required",
        )

    backup_path = build_workspace_backup(current_user)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logger = current_app.logger
    response = send_file(
        backup_path,
        as_attachment=True,
        download_name=f"ai-studio-workspace-{stamp}.zip",
        mimetype="application/zip",
        max_age=0,
    )

    def remove_temporary_backup():
        try:
            os.remove(backup_path)
        except OSError:
            logger.warning("temporary_workspace_backup_cleanup_failed")

    response.call_on_close(remove_temporary_backup)
    record_audit(
        "workspace.backup_downloaded",
        target_user_id=current_user.id,
        entity_type="workspace",
        entity_id=current_user.id,
    )
    return response


@workspace_routes.route("/api/workspace/restore", methods=["POST"])
def restore_workspace():
    if not current_user.is_authenticated:
        return error_response(
            "Sign in to restore a workspace backup.",
            401,
            "authentication_required",
        )

    uploaded = request.files.get("backup")
    try:
        summary = restore_workspace_backup(current_user, uploaded)
    except WorkspaceBackupError as error:
        return error_response(str(error), 400, "invalid_workspace_backup")
    except Exception as error:
        current_app.logger.exception("workspace_restore_failed")
        return error_response(
            "The workspace backup could not be restored.",
            500,
            "workspace_restore_failed",
            str(error),
        )

    record_audit(
        "workspace.restored",
        target_user_id=current_user.id,
        entity_type="workspace",
        entity_id=current_user.id,
        details=summary,
    )

    return {
        "message": "Workspace restored successfully.",
        "summary": summary,
    }
