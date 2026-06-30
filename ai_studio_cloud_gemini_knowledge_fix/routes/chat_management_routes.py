from flask import (
    Blueprint,
    current_app,
    request
)

from database.crud import (
    create_chat,
    create_message,
    get_all_chats,
    get_chat_by_id,
    get_messages_by_chat_id,
    update_chat_pin,
    update_chat_title,
    update_chat_organization
)

from services.api_utils import (
    error_response
)

from services.deletion_service import (
    delete_chat_with_files
)


chat_management_routes = Blueprint(
    "chat_management_routes",
    __name__
)


def chat_to_dict(chat):
    return {
        "id": chat.id,
        "title": chat.title,
        "is_pinned": chat.is_pinned,
        "is_favorite": chat.is_favorite,
        "is_archived": chat.is_archived,
        "parent_chat_id": chat.parent_chat_id,
        "branched_from_message_id": chat.branched_from_message_id,
        "branch_count": len(chat.branches),
        "folder": (
            {
                "id": chat.folder.id,
                "name": chat.folder.name,
            }
            if chat.folder
            else None
        ),
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
            }
            for tag in sorted(chat.tags, key=lambda item: item.name.casefold())
        ],
        "created_at": (
            chat.created_at.isoformat()
            if chat.created_at
            else None
        ),
        "updated_at": (
            chat.updated_at.isoformat()
            if chat.updated_at
            else None
        )
    }


def attachment_to_dict(attachment):
    return {
        "id": attachment.id,
        "original_filename": attachment.original_filename,
        "file_type": attachment.file_type,
        "mime_type": attachment.mime_type,
        "file_size": attachment.file_size,
        "attachment_kind": attachment.attachment_kind,
        "status": attachment.status,
        "chunk_count": attachment.chunk_count,
        "extraction_method": attachment.extraction_method,
        "preview_url": (
            f"/api/attachments/{attachment.id}/preview"
            if attachment.attachment_kind == "image"
            and attachment.status == "ready"
            else None
        )
    }


def message_to_dict(message):
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "role": message.role,
        "content": message.content,
        "model": message.model,
        "mode": message.mode,
        "attachments": [
            attachment_to_dict(attachment)
            for attachment in message.attachments
        ],
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        )
    }


@chat_management_routes.route(
    "/api/chats",
    methods=["POST"]
)
def create_new_chat():
    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get(
            "title",
            "New Chat"
        )
    ).strip()

    if not title:
        title = "New Chat"

    title = title[:255]

    folder_id = data.get("folder_id")
    if folder_id is not None:
        try:
            folder_id = int(folder_id)
        except (TypeError, ValueError):
            return error_response(
                "folder_id must be an integer or null.",
                400,
                "invalid_folder_id"
            )

    try:
        chat = create_chat(
            title=title,
            folder_id=folder_id
        )
    except ValueError as error:
        return error_response(
            str(error),
            400,
            "invalid_folder_id"
        )

    return chat_to_dict(
        chat
    ), 201


@chat_management_routes.route(
    "/api/chats",
    methods=["GET"]
)
def list_chats():
    view = str(request.args.get("view") or "active").strip().lower()
    include_archived = view == "all"
    archived_only = view == "archived"
    favorites_only = view == "favorites"

    folder_id = request.args.get("folder_id")
    tag_id = request.args.get("tag_id")

    try:
        folder_id = int(folder_id) if folder_id not in {None, ""} else None
        tag_id = int(tag_id) if tag_id not in {None, ""} else None
    except (TypeError, ValueError):
        return error_response(
            "folder_id and tag_id must be integers.",
            400,
            "invalid_chat_filter"
        )

    chats = get_all_chats(
        include_archived=include_archived,
        archived_only=archived_only,
        favorites_only=favorites_only,
        folder_id=folder_id,
        tag_id=tag_id,
        search=request.args.get("search"),
    )

    return [chat_to_dict(chat) for chat in chats]


