from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from database import db
from database.crud import (
    bulk_update_chats,
    create_chat_folder,
    create_chat_tag,
    delete_chat_folder,
    delete_chat_tag,
    get_chat_by_id,
    get_chat_folder_by_id,
    get_chat_folders,
    get_chat_tag_by_id,
    get_chat_tags,
    update_chat_folder,
    update_chat_tag,
)
from services.api_utils import error_response
from services.deletion_service import delete_chat_with_files


organization_routes = Blueprint("organization_routes", __name__)


ALLOWED_TAG_COLORS = {
    "violet",
    "blue",
    "cyan",
    "green",
    "amber",
    "rose",
}


def folder_to_dict(folder):
    return {
        "id": folder.id,
        "name": folder.name,
        "chat_count": len(folder.chats),
        "created_at": folder.created_at.isoformat() if folder.created_at else None,
        "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
    }


def tag_to_dict(tag):
    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "chat_count": len(tag.chats),
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
        "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
    }


def normalize_name(value, maximum, label):
    name = " ".join(str(value or "").split())
    if not name:
        raise ValueError(f"{label} name cannot be empty.")
    if len(name) > maximum:
        raise ValueError(f"{label} name cannot exceed {maximum} characters.")
    return name


@organization_routes.route("/api/chat-folders", methods=["GET"])
def list_chat_folders():
    return [folder_to_dict(folder) for folder in get_chat_folders()]


@organization_routes.route("/api/chat-folders", methods=["POST"])
def add_chat_folder():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json_body")
    try:
        name = normalize_name(data.get("name"), 120, "Folder")
        folder = create_chat_folder(name)
        return folder_to_dict(folder), 201
    except ValueError as error:
        return error_response(str(error), 400, "invalid_folder_name")
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A folder with this name already exists.",
            409,
            "chat_folder_exists",
        )


@organization_routes.route("/api/chat-folders/<int:folder_id>", methods=["PATCH"])
def edit_chat_folder(folder_id):
    if not get_chat_folder_by_id(folder_id):
        return error_response("Chat folder not found.", 404, "chat_folder_not_found")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json_body")
    try:
        name = normalize_name(data.get("name"), 120, "Folder")
        folder = update_chat_folder(folder_id, name)
        return folder_to_dict(folder)
    except ValueError as error:
        return error_response(str(error), 400, "invalid_folder_name")
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A folder with this name already exists.",
            409,
            "chat_folder_exists",
        )


@organization_routes.route("/api/chat-folders/<int:folder_id>", methods=["DELETE"])
def remove_chat_folder(folder_id):
    if not delete_chat_folder(folder_id):
        return error_response("Chat folder not found.", 404, "chat_folder_not_found")
    return {"success": True}


@organization_routes.route("/api/chat-tags", methods=["GET"])
def list_chat_tags():
    return [tag_to_dict(tag) for tag in get_chat_tags()]


@organization_routes.route("/api/chat-tags", methods=["POST"])
def add_chat_tag():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json_body")
    try:
        name = normalize_name(data.get("name"), 80, "Tag")
        color = str(data.get("color") or "violet").strip().lower()
        if color not in ALLOWED_TAG_COLORS:
            return error_response("Unsupported tag color.", 400, "invalid_tag_color")
        tag = create_chat_tag(name, color)
        return tag_to_dict(tag), 201
    except ValueError as error:
        return error_response(str(error), 400, "invalid_tag_name")
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A tag with this name already exists.",
            409,
            "chat_tag_exists",
        )


@organization_routes.route("/api/chat-tags/<int:tag_id>", methods=["PATCH"])
def edit_chat_tag(tag_id):
    if not get_chat_tag_by_id(tag_id):
        return error_response("Chat tag not found.", 404, "chat_tag_not_found")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json_body")
    try:
        name = None
        if "name" in data:
            name = normalize_name(data.get("name"), 80, "Tag")
        color = None
        if "color" in data:
            color = str(data.get("color") or "").strip().lower()
            if color not in ALLOWED_TAG_COLORS:
                return error_response("Unsupported tag color.", 400, "invalid_tag_color")
        tag = update_chat_tag(tag_id, name=name, color=color)
        return tag_to_dict(tag)
    except ValueError as error:
        return error_response(str(error), 400, "invalid_tag_name")
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A tag with this name already exists.",
            409,
            "chat_tag_exists",
        )


@organization_routes.route("/api/chat-tags/<int:tag_id>", methods=["DELETE"])
def remove_chat_tag(tag_id):
    if not delete_chat_tag(tag_id):
        return error_response("Chat tag not found.", 404, "chat_tag_not_found")
    return {"success": True}


@organization_routes.route("/api/chats/bulk", methods=["POST"])
def bulk_chat_action():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json_body")

    chat_ids = data.get("chat_ids")
    action = str(data.get("action") or "").strip().lower()
    if not isinstance(chat_ids, list) or not chat_ids:
        return error_response("Select at least one chat.", 400, "chat_selection_required")
    try:
        normalized_ids = sorted({int(value) for value in chat_ids})
    except (TypeError, ValueError):
        return error_response("chat_ids must contain integers.", 400, "invalid_chat_ids")
    if len(normalized_ids) > 250:
        return error_response("No more than 250 chats can be changed at once.", 400, "bulk_limit_exceeded")

    if action == "delete":
        chats = [get_chat_by_id(chat_id) for chat_id in normalized_ids]
        if any(chat is None for chat in chats):
            return error_response("One or more chats were not found.", 404, "chat_not_found")
        for chat in chats:
            delete_chat_with_files(chat)
        return {"success": True, "affected": len(chats)}

    try:
        chats = bulk_update_chats(
            normalized_ids,
            action,
            folder_id=data.get("folder_id"),
            tag_id=data.get("tag_id"),
        )
    except (TypeError, ValueError) as error:
        return error_response(str(error), 400, "invalid_bulk_action")

    return {"success": True, "affected": len(chats)}
