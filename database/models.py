from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from database import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


user_website_sources = db.Table(
    "user_website_sources",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "website_source_id",
        db.Integer,
        db.ForeignKey("website_sources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime,
        nullable=False,
        default=utcnow,
    ),
)


user_social_sources = db.Table(
    "user_social_sources",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "social_source_id",
        db.Integer,
        db.ForeignKey("social_sources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "created_at",
        db.DateTime,
        nullable=False,
        default=utcnow,
    ),
)


chat_tags = db.Table(
    "chat_tag_links",
    db.Column(
        "chat_id",
        db.Integer,
        db.ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("chat_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ChatFolder(db.Model):
    __tablename__ = "chat_folders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="chat_folders")
    chats = db.relationship("Chat", back_populates="folder", lazy=True)

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "name",
            name="uq_chat_folders_user_name",
        ),
    )


class ChatTag(db.Model):
    __tablename__ = "chat_tags"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(20), nullable=False, default="violet")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="chat_tags")
    chats = db.relationship(
        "Chat",
        secondary=chat_tags,
        back_populates="tags",
        lazy="selectin",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "name",
            name="uq_chat_tags_user_name",
        ),
    )


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False, index=True)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    chats = db.relationship(
        "Chat",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    chat_folders = db.relationship(
        "ChatFolder",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    chat_tags = db.relationship(
        "ChatTag",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    prompt_templates = db.relationship(
        "PromptTemplate",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    global_documents = db.relationship(
        "GlobalDocument",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    website_sources = db.relationship(
        "WebsiteSource",
        secondary=user_website_sources,
        back_populates="users",
        lazy="selectin",
    )

    social_sources = db.relationship(
        "SocialSource",
        secondary=user_social_sources,
        back_populates="users",
        lazy="selectin",
    )

    @property
    def is_active(self):
        return bool(self.active)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.updated_at = utcnow()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > utcnow())


class PromptTemplate(db.Model):
    __tablename__ = "prompt_templates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(160), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False, default="General", index=True)
    is_favorite = db.Column(db.Boolean, nullable=False, default=False, index=True)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="prompt_templates")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "title",
            name="uq_prompt_templates_user_title",
        ),
    )


class Chat(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False, default="New Chat")
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    branched_from_message_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    is_favorite = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="chats")
    folder = db.relationship("ChatFolder", back_populates="chats")
    parent_chat = db.relationship(
        "Chat",
        remote_side=[id],
        backref=db.backref("branches", lazy=True),
        foreign_keys=[parent_chat_id],
    )
    branched_from_message = db.relationship(
        "Message",
        foreign_keys=[branched_from_message_id],
        post_update=True,
    )
    tags = db.relationship(
        "ChatTag",
        secondary=chat_tags,
        back_populates="chats",
        lazy="selectin",
    )
    messages = db.relationship(
        "Message",
        backref=db.backref("chat", foreign_keys="Message.chat_id"),
        foreign_keys="Message.chat_id",
        lazy=True,
        cascade="all, delete-orphan",
    )
    documents = db.relationship(
        "Document",
        backref="chat",
        lazy=True,
        cascade="all, delete-orphan",
    )
    attachments = db.relationship(
        "MessageAttachment",
        backref="chat",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(100))
    mode = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    attachments = db.relationship(
        "MessageAttachment",
        backref="message",
        lazy=True,
    )


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id"),
        nullable=False,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(
        db.String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    error_message = db.Column(db.Text)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    text_length = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    chunks = db.relationship(
        "DocumentChunk",
        backref="document",
        lazy=True,
        cascade="all, delete-orphan",
    )


class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunk_index",
        ),
    )


class GlobalDocument(db.Model):
    __tablename__ = "global_documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(
        db.String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    error_message = db.Column(db.Text)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    text_length = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="global_documents")
    chunks = db.relationship(
        "GlobalDocumentChunk",
        backref="global_document",
        lazy=True,
        cascade="all, delete-orphan",
    )


class GlobalDocumentChunk(db.Model):
    __tablename__ = "global_document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    global_document_id = db.Column(
        db.Integer,
        db.ForeignKey("global_documents.id"),
        nullable=False,
        index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "global_document_id",
            "chunk_index",
            name="uq_global_document_chunk_index",
        ),
    )