@chat_management_routes.route(
    "/api/chats/<int:chat_id>",
    methods=["PATCH"]
)
def update_chat(chat_id):
    chat = get_chat_by_id(
        chat_id
    )

    if not chat:
        return error_response(
            "Chat not found.",
            404,
            "chat_not_found"
        )

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json"
        )

    changed = False

    if "title" in data:
        title = str(
            data.get(
                "title",
                ""
            )
        ).strip()

        if not title:
            return error_response(
                "Chat title cannot be empty.",
                400,
                "invalid_chat_title"
            )

        if len(title) > 255:
            return error_response(
                "Chat title cannot exceed 255 characters.",
                400,
                "invalid_chat_title"
            )

        chat = update_chat_title(
            chat_id,
            title
        )

        changed = True

    if "is_pinned" in data:
        is_pinned = data.get(
            "is_pinned"
        )

        if not isinstance(
            is_pinned,
            bool
        ):
            return error_response(
                "is_pinned must be true or false.",
                400,
                "invalid_pin_value"
            )

        chat = update_chat_pin(
            chat_id,
            is_pinned
        )

        changed = True

    organization_fields = {
        "folder_id",
        "is_favorite",
        "is_archived",
        "tag_ids",
    }

    if organization_fields.intersection(data):
        is_favorite = data.get("is_favorite")
        is_archived = data.get("is_archived")
        tag_ids = data.get("tag_ids") if "tag_ids" in data else None

        if is_favorite is not None and not isinstance(is_favorite, bool):
            return error_response(
                "is_favorite must be true or false.",
                400,
                "invalid_favorite_value"
            )

        if is_archived is not None and not isinstance(is_archived, bool):
            return error_response(
                "is_archived must be true or false.",
                400,
                "invalid_archive_value"
            )

        if tag_ids is not None and not isinstance(tag_ids, list):
            return error_response(
                "tag_ids must be a list.",
                400,
                "invalid_tag_ids"
            )

        folder_id = data.get("folder_id")
        if "folder_id" in data and folder_id is not None:
            try:
                folder_id = int(folder_id)
            except (TypeError, ValueError):
                return error_response(
                    "folder_id must be an integer or null.",
                    400,
                    "invalid_folder_id"
                )

        try:
            chat = update_chat_organization(
                chat_id,
                folder_id=folder_id,
                folder_provided="folder_id" in data,
                is_favorite=is_favorite,
                is_archived=is_archived,
                tag_ids=tag_ids,
            )
        except (TypeError, ValueError) as error:
            return error_response(
                str(error),
                400,
                "invalid_chat_organization"
            )

        changed = True

    if not changed:
        return error_response(
            (
                "Provide title, pin, favorite, archive, folder, or tags to update."
            ),
            400,
            "no_update_fields"
        )

    return chat_to_dict(
        chat
    )


@chat_management_routes.route(
    "/api/chats/<int:chat_id>",
    methods=["DELETE"]
)
def remove_chat(chat_id):
    chat = get_chat_by_id(
        chat_id
    )

    if not chat:
        return error_response(
            "Chat not found.",
            404,
            "chat_not_found"
        )

    delete_chat_with_files(
        chat
    )

    return {
        "success": True
    }


@chat_management_routes.route(
    "/api/chats/<int:chat_id>/messages",
    methods=["POST"]
)
def save_chat_message(chat_id):
    chat = get_chat_by_id(
        chat_id
    )

    if not chat:
        return error_response(
            "Chat not found.",
            404,
            "chat_not_found"
        )

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):
        return error_response(
            "A JSON object is required.",
            400,
            "invalid_json"
        )

    role = str(
        data.get(
            "role",
            ""
        )
    ).strip().lower()

    if role not in {
        "user",
        "bot",
        "assistant"
    }:
        return error_response(
            (
                "Message role must be "
                "user, bot, or assistant."
            ),
            400,
            "invalid_message_role"
        )

    content = str(
        data.get(
            "content",
            ""
        )
    ).strip()

    if not content:
        return error_response(
            "Message content cannot be empty.",
            400,
            "empty_message"
        )

    if len(content) > 1_000_000:
        return error_response(
            "Message content is too large.",
            413,
            "message_too_large"
        )

    model = data.get(
        "model"
    )

    mode = data.get(
        "mode"
    )

    attachment_ids = data.get("attachment_ids", [])

    if not isinstance(attachment_ids, list):
        return error_response(
            "attachment_ids must be a list.",
            400,
            "invalid_attachment_ids"
        )

    maximum_attachments = int(
        current_app.config.get("ATTACHMENT_MAX_FILES", 5)
    )

    if len(attachment_ids) > maximum_attachments:
        return error_response(
            f"No more than {maximum_attachments} attachments can be saved with one message.",
            400,
            "too_many_attachments"
        )

    if attachment_ids and role != "user":
        return error_response(
            "Only user messages can contain attachments.",
            400,
            "attachments_require_user_message"
        )

    normalized_attachment_ids = []
    try:
        for attachment_id in attachment_ids:
            parsed_id = int(attachment_id)
            if parsed_id <= 0:
                raise ValueError
            if parsed_id not in normalized_attachment_ids:
                normalized_attachment_ids.append(parsed_id)
    except (TypeError, ValueError):
        return error_response(
            "Every attachment ID must be a positive integer.",
            400,
            "invalid_attachment_ids"
        )

    try:
        message = create_message(
            chat_id=chat_id,
            role=role,
            content=content,
            model=(
                str(model)[:100]
                if model is not None
                else None
            ),
            mode=(
                str(mode)[:50]
                if mode is not None
                else None
            ),
            attachment_ids=normalized_attachment_ids
        )
    except ValueError as error:
        return error_response(
            str(error),
            400,
            "invalid_message_attachments"
        )

    return message_to_dict(
        message
    ), 201


@chat_management_routes.route(
    "/api/chats/<int:chat_id>/messages",
    methods=["GET"]
)
def get_chat_messages(chat_id):
    chat = get_chat_by_id(
        chat_id
    )

    if not chat:
        return error_response(
            "Chat not found.",
            404,
            "chat_not_found"
        )

    return [
        message_to_dict(message)
        for message in (
            get_messages_by_chat_id(
                chat_id
            )
        )
    ]
