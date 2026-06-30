from flask import (
    Blueprint,
    Response
)

from werkzeug.utils import (
    secure_filename
)

from database.crud import (
    get_chat_by_id,
    get_messages_by_chat_id
)

from services.api_utils import (
    error_response
)


export_routes = Blueprint(
    "export_routes",
    __name__
)


@export_routes.route(
    "/api/chats/<int:chat_id>/export/<file_type>"
)
def export_chat(
    chat_id,
    file_type
):
    if file_type not in {
        "txt",
        "md"
    }:
        return error_response(
            "Export type must be txt or md.",
            400,
            "invalid_export_type"
        )

    chat = get_chat_by_id(
        chat_id
    )

    if not chat:
        return error_response(
            "Chat not found.",
            404,
            "chat_not_found"
        )

    messages = get_messages_by_chat_id(
        chat_id
    )

    content = (
        f"# {chat.title}\n\n"
    )

    for message in messages:
        role = (
            "User"
            if message.role == "user"
            else "AI"
        )

        content += f"## {role}\n\n"

        if message.attachments:
            attachment_names = ", ".join(
                attachment.original_filename
                for attachment in message.attachments
            )
            content += f"Attachments: {attachment_names}\n\n"

        content += f"{message.content}\n\n"

    safe_title = (
        secure_filename(
            chat.title
        )
        or f"chat-{chat.id}"
    )

    if file_type == "md":
        mimetype = "text/markdown"
    else:
        mimetype = "text/plain"

    filename = (
        f"{safe_title}.{file_type}"
    )

    return Response(
        content,
        mimetype=mimetype,
        headers={
            "Content-Disposition": (
                "attachment; "
                f"filename=\"{filename}\""
            )
        }
    )