class WebsiteSource(db.Model):
    __tablename__ = "website_sources"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False, unique=True)
    canonical_url = db.Column(db.String(2048), nullable=False, unique=True)
    title = db.Column(db.String(500), nullable=False)
    domain = db.Column(db.String(255), nullable=False, index=True)
    status = db.Column(
        db.String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    error_message = db.Column(db.Text)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    text_length = db.Column(db.Integer, nullable=False, default=0)
    http_status = db.Column(db.Integer)
    content_type = db.Column(db.String(255))
    fetched_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    users = db.relationship(
        "User",
        secondary=user_website_sources,
        back_populates="website_sources",
        lazy="selectin",
    )
    chunks = db.relationship(
        "WebsiteChunk",
        backref="website_source",
        lazy=True,
        cascade="all, delete-orphan",
    )


class WebsiteChunk(db.Model):
    __tablename__ = "website_chunks"

    id = db.Column(db.Integer, primary_key=True)
    website_source_id = db.Column(
        db.Integer,
        db.ForeignKey("website_sources.id"),
        nullable=False,
        index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "website_source_id",
            "chunk_index",
            name="uq_website_chunk_index",
        ),
    )


class MessageAttachment(db.Model):
    __tablename__ = "message_attachments"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id"),
        nullable=False,
        index=True,
    )
    message_id = db.Column(
        db.Integer,
        db.ForeignKey("messages.id"),
        nullable=True,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(20), nullable=False)
    mime_type = db.Column(db.String(255))
    file_size = db.Column(db.Integer, nullable=False, default=0)
    attachment_kind = db.Column(
        db.String(30),
        nullable=False,
        default="document",
        index=True,
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    error_message = db.Column(db.Text)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    text_length = db.Column(db.Integer, nullable=False, default=0)
    extraction_method = db.Column(db.String(30))
    page_count = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    chunks = db.relationship(
        "MessageAttachmentChunk",
        backref="attachment",
        lazy=True,
        cascade="all, delete-orphan",
    )


class MessageAttachmentChunk(db.Model):
    __tablename__ = "message_attachment_chunks"

    id = db.Column(db.Integer, primary_key=True)
    attachment_id = db.Column(
        db.Integer,
        db.ForeignKey("message_attachments.id"),
        nullable=False,
        index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "attachment_id",
            "chunk_index",
            name="uq_message_attachment_chunk_index",
        ),
    )


class SocialSource(db.Model):
    __tablename__ = "social_sources"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False, unique=True)
    canonical_url = db.Column(db.String(2048), nullable=False, unique=True)
    title = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50), nullable=False, index=True)
    domain = db.Column(db.String(255), nullable=False, index=True)
    extraction_method = db.Column(
        db.String(30),
        nullable=False,
        default="public_page",
    )
    status = db.Column(
        db.String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    error_message = db.Column(db.Text)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    text_length = db.Column(db.Integer, nullable=False, default=0)
    http_status = db.Column(db.Integer)
    content_type = db.Column(db.String(255))
    fetched_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    users = db.relationship(
        "User",
        secondary=user_social_sources,
        back_populates="social_sources",
        lazy="selectin",
    )
    chunks = db.relationship(
        "SocialChunk",
        backref="social_source",
        lazy=True,
        cascade="all, delete-orphan",
    )


class SocialChunk(db.Model):
    __tablename__ = "social_chunks"

    id = db.Column(db.Integer, primary_key=True)
    social_source_id = db.Column(
        db.Integer,
        db.ForeignKey("social_sources.id"),
        nullable=False,
        index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "social_source_id",
            "chunk_index",
            name="uq_social_chunk_index",
        ),
    )


class RequestMetric(db.Model):
    __tablename__ = "request_metrics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    method = db.Column(db.String(12), nullable=False)
    path = db.Column(db.String(512), nullable=False, index=True)
    endpoint = db.Column(db.String(160), nullable=True, index=True)
    status_code = db.Column(db.Integer, nullable=False, index=True)
    duration_ms = db.Column(db.Float, nullable=True)
    is_error = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)


class ModelUsageEvent(db.Model):
    __tablename__ = "model_usage_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chat_id = db.Column(
        db.Integer,
        db.ForeignKey("chats.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id = db.Column(db.String(64), nullable=True, index=True)
    model = db.Column(db.String(200), nullable=False, index=True)
    mode = db.Column(db.String(50), nullable=True, index=True)
    duration_ms = db.Column(db.Float, nullable=True)
    success = db.Column(db.Boolean, nullable=False, default=True, index=True)
    used_rag = db.Column(db.Boolean, nullable=False, default=False, index=True)
    source_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)


class HealthCheckEvent(db.Model):
    __tablename__ = "health_check_events"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    ready = db.Column(db.Boolean, nullable=False, default=False, index=True)
    duration_ms = db.Column(db.Float, nullable=True)
    components = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = db.Column(db.String(120), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=True, index=True)
    entity_id = db.Column(db.String(120), nullable=True)
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
