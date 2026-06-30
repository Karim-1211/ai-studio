from sqlalchemy import or_

from flask import current_app, has_app_context, has_request_context
from flask_login import current_user

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
    User,
    WebsiteChunk,
    WebsiteSource,
    user_social_sources,
    user_website_sources,
    utcnow,
)


def _resolve_user_id(user_id=None):
    if user_id is not None:
        return int(user_id)

    if has_request_context() and current_user.is_authenticated:
        return int(current_user.id)

    if has_app_context() and current_app.config.get("AUTH_REQUIRED"):
        raise RuntimeError("An authenticated user is required for this operation.")

    return None


def _chat_query_for_user(user_id=None):
    user_id = _resolve_user_id(user_id)
    query = Chat.query
    if user_id is not None:
        query = query.filter(Chat.user_id == user_id)
    return query


def _global_document_query_for_user(user_id=None):
    user_id = _resolve_user_id(user_id)
    query = GlobalDocument.query
    if user_id is not None:
        query = query.filter(GlobalDocument.user_id == user_id)
    return query


def _website_query_for_user(user_id=None):
    user_id = _resolve_user_id(user_id)
    query = WebsiteSource.query
    if user_id is not None:
        query = query.join(
            user_website_sources,
            user_website_sources.c.website_source_id == WebsiteSource.id,
        ).filter(user_website_sources.c.user_id == user_id)
    return query


def _social_query_for_user(user_id=None):
    user_id = _resolve_user_id(user_id)
    query = SocialSource.query
    if user_id is not None:
        query = query.join(
            user_social_sources,
            user_social_sources.c.social_source_id == SocialSource.id,
        ).filter(user_social_sources.c.user_id == user_id)
    return query


def _prompt_template_query_for_user(user_id=None):
    user_id = _resolve_user_id(user_id)
    query = PromptTemplate.query
    if user_id is not None:
        query = query.filter(PromptTemplate.user_id == user_id)
    return query


# =========================================================
# CHAT CRUD
# =========================================================


def create_chat(title="New Chat", user_id=None, folder_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    if folder_id is not None:
        folder = get_chat_folder_by_id(folder_id, user_id=resolved_user_id)
        if not folder:
            raise ValueError("Chat folder not found.")
        folder_id = folder.id
    chat = Chat(
        title=title,
        user_id=resolved_user_id,
        folder_id=folder_id,
    )
    db.session.add(chat)
    db.session.commit()
    return chat


def get_all_chats(
    user_id=None,
    include_archived=False,
    archived_only=False,
    favorites_only=False,
    folder_id=None,
    tag_id=None,
    search=None,
):
    query = _chat_query_for_user(user_id)

    if archived_only:
        query = query.filter(Chat.is_archived.is_(True))
    elif not include_archived:
        query = query.filter(Chat.is_archived.is_(False))

    if favorites_only:
        query = query.filter(Chat.is_favorite.is_(True))

    if folder_id is not None:
        query = query.filter(Chat.folder_id == folder_id)

    if tag_id is not None:
        query = query.join(Chat.tags).filter(ChatTag.id == tag_id)

    if search:
        query = query.filter(Chat.title.ilike(f"%{str(search).strip()}%"))

    return query.order_by(
        Chat.is_pinned.desc(),
        Chat.is_favorite.desc(),
        Chat.updated_at.desc(),
    ).all()


def get_chat_by_id(chat_id, user_id=None):
    return _chat_query_for_user(user_id).filter(Chat.id == chat_id).first()


def create_message(
    chat_id,
    role,
    content,
    model=None,
    mode=None,
    attachment_ids=None,
    user_id=None,
):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        raise ValueError("Chat not found.")

    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
        model=model,
        mode=mode,
    )
    chat.updated_at = utcnow()
    db.session.add(message)
    db.session.flush()

    if attachment_ids:
        attachments = (
            MessageAttachment.query
            .join(Chat, MessageAttachment.chat_id == Chat.id)
            .filter(
                MessageAttachment.chat_id == chat_id,
                MessageAttachment.id.in_(attachment_ids),
                MessageAttachment.message_id.is_(None),
                MessageAttachment.status == "ready",
                *(
                    [Chat.user_id == chat.user_id]
                    if chat.user_id is not None
                    else []
                ),
            )
            .all()
        )
        found_ids = {item.id for item in attachments}
        missing_ids = set(attachment_ids) - found_ids
        if missing_ids:
            db.session.rollback()
            raise ValueError(
                "One or more attachments are unavailable for this chat."
            )
        for attachment in attachments:
            attachment.message_id = message.id
            attachment.updated_at = utcnow()

    db.session.commit()
    return message


