import json
import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from flask import current_app

from database import db
from database.models import (
    Chat,
    ChatFolder,
    ChatTag,
    Document,
    DocumentChunk,
    GlobalDocument,
    GlobalDocumentChunk,
    Message,
    MessageAttachment,
    MessageAttachmentChunk,
    PromptTemplate,
    SocialChunk,
    SocialSource,
    WebsiteChunk,
    WebsiteSource,
    user_social_sources,
    user_website_sources,
    utcnow,
)


BACKUP_VERSION = 1


class WorkspaceBackupError(ValueError):
    pass


def _iso(value):
    return value.isoformat() if value else None


def _safe_archive_name(stored_filename):
    name = os.path.basename(str(stored_filename or ""))
    if not name or name in {".", ".."}:
        raise WorkspaceBackupError("A stored upload filename is invalid.")
    return name


def _copy_upload_to_archive(archive, stored_filename, included):
    name = _safe_archive_name(stored_filename)
    if name in included:
        return
    source = Path(current_app.config["UPLOAD_FOLDER"]) / name
    if source.is_file():
        archive.write(source, f"files/{name}")
        included.add(name)


def _chunk_payload(chunks):
    return [
        {
            "chunk_index": item.chunk_index,
            "content": item.content,
            "embedding": item.embedding,
        }
        for item in sorted(chunks, key=lambda item: item.chunk_index)
    ]


