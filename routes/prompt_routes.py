from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from database import db
from database.crud import (
    branch_chat_from_message,
    create_prompt_template,
    delete_prompt_template,
    get_chat_by_id,
    get_prompt_template_by_id,
    list_prompt_templates,
    record_prompt_template_use,
    update_prompt_template,
)
from services.api_utils import error_response


prompt_routes = Blueprint("prompt_routes", __name__)


def prompt_to_dict(template):
    return {
        "id": template.id,
        "title": template.title,
        "content": template.content,
        "category": template.category,
        "is_favorite": bool(template.is_favorite),
        "usage_count": int(template.usage_count or 0),
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


def branch_to_dict(chat):
    return {
        "id": chat.id,
        "title": chat.title,
        "is_pinned": bool(chat.is_pinned),
        "is_favorite": bool(chat.is_favorite),
        "is_archived": bool(chat.is_archived),
        "parent_chat_id": chat.parent_chat_id,
        "branched_from_message_id": chat.branched_from_message_id,
        "folder": (
            {"id": chat.folder.id, "name": chat.folder.name}
            if chat.folder
            else None
        ),
        "tags": [
            {"id": tag.id, "name": tag.name, "color": tag.color}
            for tag in sorted(chat.tags, key=lambda item: item.name.casefold())
        ],
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
    }


def normalize_title(value):
    title = " ".join(str(value or "").split())
    if not title:
        raise ValueError("Prompt title is required.")
    if len(title) > 160:
        raise ValueError("Prompt title cannot exceed 160 characters.")
    return title


def normalize_content(value):
    content = str(value or "").strip()
    if not content:
        raise ValueError("Prompt content is required.")
    if len(content) > 50_000:
        raise ValueError("Prompt content cannot exceed 50,000 characters.")
    return content


def normalize_category(value):
    category = " ".join(str(value or "General").split()) or "General"
    if len(category) > 80:
        raise ValueError("Prompt category cannot exceed 80 characters.")
    return category


@prompt_routes.route("/api/prompt-templates", methods=["GET"])
def list_templates():
    favorites_only = str(request.args.get("favorites") or "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    templates = list_prompt_templates(
        search=request.args.get("search"),
        category=request.args.get("category"),
        favorites_only=favorites_only,
    )
    return [prompt_to_dict(item) for item in templates]


@prompt_routes.route("/api/prompt-templates", methods=["POST"])
def create_template():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json")

    try:
        title = normalize_title(data.get("title"))
        content = normalize_content(data.get("content"))
        category = normalize_category(data.get("category"))
    except ValueError as error:
        return error_response(str(error), 400, "invalid_prompt_template")

    is_favorite = data.get("is_favorite", False)
    if not isinstance(is_favorite, bool):
        return error_response(
            "is_favorite must be true or false.",
            400,
            "invalid_favorite_value",
        )

    try:
        template = create_prompt_template(
            title,
            content,
            category=category,
            is_favorite=is_favorite,
        )
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A prompt with this title already exists.",
            409,
            "prompt_title_exists",
        )

    return prompt_to_dict(template), 201


@prompt_routes.route("/api/prompt-templates/<int:template_id>", methods=["PATCH"])
def update_template(template_id):
    template = get_prompt_template_by_id(template_id)
    if not template:
        return error_response("Prompt template not found.", 404, "prompt_not_found")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json")

    fields = {}
    try:
        if "title" in data:
            fields["title"] = normalize_title(data.get("title"))
        if "content" in data:
            fields["content"] = normalize_content(data.get("content"))
        if "category" in data:
            fields["category"] = normalize_category(data.get("category"))
    except ValueError as error:
        return error_response(str(error), 400, "invalid_prompt_template")

    if "is_favorite" in data:
        if not isinstance(data.get("is_favorite"), bool):
            return error_response(
                "is_favorite must be true or false.",
                400,
                "invalid_favorite_value",
            )
        fields["is_favorite"] = data["is_favorite"]

    if not fields:
        return error_response(
            "Provide a prompt field to update.",
            400,
            "no_update_fields",
        )

    try:
        template = update_prompt_template(template_id, **fields)
    except IntegrityError:
        db.session.rollback()
        return error_response(
            "A prompt with this title already exists.",
            409,
            "prompt_title_exists",
        )

    return prompt_to_dict(template)


@prompt_routes.route("/api/prompt-templates/<int:template_id>", methods=["DELETE"])
def remove_template(template_id):
    if not delete_prompt_template(template_id):
        return error_response("Prompt template not found.", 404, "prompt_not_found")
    return {"success": True}


@prompt_routes.route("/api/prompt-templates/<int:template_id>/use", methods=["POST"])
def use_template(template_id):
    template = record_prompt_template_use(template_id)
    if not template:
        return error_response("Prompt template not found.", 404, "prompt_not_found")
    return prompt_to_dict(template)


@prompt_routes.route("/api/chats/<int:chat_id>/branch", methods=["POST"])
def branch_chat(chat_id):
    source_chat = get_chat_by_id(chat_id)
    if not source_chat:
        return error_response("Chat not found.", 404, "chat_not_found")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("A JSON object is required.", 400, "invalid_json")

    try:
        message_id = int(data.get("message_id"))
        if message_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return error_response(
            "message_id must be a positive integer.",
            400,
            "invalid_message_id",
        )

    include_target = data.get("include_target", True)
    if not isinstance(include_target, bool):
        return error_response(
            "include_target must be true or false.",
            400,
            "invalid_include_target",
        )

    title = str(data.get("title") or "").strip()
    if len(title) > 255:
        return error_response(
            "Branch title cannot exceed 255 characters.",
            400,
            "invalid_branch_title",
        )

    try:
        branch = branch_chat_from_message(
            chat_id,
            message_id,
            title=title or None,
            include_target=include_target,
        )
    except (TypeError, ValueError) as error:
        return error_response(str(error), 400, "branch_failed")

    return branch_to_dict(branch), 201