def get_messages_by_chat_id(chat_id, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    return (
        Message.query
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at.asc())
        .all()
    )


def update_chat_title(chat_id, title, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return None
    chat.title = title
    chat.updated_at = utcnow()
    db.session.commit()
    return chat


def update_chat_pin(chat_id, is_pinned, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return None
    chat.is_pinned = bool(is_pinned)
    chat.updated_at = utcnow()
    db.session.commit()
    return chat


def update_chat_organization(
    chat_id,
    folder_id=None,
    folder_provided=False,
    is_favorite=None,
    is_archived=None,
    tag_ids=None,
    user_id=None,
):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return None

    resolved_user_id = _resolve_user_id(user_id)

    if folder_provided:
        if folder_id is None:
            chat.folder_id = None
        else:
            folder = get_chat_folder_by_id(folder_id, user_id=resolved_user_id)
            if not folder:
                raise ValueError("Chat folder not found.")
            chat.folder_id = folder.id

    if is_favorite is not None:
        chat.is_favorite = bool(is_favorite)

    if is_archived is not None:
        chat.is_archived = bool(is_archived)
        if chat.is_archived:
            chat.is_pinned = False

    if tag_ids is not None:
        normalized_ids = sorted({int(value) for value in tag_ids})
        tags = []
        if normalized_ids:
            tags = (
                ChatTag.query
                .filter(
                    ChatTag.user_id == resolved_user_id,
                    ChatTag.id.in_(normalized_ids),
                )
                .all()
            )
            if len(tags) != len(normalized_ids):
                raise ValueError("One or more chat tags were not found.")
        chat.tags = tags

    chat.updated_at = utcnow()
    db.session.commit()
    return chat


def delete_chat(chat_id, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return False
    db.session.delete(chat)
    db.session.commit()
    return True


def branch_chat_from_message(
    chat_id,
    message_id,
    *,
    title=None,
    include_target=True,
    user_id=None,
):
    source_chat = get_chat_by_id(chat_id, user_id=user_id)
    if not source_chat:
        raise ValueError("Chat not found.")

    target_message = (
        Message.query
        .filter(
            Message.chat_id == source_chat.id,
            Message.id == int(message_id),
        )
        .first()
    )
    if not target_message:
        raise ValueError("Message not found in this chat.")

    source_messages = (
        Message.query
        .filter(Message.chat_id == source_chat.id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    target_index = next(
        (
            index
            for index, item in enumerate(source_messages)
            if item.id == target_message.id
        ),
        None,
    )
    if target_index is None:
        raise ValueError("Message not found in this chat.")

    copy_limit = target_index + (1 if include_target else 0)
    default_title = f"Branch: {source_chat.title}"[:255]
    branch_title = str(title or default_title).strip()[:255] or default_title

    branch = Chat(
        user_id=source_chat.user_id,
        title=branch_title,
        folder_id=source_chat.folder_id,
        parent_chat_id=source_chat.id,
        branched_from_message_id=target_message.id,
        is_pinned=False,
        is_favorite=False,
        is_archived=False,
    )
    branch.tags = list(source_chat.tags)
    db.session.add(branch)
    db.session.flush()

    for source_message in source_messages[:copy_limit]:
        db.session.add(
            Message(
                chat_id=branch.id,
                role=source_message.role,
                content=source_message.content,
                model=source_message.model,
                mode=source_message.mode,
                created_at=source_message.created_at,
            )
        )

    db.session.commit()
    return branch


# =========================================================
# PROMPT TEMPLATE CRUD
# =========================================================


def list_prompt_templates(
    *,
    search=None,
    category=None,
    favorites_only=False,
    user_id=None,
):
    query = _prompt_template_query_for_user(user_id)

    if search:
        value = f"%{str(search).strip()}%"
        query = query.filter(
            or_(
                PromptTemplate.title.ilike(value),
                PromptTemplate.content.ilike(value),
                PromptTemplate.category.ilike(value),
            )
        )

    if category:
        query = query.filter(PromptTemplate.category == str(category).strip())

    if favorites_only:
        query = query.filter(PromptTemplate.is_favorite.is_(True))

    return query.order_by(
        PromptTemplate.is_favorite.desc(),
        PromptTemplate.usage_count.desc(),
        PromptTemplate.updated_at.desc(),
    ).all()


def get_prompt_template_by_id(template_id, user_id=None):
    return (
        _prompt_template_query_for_user(user_id)
        .filter(PromptTemplate.id == int(template_id))
        .first()
    )


def create_prompt_template(
    title,
    content,
    *,
    category="General",
    is_favorite=False,
    user_id=None,
):
    resolved_user_id = _resolve_user_id(user_id)
    template = PromptTemplate(
        user_id=resolved_user_id,
        title=str(title).strip(),
        content=str(content).strip(),
        category=str(category or "General").strip() or "General",
        is_favorite=bool(is_favorite),
    )
    db.session.add(template)
    db.session.commit()
    return template


def update_prompt_template(
    template_id,
    *,
    title=None,
    content=None,
    category=None,
    is_favorite=None,
    user_id=None,
):
    template = get_prompt_template_by_id(template_id, user_id=user_id)
    if not template:
        return None

    if title is not None:
        template.title = str(title).strip()
    if content is not None:
        template.content = str(content).strip()
    if category is not None:
        template.category = str(category).strip() or "General"
    if is_favorite is not None:
        template.is_favorite = bool(is_favorite)

    template.updated_at = utcnow()
    db.session.commit()
    return template


def record_prompt_template_use(template_id, user_id=None):
    template = get_prompt_template_by_id(template_id, user_id=user_id)
    if not template:
        return None
    template.usage_count = int(template.usage_count or 0) + 1
    template.updated_at = utcnow()
    db.session.commit()
    return template


def delete_prompt_template(template_id, user_id=None):
    template = get_prompt_template_by_id(template_id, user_id=user_id)
    if not template:
        return False
    db.session.delete(template)
    db.session.commit()
    return True


# =========================================================
# CHAT DOCUMENT CRUD
# =========================================================


def create_document(
    chat_id,
    original_filename,
    stored_filename,
    file_type,
    file_size,
    user_id=None,
):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        raise ValueError("Chat not found.")
    document = Document(
        chat_id=chat.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_size=file_size,
        status="processing",
    )
    db.session.add(document)
    db.session.commit()
    return document


def get_document_by_id(document_id, user_id=None):
    user_id = _resolve_user_id(user_id)
    query = Document.query.join(Chat, Document.chat_id == Chat.id).filter(
        Document.id == document_id
    )
    if user_id is not None:
        query = query.filter(Chat.user_id == user_id)
    return query.first()


def get_documents_by_chat_id(chat_id, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    return (
        Document.query
        .filter(Document.chat_id == chat.id)
        .order_by(Document.created_at.desc())
        .all()
    )


def update_document_status(
    document_id,
    status,
    error_message=None,
    chunk_count=None,
    text_length=None,
    user_id=None,
):
    document = get_document_by_id(document_id, user_id=user_id)
    if not document:
        return None
    document.status = status
    document.error_message = error_message
    document.updated_at = utcnow()
    if chunk_count is not None:
        document.chunk_count = chunk_count
    if text_length is not None:
        document.text_length = text_length
    db.session.commit()
    return document


def create_document_chunks(document_id, chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    records = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db.session.add_all(records)
    db.session.commit()
    return records


def get_ready_chunks_by_chat_id(chat_id, document_ids=None, user_id=None):
    if document_ids == []:
        return []
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    query = (
        DocumentChunk.query
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(
            Document.chat_id == chat.id,
            Document.status == "ready",
        )
    )
    if document_ids is not None:
        query = query.filter(Document.id.in_(document_ids))
    return query.all()


def delete_document(document_id, user_id=None):
    document = get_document_by_id(document_id, user_id=user_id)
    if not document:
        return False
    db.session.delete(document)
    db.session.commit()
    return True


# =========================================================
# GLOBAL KNOWLEDGE CRUD
# =========================================================


def create_global_document(
    original_filename,
    stored_filename,
    file_type,
    file_size,
    user_id=None,
):
    document = GlobalDocument(
        user_id=_resolve_user_id(user_id),
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_size=file_size,
        status="processing",
    )
    db.session.add(document)
    db.session.commit()
    return document


def get_global_document_by_id(document_id, user_id=None):
    return _global_document_query_for_user(user_id).filter(
        GlobalDocument.id == document_id
    ).first()


def get_all_global_documents(user_id=None):
    return _global_document_query_for_user(user_id).order_by(
        GlobalDocument.created_at.desc()
    ).all()


def update_global_document_status(
    document_id,
    status,
    error_message=None,
    chunk_count=None,
    text_length=None,
    user_id=None,
):
    document = get_global_document_by_id(document_id, user_id=user_id)
    if not document:
        return None
    document.status = status
    document.error_message = error_message
    document.updated_at = utcnow()
    if chunk_count is not None:
        document.chunk_count = chunk_count
    if text_length is not None:
        document.text_length = text_length
    db.session.commit()
    return document


def create_global_document_chunks(global_document_id, chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    records = [
        GlobalDocumentChunk(
            global_document_id=global_document_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db.session.add_all(records)
    db.session.commit()
    return records


def get_ready_global_chunks(global_document_ids=None, user_id=None):
    if global_document_ids == []:
        return []
    user_id = _resolve_user_id(user_id)
    query = (
        GlobalDocumentChunk.query
        .join(
            GlobalDocument,
            GlobalDocumentChunk.global_document_id == GlobalDocument.id,
        )
        .filter(GlobalDocument.status == "ready")
    )
    if user_id is not None:
        query = query.filter(GlobalDocument.user_id == user_id)
    if global_document_ids is not None:
        query = query.filter(GlobalDocument.id.in_(global_document_ids))
    return query.all()


def delete_global_document(document_id, user_id=None):
    document = get_global_document_by_id(document_id, user_id=user_id)
    if not document:
        return False
    db.session.delete(document)
    db.session.commit()
    return True


# =========================================================
# WEBSITE KNOWLEDGE CRUD
# =========================================================


def add_website_source_to_user(source, user_id=None):
    user_id = _resolve_user_id(user_id)
    if user_id is None:
        return source
    membership = db.session.execute(
        db.select(user_website_sources).where(
            user_website_sources.c.user_id == user_id,
            user_website_sources.c.website_source_id == source.id,
        )
    ).first()
    if not membership:
        db.session.execute(
            user_website_sources.insert().values(
                user_id=user_id,
                website_source_id=source.id,
                created_at=utcnow(),
            )
        )
        db.session.commit()
    return source


def get_shared_website_source_by_url(url):
    return WebsiteSource.query.filter(
        db.or_(
            WebsiteSource.url == url,
            WebsiteSource.canonical_url == url,
        )
    ).first()


def create_website_source(
    url,
    canonical_url,
    title,
    domain,
    status="processing",
    http_status=None,
    content_type=None,
    fetched_at=None,
    user_id=None,
):
    source = WebsiteSource(
        url=url,
        canonical_url=canonical_url,
        title=title,
        domain=domain,
        status=status,
        http_status=http_status,
        content_type=content_type,
        fetched_at=fetched_at,
    )
    db.session.add(source)
    db.session.flush()
    resolved_user_id = _resolve_user_id(user_id)
    if resolved_user_id is not None:
        db.session.execute(
            user_website_sources.insert().values(
                user_id=resolved_user_id,
                website_source_id=source.id,
                created_at=utcnow(),
            )
        )
    db.session.commit()
    return source


def get_website_source_by_id(website_source_id, user_id=None):
    return _website_query_for_user(user_id).filter(
        WebsiteSource.id == website_source_id
    ).first()


def get_website_source_by_url(url, user_id=None):
    return _website_query_for_user(user_id).filter(
        db.or_(
            WebsiteSource.url == url,
            WebsiteSource.canonical_url == url,
        )
    ).first()


def get_all_website_sources(user_id=None):
    return _website_query_for_user(user_id).order_by(
        WebsiteSource.created_at.desc()
    ).all()


def update_website_source_status(
    website_source_id,
    status,
    error_message=None,
    chunk_count=None,
    text_length=None,
    title=None,
    canonical_url=None,
    domain=None,
    http_status=None,
    content_type=None,
    fetched_at=None,
    user_id=None,
):
    source = get_website_source_by_id(website_source_id, user_id=user_id)
    if not source:
        return None
    source.status = status
    source.error_message = error_message
    source.updated_at = utcnow()
    for attribute, value in {
        "chunk_count": chunk_count,
        "text_length": text_length,
        "title": title,
        "canonical_url": canonical_url,
        "domain": domain,
        "http_status": http_status,
        "content_type": content_type,
        "fetched_at": fetched_at,
    }.items():
        if value is not None:
            setattr(source, attribute, value)
    db.session.commit()
    return source


def create_website_source_chunks(website_source_id, chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    records = [
        WebsiteChunk(
            website_source_id=website_source_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db.session.add_all(records)
    db.session.commit()
    return records


def replace_website_source_content(
    website_source_id,
    chunks,
    embeddings,
    title,
    canonical_url,
    domain,
    text_length,
    http_status,
    content_type,
    fetched_at,
    user_id=None,
):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    source = get_website_source_by_id(website_source_id, user_id=user_id)
    if not source:
        return None
    try:
        WebsiteChunk.query.filter_by(
            website_source_id=website_source_id
        ).delete(synchronize_session=False)
        db.session.add_all([
            WebsiteChunk(
                website_source_id=website_source_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
            for index, (content, embedding) in enumerate(zip(chunks, embeddings))
        ])
        source.title = title
        source.canonical_url = canonical_url
        source.domain = domain
        source.status = "ready"
        source.error_message = None
        source.chunk_count = len(chunks)
        source.text_length = text_length
        source.http_status = http_status
        source.content_type = content_type
        source.fetched_at = fetched_at
        source.updated_at = utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return source


def get_ready_website_chunks(website_source_ids=None, user_id=None):
    if website_source_ids == []:
        return []
    user_id = _resolve_user_id(user_id)
    query = (
        WebsiteChunk.query
        .join(WebsiteSource, WebsiteChunk.website_source_id == WebsiteSource.id)
        .filter(WebsiteSource.status == "ready")
    )
    if user_id is not None:
        query = query.join(
            user_website_sources,
            user_website_sources.c.website_source_id == WebsiteSource.id,
        ).filter(user_website_sources.c.user_id == user_id)
    if website_source_ids is not None:
        query = query.filter(WebsiteSource.id.in_(website_source_ids))
    return query.all()


def delete_website_source(website_source_id, user_id=None):
    user_id = _resolve_user_id(user_id)
    source = get_website_source_by_id(website_source_id, user_id=user_id)
    if not source:
        return False
    if user_id is None:
        db.session.delete(source)
    else:
        db.session.execute(
            user_website_sources.delete().where(
                user_website_sources.c.user_id == user_id,
                user_website_sources.c.website_source_id == source.id,
            )
        )
        remaining = db.session.execute(
            db.select(user_website_sources.c.user_id).where(
                user_website_sources.c.website_source_id == source.id
            )
        ).first()
        if not remaining:
            db.session.delete(source)
    db.session.commit()
    return True


def get_website_sources_by_domain(domain, user_id=None):
    return _website_query_for_user(user_id).filter(
        WebsiteSource.domain == domain
    ).order_by(WebsiteSource.created_at.asc()).all()


def delete_website_sources_by_domain(domain, user_id=None):
    sources = get_website_sources_by_domain(domain, user_id=user_id)
    deleted_ids = []
    for source in sources:
        if delete_website_source(source.id, user_id=user_id):
            deleted_ids.append(source.id)
    return deleted_ids


# =========================================================
# MESSAGE ATTACHMENT CRUD
# =========================================================


def create_message_attachment(
    chat_id,
    original_filename,
    stored_filename,
    file_type,
    mime_type,
    file_size,
    attachment_kind,
    user_id=None,
):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        raise ValueError("Chat not found.")
    attachment = MessageAttachment(
        chat_id=chat.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        attachment_kind=attachment_kind,
        status="processing",
    )
    db.session.add(attachment)
    db.session.commit()
    return attachment


def get_message_attachment_by_id(attachment_id, user_id=None):
    user_id = _resolve_user_id(user_id)
    query = MessageAttachment.query.join(
        Chat,
        MessageAttachment.chat_id == Chat.id,
    ).filter(MessageAttachment.id == attachment_id)
    if user_id is not None:
        query = query.filter(Chat.user_id == user_id)
    return query.first()


def get_pending_message_attachments(chat_id, user_id=None):
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    return (
        MessageAttachment.query
        .filter(
            MessageAttachment.chat_id == chat.id,
            MessageAttachment.message_id.is_(None),
        )
        .order_by(MessageAttachment.created_at.asc())
        .all()
    )


def get_message_attachments_by_ids(chat_id, attachment_ids, user_id=None):
    if not attachment_ids:
        return []
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    return (
        MessageAttachment.query
        .filter(
            MessageAttachment.chat_id == chat.id,
            MessageAttachment.id.in_(attachment_ids),
        )
        .order_by(MessageAttachment.created_at.asc())
        .all()
    )


def update_message_attachment_status(
    attachment_id,
    status,
    error_message=None,
    chunk_count=None,
    text_length=None,
    extraction_method=None,
    page_count=None,
    user_id=None,
):
    attachment = get_message_attachment_by_id(attachment_id, user_id=user_id)
    if not attachment:
        return None
    attachment.status = status
    attachment.error_message = error_message
    attachment.updated_at = utcnow()
    if chunk_count is not None:
        attachment.chunk_count = chunk_count
    if text_length is not None:
        attachment.text_length = text_length
    if extraction_method is not None:
        attachment.extraction_method = extraction_method
    if page_count is not None:
        attachment.page_count = page_count
    db.session.commit()
    return attachment


def create_message_attachment_chunks(attachment_id, chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    records = [
        MessageAttachmentChunk(
            attachment_id=attachment_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db.session.add_all(records)
    db.session.commit()
    return records


def get_ready_attachment_chunks(chat_id, attachment_ids=None, user_id=None):
    if attachment_ids == []:
        return []
    chat = get_chat_by_id(chat_id, user_id=user_id)
    if not chat:
        return []
    query = (
        MessageAttachmentChunk.query
        .join(
            MessageAttachment,
            MessageAttachmentChunk.attachment_id == MessageAttachment.id,
        )
        .filter(
            MessageAttachment.chat_id == chat.id,
            MessageAttachment.status == "ready",
        )
    )
    if attachment_ids is not None:
        query = query.filter(MessageAttachment.id.in_(attachment_ids))
    return query.all()


def delete_message_attachment(attachment_id, user_id=None):
    attachment = get_message_attachment_by_id(attachment_id, user_id=user_id)
    if not attachment:
        return False
    db.session.delete(attachment)
    db.session.commit()
    return True


# =========================================================
# SOCIAL KNOWLEDGE CRUD
# =========================================================


def add_social_source_to_user(source, user_id=None):
    user_id = _resolve_user_id(user_id)
    if user_id is None:
        return source
    membership = db.session.execute(
        db.select(user_social_sources).where(
            user_social_sources.c.user_id == user_id,
            user_social_sources.c.social_source_id == source.id,
        )
    ).first()
    if not membership:
        db.session.execute(
            user_social_sources.insert().values(
                user_id=user_id,
                social_source_id=source.id,
                created_at=utcnow(),
            )
        )
        db.session.commit()
    return source


def get_shared_social_source_by_url(url):
    return SocialSource.query.filter(
        db.or_(
            SocialSource.url == url,
            SocialSource.canonical_url == url,
        )
    ).first()


def create_social_source(
    url,
    canonical_url,
    title,
    platform,
    domain,
    extraction_method,
    status="processing",
    http_status=None,
    content_type=None,
    fetched_at=None,
    user_id=None,
):
    source = SocialSource(
        url=url,
        canonical_url=canonical_url,
        title=title,
        platform=platform,
        domain=domain,
        extraction_method=extraction_method,
        status=status,
        http_status=http_status,
        content_type=content_type,
        fetched_at=fetched_at,
    )
    db.session.add(source)
    db.session.flush()
    resolved_user_id = _resolve_user_id(user_id)
    if resolved_user_id is not None:
        db.session.execute(
            user_social_sources.insert().values(
                user_id=resolved_user_id,
                social_source_id=source.id,
                created_at=utcnow(),
            )
        )
    db.session.commit()
    return source


def get_social_source_by_id(source_id, user_id=None):
    return _social_query_for_user(user_id).filter(SocialSource.id == source_id).first()


def get_social_source_by_url(url, user_id=None):
    return _social_query_for_user(user_id).filter(
        db.or_(
            SocialSource.url == url,
            SocialSource.canonical_url == url,
        )
    ).first()


def get_all_social_sources(user_id=None):
    return _social_query_for_user(user_id).order_by(
        SocialSource.created_at.desc()
    ).all()


def create_social_source_chunks(source_id, chunks, embeddings):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    records = [
        SocialChunk(
            social_source_id=source_id,
            chunk_index=index,
            content=content,
            embedding=embedding,
        )
        for index, (content, embedding) in enumerate(zip(chunks, embeddings))
    ]
    db.session.add_all(records)
    db.session.commit()
    return records


def update_social_source_status(
    source_id,
    status,
    error_message=None,
    chunk_count=None,
    text_length=None,
    title=None,
    canonical_url=None,
    domain=None,
    extraction_method=None,
    http_status=None,
    content_type=None,
    fetched_at=None,
    user_id=None,
):
    source = get_social_source_by_id(source_id, user_id=user_id)
    if not source:
        return None
    source.status = status
    source.error_message = error_message
    source.updated_at = utcnow()
    for attribute, value in {
        "chunk_count": chunk_count,
        "text_length": text_length,
        "title": title,
        "canonical_url": canonical_url,
        "domain": domain,
        "extraction_method": extraction_method,
        "http_status": http_status,
        "content_type": content_type,
        "fetched_at": fetched_at,
    }.items():
        if value is not None:
            setattr(source, attribute, value)
    db.session.commit()
    return source


def replace_social_source_content(
    source_id,
    chunks,
    embeddings,
    title,
    canonical_url,
    domain,
    text_length,
    extraction_method,
    http_status,
    content_type,
    fetched_at,
    user_id=None,
):
    if len(chunks) != len(embeddings):
        raise ValueError("The chunk count and embedding count do not match.")
    source = get_social_source_by_id(source_id, user_id=user_id)
    if not source:
        return None
    try:
        SocialChunk.query.filter_by(
            social_source_id=source_id
        ).delete(synchronize_session=False)
        db.session.add_all([
            SocialChunk(
                social_source_id=source_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
            for index, (content, embedding) in enumerate(zip(chunks, embeddings))
        ])
        source.title = title
        source.canonical_url = canonical_url
        source.domain = domain
        source.extraction_method = extraction_method
        source.status = "ready"
        source.error_message = None
        source.chunk_count = len(chunks)
        source.text_length = text_length
        source.http_status = http_status
        source.content_type = content_type
        source.fetched_at = fetched_at
        source.updated_at = utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return source


def get_ready_social_chunks(social_source_ids=None, user_id=None):
    if social_source_ids == []:
        return []
    user_id = _resolve_user_id(user_id)
    query = (
        SocialChunk.query
        .join(SocialSource, SocialChunk.social_source_id == SocialSource.id)
        .filter(SocialSource.status == "ready")
    )
    if user_id is not None:
        query = query.join(
            user_social_sources,
            user_social_sources.c.social_source_id == SocialSource.id,
        ).filter(user_social_sources.c.user_id == user_id)
    if social_source_ids is not None:
        query = query.filter(SocialSource.id.in_(social_source_ids))
    return query.all()


def delete_social_source(source_id, user_id=None):
    user_id = _resolve_user_id(user_id)
    source = get_social_source_by_id(source_id, user_id=user_id)
    if not source:
        return False
    if user_id is None:
        db.session.delete(source)
    else:
        db.session.execute(
            user_social_sources.delete().where(
                user_social_sources.c.user_id == user_id,
                user_social_sources.c.social_source_id == source.id,
            )
        )
        remaining = db.session.execute(
            db.select(user_social_sources.c.user_id).where(
                user_social_sources.c.social_source_id == source.id
            )
        ).first()
        if not remaining:
            db.session.delete(source)
    db.session.commit()
    return True


# =========================================================
# CHAT ORGANIZATION CRUD
# =========================================================


def get_chat_folder_by_id(folder_id, user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    query = ChatFolder.query.filter(ChatFolder.id == folder_id)
    if resolved_user_id is not None:
        query = query.filter(ChatFolder.user_id == resolved_user_id)
    return query.first()


def get_chat_folders(user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    query = ChatFolder.query
    if resolved_user_id is not None:
        query = query.filter(ChatFolder.user_id == resolved_user_id)
    return query.order_by(ChatFolder.name.asc()).all()


def create_chat_folder(name, user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    folder = ChatFolder(
        user_id=resolved_user_id,
        name=" ".join(str(name or "").split())[:120],
    )
    db.session.add(folder)
    db.session.commit()
    return folder


def update_chat_folder(folder_id, name, user_id=None):
    folder = get_chat_folder_by_id(folder_id, user_id=user_id)
    if not folder:
        return None
    folder.name = " ".join(str(name or "").split())[:120]
    folder.updated_at = utcnow()
    db.session.commit()
    return folder


def delete_chat_folder(folder_id, user_id=None):
    folder = get_chat_folder_by_id(folder_id, user_id=user_id)
    if not folder:
        return False
    for chat in list(folder.chats):
        chat.folder_id = None
    db.session.delete(folder)
    db.session.commit()
    return True


def get_chat_tag_by_id(tag_id, user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    query = ChatTag.query.filter(ChatTag.id == tag_id)
    if resolved_user_id is not None:
        query = query.filter(ChatTag.user_id == resolved_user_id)
    return query.first()


def get_chat_tags(user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    query = ChatTag.query
    if resolved_user_id is not None:
        query = query.filter(ChatTag.user_id == resolved_user_id)
    return query.order_by(ChatTag.name.asc()).all()


def create_chat_tag(name, color="violet", user_id=None):
    resolved_user_id = _resolve_user_id(user_id)
    tag = ChatTag(
        user_id=resolved_user_id,
        name=" ".join(str(name or "").split())[:80],
        color=str(color or "violet")[:20],
    )
    db.session.add(tag)
    db.session.commit()
    return tag


def update_chat_tag(tag_id, name=None, color=None, user_id=None):
    tag = get_chat_tag_by_id(tag_id, user_id=user_id)
    if not tag:
        return None
    if name is not None:
        tag.name = " ".join(str(name or "").split())[:80]
    if color is not None:
        tag.color = str(color or "violet")[:20]
    tag.updated_at = utcnow()
    db.session.commit()
    return tag


def delete_chat_tag(tag_id, user_id=None):
    tag = get_chat_tag_by_id(tag_id, user_id=user_id)
    if not tag:
        return False
    db.session.delete(tag)
    db.session.commit()
    return True


def bulk_update_chats(
    chat_ids,
    action,
    folder_id=None,
    tag_id=None,
    user_id=None,
):
    resolved_user_id = _resolve_user_id(user_id)
    normalized_ids = sorted({int(value) for value in chat_ids})
    chats = _chat_query_for_user(resolved_user_id).filter(
        Chat.id.in_(normalized_ids)
    ).all()

    if len(chats) != len(normalized_ids):
        raise ValueError("One or more chats were not found.")

    if action == "archive":
        for chat in chats:
            chat.is_archived = True
            chat.is_pinned = False
    elif action == "restore":
        for chat in chats:
            chat.is_archived = False
    elif action == "favorite":
        for chat in chats:
            chat.is_favorite = True
    elif action == "unfavorite":
        for chat in chats:
            chat.is_favorite = False
    elif action == "move":
        if folder_id is None:
            target_folder = None
        else:
            target_folder = get_chat_folder_by_id(
                int(folder_id),
                user_id=resolved_user_id,
            )
            if not target_folder:
                raise ValueError("Chat folder not found.")
        for chat in chats:
            chat.folder_id = target_folder.id if target_folder else None
    elif action == "add_tag":
        tag = get_chat_tag_by_id(int(tag_id), user_id=resolved_user_id)
        if not tag:
            raise ValueError("Chat tag not found.")
        for chat in chats:
            if tag not in chat.tags:
                chat.tags.append(tag)
    elif action == "remove_tag":
        tag = get_chat_tag_by_id(int(tag_id), user_id=resolved_user_id)
        if not tag:
            raise ValueError("Chat tag not found.")
        for chat in chats:
            if tag in chat.tags:
                chat.tags.remove(tag)
    else:
        raise ValueError("Unsupported bulk chat action.")

    now = utcnow()
    for chat in chats:
        chat.updated_at = now

    db.session.commit()
    return chats