def build_workspace_backup(user):
    folders = list(user.chat_folders)
    tags = list(user.chat_tags)

    chats = []
    for chat in sorted(user.chats, key=lambda item: item.created_at):
        chats.append({
            "backup_ref": chat.id,
            "parent_backup_ref": chat.parent_chat_id,
            "branched_from_message_backup_ref": chat.branched_from_message_id,
            "title": chat.title,
            "is_pinned": bool(chat.is_pinned),
            "is_favorite": bool(chat.is_favorite),
            "is_archived": bool(chat.is_archived),
            "folder": chat.folder.name if chat.folder else None,
            "tags": [tag.name for tag in chat.tags],
            "created_at": _iso(chat.created_at),
            "updated_at": _iso(chat.updated_at),
            "messages": [
                {
                    "backup_ref": message.id,
                    "role": message.role,
                    "content": message.content,
                    "model": message.model,
                    "mode": message.mode,
                    "created_at": _iso(message.created_at),
                }
                for message in sorted(chat.messages, key=lambda item: item.created_at)
            ],
            "documents": [
                {
                    "original_filename": item.original_filename,
                    "stored_filename": item.stored_filename,
                    "file_type": item.file_type,
                    "file_size": item.file_size,
                    "status": item.status,
                    "error_message": item.error_message,
                    "chunk_count": item.chunk_count,
                    "text_length": item.text_length,
                    "created_at": _iso(item.created_at),
                    "updated_at": _iso(item.updated_at),
                    "chunks": _chunk_payload(item.chunks),
                }
                for item in chat.documents
            ],
            "attachments": [
                {
                    "message_index": (
                        sorted(chat.messages, key=lambda item: item.created_at).index(item.message)
                        if item.message in chat.messages
                        else None
                    ),
                    "original_filename": item.original_filename,
                    "stored_filename": item.stored_filename,
                    "file_type": item.file_type,
                    "mime_type": item.mime_type,
                    "file_size": item.file_size,
                    "attachment_kind": item.attachment_kind,
                    "status": item.status,
                    "error_message": item.error_message,
                    "chunk_count": item.chunk_count,
                    "text_length": item.text_length,
                    "extraction_method": item.extraction_method,
                    "page_count": item.page_count,
                    "created_at": _iso(item.created_at),
                    "updated_at": _iso(item.updated_at),
                    "chunks": _chunk_payload(item.chunks),
                }
                for item in chat.attachments
            ],
        })

    manifest = {
        "format": "ai-studio-workspace",
        "version": BACKUP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner": {
            "email": user.email,
            "display_name": user.display_name,
        },
        "folders": [
            {"name": item.name, "created_at": _iso(item.created_at)}
            for item in sorted(folders, key=lambda item: item.name.casefold())
        ],
        "tags": [
            {
                "name": item.name,
                "color": item.color,
                "created_at": _iso(item.created_at),
            }
            for item in sorted(tags, key=lambda item: item.name.casefold())
        ],
        "prompt_templates": [
            {
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "is_favorite": bool(item.is_favorite),
                "usage_count": int(item.usage_count or 0),
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
            }
            for item in sorted(
                user.prompt_templates,
                key=lambda item: item.title.casefold(),
            )
        ],
        "chats": chats,
        "global_documents": [
            {
                "original_filename": item.original_filename,
                "stored_filename": item.stored_filename,
                "file_type": item.file_type,
                "file_size": item.file_size,
                "status": item.status,
                "error_message": item.error_message,
                "chunk_count": item.chunk_count,
                "text_length": item.text_length,
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
                "chunks": _chunk_payload(item.chunks),
            }
            for item in user.global_documents
        ],
        "website_sources": [
            {
                "url": item.url,
                "canonical_url": item.canonical_url,
                "title": item.title,
                "domain": item.domain,
                "status": item.status,
                "error_message": item.error_message,
                "chunk_count": item.chunk_count,
                "text_length": item.text_length,
                "http_status": item.http_status,
                "content_type": item.content_type,
                "fetched_at": _iso(item.fetched_at),
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
                "chunks": _chunk_payload(item.chunks),
            }
            for item in user.website_sources
        ],
        "social_sources": [
            {
                "url": item.url,
                "canonical_url": item.canonical_url,
                "title": item.title,
                "platform": item.platform,
                "domain": item.domain,
                "extraction_method": item.extraction_method,
                "status": item.status,
                "error_message": item.error_message,
                "chunk_count": item.chunk_count,
                "text_length": item.text_length,
                "http_status": item.http_status,
                "content_type": item.content_type,
                "fetched_at": _iso(item.fetched_at),
                "created_at": _iso(item.created_at),
                "updated_at": _iso(item.updated_at),
                "chunks": _chunk_payload(item.chunks),
            }
            for item in user.social_sources
        ],
    }

    temporary = tempfile.NamedTemporaryFile(
        prefix="ai-studio-workspace-",
        suffix=".zip",
        delete=False,
    )
    temporary.close()

    included = set()
    with zipfile.ZipFile(temporary.name, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        for chat in user.chats:
            for document in chat.documents:
                _copy_upload_to_archive(archive, document.stored_filename, included)
            for attachment in chat.attachments:
                _copy_upload_to_archive(archive, attachment.stored_filename, included)
        for document in user.global_documents:
            _copy_upload_to_archive(archive, document.stored_filename, included)

    return temporary.name


def _read_manifest(archive):
    try:
        raw = archive.read("manifest.json")
        manifest = json.loads(raw.decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkspaceBackupError("The backup manifest is missing or invalid.") from error

    if manifest.get("format") != "ai-studio-workspace":
        raise WorkspaceBackupError("This file is not an AI Studio workspace backup.")
    if int(manifest.get("version", 0)) != BACKUP_VERSION:
        raise WorkspaceBackupError("This backup version is not supported.")
    return manifest


def _archive_member_bytes(archive, stored_filename):
    name = _safe_archive_name(stored_filename)
    member_name = f"files/{name}"
    try:
        return archive.read(member_name)
    except KeyError:
        return None


def _write_restored_file(data, original_stored_name, created_files):
    if data is None:
        return None
    suffix = Path(original_stored_name).suffix.lower()
    new_name = f"{uuid.uuid4().hex}{suffix}"
    target = Path(current_app.config["UPLOAD_FOLDER"]) / new_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    created_files.append(target)
    return new_name


def _restore_chunks(model, foreign_key_name, parent_id, chunks):
    records = []
    for index, item in enumerate(chunks or []):
        values = {
            foreign_key_name: parent_id,
            "chunk_index": int(item.get("chunk_index", index)),
            "content": str(item.get("content") or ""),
            "embedding": item.get("embedding") or [],
        }
        records.append(model(**values))
    db.session.add_all(records)
    return len(records)


def _attach_website_to_user(source, user_id):
    exists = db.session.execute(
        db.select(user_website_sources).where(
            user_website_sources.c.user_id == user_id,
            user_website_sources.c.website_source_id == source.id,
        )
    ).first()
    if not exists:
        db.session.execute(user_website_sources.insert().values(
            user_id=user_id,
            website_source_id=source.id,
            created_at=utcnow(),
        ))


def _attach_social_to_user(source, user_id):
    exists = db.session.execute(
        db.select(user_social_sources).where(
            user_social_sources.c.user_id == user_id,
            user_social_sources.c.social_source_id == source.id,
        )
    ).first()
    if not exists:
        db.session.execute(user_social_sources.insert().values(
            user_id=user_id,
            social_source_id=source.id,
            created_at=utcnow(),
        ))


def restore_workspace_backup(user, file_storage):
    if not file_storage or not file_storage.filename:
        raise WorkspaceBackupError("Choose an AI Studio backup ZIP file.")

    created_files = []
    summary = {
        "folders": 0,
        "tags": 0,
        "prompt_templates": 0,
        "chats": 0,
        "messages": 0,
        "documents": 0,
        "attachments": 0,
        "global_documents": 0,
        "website_sources": 0,
        "social_sources": 0,
    }

    try:
        with zipfile.ZipFile(file_storage.stream) as archive:
            members = archive.infolist()
            maximum_members = int(
                current_app.config.get("WORKSPACE_BACKUP_MAX_MEMBERS", 5000)
            )
            maximum_uncompressed = int(
                current_app.config.get(
                    "WORKSPACE_BACKUP_MAX_UNCOMPRESSED_BYTES",
                    1_000_000_000,
                )
            )

            if len(members) > maximum_members:
                raise WorkspaceBackupError(
                    "The backup contains too many files."
                )

            total_uncompressed = sum(
                max(0, int(member.file_size or 0))
                for member in members
            )
            if total_uncompressed > maximum_uncompressed:
                raise WorkspaceBackupError(
                    "The uncompressed backup is too large."
                )

            for member in members:
                path = PurePosixPath(member.filename.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    raise WorkspaceBackupError("The backup contains an unsafe path.")

            manifest = _read_manifest(archive)

            folder_map = {
                folder.name.casefold(): folder
                for folder in user.chat_folders
            }
            for item in manifest.get("folders", []):
                name = " ".join(str(item.get("name") or "").split())[:120]
                if not name or name.casefold() in folder_map:
                    continue
                folder = ChatFolder(user_id=user.id, name=name)
                db.session.add(folder)
                db.session.flush()
                folder_map[name.casefold()] = folder
                summary["folders"] += 1

            tag_map = {
                tag.name.casefold(): tag
                for tag in user.chat_tags
            }
            for item in manifest.get("tags", []):
                name = " ".join(str(item.get("name") or "").split())[:80]
                if not name or name.casefold() in tag_map:
                    continue
                tag = ChatTag(
                    user_id=user.id,
                    name=name,
                    color=str(item.get("color") or "violet")[:20],
                )
                db.session.add(tag)
                db.session.flush()
                tag_map[name.casefold()] = tag
                summary["tags"] += 1

            existing_prompt_titles = {
                item.title.casefold()
                for item in user.prompt_templates
            }
            for item in manifest.get("prompt_templates", []):
                title = " ".join(str(item.get("title") or "").split())[:160]
                content = str(item.get("content") or "").strip()[:50_000]
                if not title or not content or title.casefold() in existing_prompt_titles:
                    continue
                template = PromptTemplate(
                    user_id=user.id,
                    title=title,
                    content=content,
                    category=(
                        " ".join(str(item.get("category") or "General").split())[:80]
                        or "General"
                    ),
                    is_favorite=bool(item.get("is_favorite")),
                    usage_count=max(0, int(item.get("usage_count") or 0)),
                )
                db.session.add(template)
                existing_prompt_titles.add(title.casefold())
                summary["prompt_templates"] += 1

            restored_chat_map = {}
            restored_message_map = {}
            pending_branch_links = []

            for chat_item in manifest.get("chats", []):
                folder_name = str(chat_item.get("folder") or "").casefold()
                chat = Chat(
                    user_id=user.id,
                    title=str(chat_item.get("title") or "Restored chat")[:255],
                    folder_id=(folder_map[folder_name].id if folder_name in folder_map else None),
                    is_pinned=bool(chat_item.get("is_pinned")),
                    is_favorite=bool(chat_item.get("is_favorite")),
                    is_archived=bool(chat_item.get("is_archived")),
                )
                chat.tags = [
                    tag_map[name.casefold()]
                    for name in chat_item.get("tags", [])
                    if str(name).casefold() in tag_map
                ]
                db.session.add(chat)
                db.session.flush()
                summary["chats"] += 1

                backup_ref = chat_item.get("backup_ref")
                if backup_ref is not None:
                    restored_chat_map[str(backup_ref)] = chat
                pending_branch_links.append((
                    chat,
                    chat_item.get("parent_backup_ref"),
                    chat_item.get("branched_from_message_backup_ref"),
                ))

                restored_messages = []
                for message_item in chat_item.get("messages", []):
                    message = Message(
                        chat_id=chat.id,
                        role=str(message_item.get("role") or "user")[:50],
                        content=str(message_item.get("content") or ""),
                        model=message_item.get("model"),
                        mode=message_item.get("mode"),
                    )
                    db.session.add(message)
                    db.session.flush()
                    restored_messages.append(message)
                    message_backup_ref = message_item.get("backup_ref")
                    if message_backup_ref is not None:
                        restored_message_map[str(message_backup_ref)] = message
                    summary["messages"] += 1

                for document_item in chat_item.get("documents", []):
                    file_data = _archive_member_bytes(
                        archive,
                        document_item.get("stored_filename"),
                    )
                    stored_name = _write_restored_file(
                        file_data,
                        document_item.get("stored_filename"),
                        created_files,
                    )
                    if not stored_name:
                        continue
                    document = Document(
                        chat_id=chat.id,
                        original_filename=str(document_item.get("original_filename") or "restored-file")[:255],
                        stored_filename=stored_name,
                        file_type=str(document_item.get("file_type") or "txt")[:20],
                        file_size=len(file_data),
                        status=str(document_item.get("status") or "ready")[:30],
                        error_message=document_item.get("error_message"),
                        chunk_count=0,
                        text_length=int(document_item.get("text_length") or 0),
                    )
                    db.session.add(document)
                    db.session.flush()
                    document.chunk_count = _restore_chunks(
                        DocumentChunk,
                        "document_id",
                        document.id,
                        document_item.get("chunks"),
                    )
                    summary["documents"] += 1

                for attachment_item in chat_item.get("attachments", []):
                    file_data = _archive_member_bytes(
                        archive,
                        attachment_item.get("stored_filename"),
                    )
                    stored_name = _write_restored_file(
                        file_data,
                        attachment_item.get("stored_filename"),
                        created_files,
                    )
                    if not stored_name:
                        continue
                    message_index = attachment_item.get("message_index")
                    message_id = None
                    if isinstance(message_index, int) and 0 <= message_index < len(restored_messages):
                        message_id = restored_messages[message_index].id
                    attachment = MessageAttachment(
                        chat_id=chat.id,
                        message_id=message_id,
                        original_filename=str(attachment_item.get("original_filename") or "restored-file")[:255],
                        stored_filename=stored_name,
                        file_type=str(attachment_item.get("file_type") or "txt")[:20],
                        mime_type=attachment_item.get("mime_type"),
                        file_size=len(file_data),
                        attachment_kind=str(attachment_item.get("attachment_kind") or "document")[:30],
                        status=str(attachment_item.get("status") or "ready")[:30],
                        error_message=attachment_item.get("error_message"),
                        chunk_count=0,
                        text_length=int(attachment_item.get("text_length") or 0),
                        extraction_method=attachment_item.get("extraction_method"),
                        page_count=int(attachment_item.get("page_count") or 1),
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    attachment.chunk_count = _restore_chunks(
                        MessageAttachmentChunk,
                        "attachment_id",
                        attachment.id,
                        attachment_item.get("chunks"),
                    )
                    summary["attachments"] += 1

            for chat, parent_ref, message_ref in pending_branch_links:
                if parent_ref is not None:
                    parent = restored_chat_map.get(str(parent_ref))
                    if parent:
                        chat.parent_chat_id = parent.id
                if message_ref is not None:
                    source_message = restored_message_map.get(str(message_ref))
                    if source_message:
                        chat.branched_from_message_id = source_message.id

            for item in manifest.get("global_documents", []):
                file_data = _archive_member_bytes(archive, item.get("stored_filename"))
                stored_name = _write_restored_file(
                    file_data,
                    item.get("stored_filename"),
                    created_files,
                )
                if not stored_name:
                    continue
                document = GlobalDocument(
                    user_id=user.id,
                    original_filename=str(item.get("original_filename") or "restored-file")[:255],
                    stored_filename=stored_name,
                    file_type=str(item.get("file_type") or "txt")[:20],
                    file_size=len(file_data),
                    status=str(item.get("status") or "ready")[:30],
                    error_message=item.get("error_message"),
                    chunk_count=0,
                    text_length=int(item.get("text_length") or 0),
                )
                db.session.add(document)
                db.session.flush()
                document.chunk_count = _restore_chunks(
                    GlobalDocumentChunk,
                    "global_document_id",
                    document.id,
                    item.get("chunks"),
                )
                summary["global_documents"] += 1

            for item in manifest.get("website_sources", []):
                canonical = str(item.get("canonical_url") or item.get("url") or "")
                source = WebsiteSource.query.filter(
                    db.or_(WebsiteSource.canonical_url == canonical, WebsiteSource.url == canonical)
                ).first()
                if not source:
                    source = WebsiteSource(
                        url=str(item.get("url") or canonical)[:2048],
                        canonical_url=canonical[:2048],
                        title=str(item.get("title") or "Restored website")[:500],
                        domain=str(item.get("domain") or "")[:255],
                        status=str(item.get("status") or "ready")[:30],
                        error_message=item.get("error_message"),
                        chunk_count=0,
                        text_length=int(item.get("text_length") or 0),
                        http_status=item.get("http_status"),
                        content_type=item.get("content_type"),
                    )
                    db.session.add(source)
                    db.session.flush()
                    source.chunk_count = _restore_chunks(
                        WebsiteChunk,
                        "website_source_id",
                        source.id,
                        item.get("chunks"),
                    )
                _attach_website_to_user(source, user.id)
                summary["website_sources"] += 1

            for item in manifest.get("social_sources", []):
                canonical = str(item.get("canonical_url") or item.get("url") or "")
                source = SocialSource.query.filter(
                    db.or_(SocialSource.canonical_url == canonical, SocialSource.url == canonical)
                ).first()
                if not source:
                    source = SocialSource(
                        url=str(item.get("url") or canonical)[:2048],
                        canonical_url=canonical[:2048],
                        title=str(item.get("title") or "Restored social source")[:500],
                        platform=str(item.get("platform") or "Social")[:50],
                        domain=str(item.get("domain") or "")[:255],
                        extraction_method=str(item.get("extraction_method") or "manual")[:30],
                        status=str(item.get("status") or "ready")[:30],
                        error_message=item.get("error_message"),
                        chunk_count=0,
                        text_length=int(item.get("text_length") or 0),
                        http_status=item.get("http_status"),
                        content_type=item.get("content_type"),
                    )
                    db.session.add(source)
                    db.session.flush()
                    source.chunk_count = _restore_chunks(
                        SocialChunk,
                        "social_source_id",
                        source.id,
                        item.get("chunks"),
                    )
                _attach_social_to_user(source, user.id)
                summary["social_sources"] += 1

            db.session.commit()
            return summary

    except zipfile.BadZipFile as error:
        db.session.rollback()
        raise WorkspaceBackupError("The selected file is not a valid ZIP backup.") from error
    except Exception:
        db.session.rollback()
        for path in created_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
