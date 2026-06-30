import os
import time
import uuid

import click

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import current_user, logout_user
from flask_wtf.csrf import CSRFError

from werkzeug.middleware.proxy_fix import (
    ProxyFix
)

from config import get_config_class

from database import (
    csrf,
    db,
    login_manager,
    migrate
)

from database.models import (
    User,
    ChatFolder,
    ChatTag,
    PromptTemplate,
    Chat,
    Message,
    Document,
    DocumentChunk,
    GlobalDocument,
    GlobalDocumentChunk,
    WebsiteSource,
    WebsiteChunk,
    MessageAttachment,
    MessageAttachmentChunk,
    SocialSource,
    SocialChunk,
    user_social_sources,
    user_website_sources
)

from routes.auth_routes import (
    auth_routes
)

from routes.admin_routes import (
    admin_routes
)

from routes.attachment_routes import (
    attachment_routes
)

from routes.chat_management_routes import (
    chat_management_routes
)

from routes.organization_routes import (
    organization_routes
)

from routes.prompt_routes import (
    prompt_routes
)

from routes.workspace_routes import (
    workspace_routes
)

from routes.chat_routes import (
    chat_routes
)

from routes.crawler_routes import (
    crawler_routes
)

from routes.document_routes import (
    document_routes
)

from routes.export_routes import (
    export_routes
)

from routes.global_document_routes import (
    global_document_routes
)

from routes.health_routes import (
    health_routes
)

from routes.model_routes import (
    model_routes
)

from routes.website_routes import (
    website_routes
)

from routes.social_routes import (
    social_routes
)

from services.auth_service import (
    AuthenticationError,
    create_user,
    get_user_by_email,
    set_user_password
)

from services.deletion_service import (
    find_orphan_uploads,
    remove_orphan_uploads
)

from services.document_service import (
    get_ocr_status
)

from services.logging_service import (
    configure_logging
)

from services.rate_limit_service import (
    rate_limiter
)

from services.telemetry_service import (
    record_request_metric
)


def create_app(
    config_override=None
):
    app = Flask(
        __name__
    )

    app.config.from_object(
        get_config_class()
    )

    if config_override:
        app.config.update(
            config_override
        )

    if (
        not app.config.get("TESTING")
        and not app.config.get("DEBUG")
        and app.config.get("SECRET_KEY")
        == "development-only-change-me"
    ):
        raise RuntimeError(
            "Set a strong SECRET_KEY before starting production."
        )

    if app.config.get(
        "TRUST_PROXY_HEADERS"
    ):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_port=1
        )

    os.makedirs(
        app.config[
            "UPLOAD_FOLDER"
        ],
        exist_ok=True
    )

    configure_logging(
        app
    )

    db.init_app(
        app
    )

    migrate.init_app(
        app,
        db
    )

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
    csrf.init_app(app)
    configure_authentication(app)

    register_blueprints(
        app
    )

    register_request_hooks(
        app
    )

    register_error_handlers(
        app
    )

    register_cli_commands(
        app
    )

    if app.config.get(
        "AUTO_CREATE_DATABASE"
    ):
        with app.app_context():
            db.create_all()

    log_ocr_status(
        app
    )

    return app



def configure_authentication(app):
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/") or request.path in {"/chat", "/models"}:
            return jsonify({
                "error": "Authentication is required.",
                "code": "authentication_required"
            }), 401

        return redirect(
            url_for(
                "auth.login",
                next=request.full_path if request.query_string else request.path
            )
        )

def register_blueprints(
    app
):
    app.register_blueprint(
        auth_routes
    )

    app.register_blueprint(
        admin_routes
    )

    app.register_blueprint(
        chat_routes
    )

    app.register_blueprint(
        model_routes
    )

    app.register_blueprint(
        chat_management_routes
    )

    app.register_blueprint(
        organization_routes
    )

    app.register_blueprint(
        prompt_routes
    )

    app.register_blueprint(
        workspace_routes
    )

    app.register_blueprint(
        export_routes
    )

    app.register_blueprint(
        document_routes
    )

    app.register_blueprint(
        global_document_routes
    )

    app.register_blueprint(
        health_routes
    )

    app.register_blueprint(
        website_routes
    )

    app.register_blueprint(
        crawler_routes
    )

    app.register_blueprint(
        attachment_routes
    )

    app.register_blueprint(
        social_routes
    )

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            user=current_user
        )

    @app.route(
        "/api/ocr/status",
        methods=["GET"]
    )
    def ocr_status():
        status = get_ocr_status(
            app.config
        )

        return jsonify({
            "enabled": status["enabled"],
            "available": status["available"],
            "language": status["language"],
            "supported_images": [
                "png",
                "jpg",
                "jpeg",
                "webp"
            ]
        })


def register_request_hooks(
    app
):
    @app.before_request
    def start_request():
        g.request_id = (
            request.headers.get(
                "X-Request-ID"
            )
            or uuid.uuid4().hex
        )

        g.request_started_at = (
            time.perf_counter()
        )

        limited_response = enforce_rate_limit(app)
        if limited_response is not None:
            return limited_response

        if not app.config.get("AUTH_REQUIRED", True):
            return None

        public_endpoints = {
            "auth.login",
            "auth.register",
            "static",
            "health_routes.liveness",
            "health_routes.health",
            "health_routes.readiness"
        }

        if request.endpoint in public_endpoints:
            return None

        if not current_user.is_authenticated:
            return login_manager.unauthorized()

        if not current_user.is_active:
            logout_user()
            return login_manager.unauthorized()

        return None

    @app.after_request
    def finalize_request(
        response
    ):
        request_id = getattr(
            g,
            "request_id",
            uuid.uuid4().hex
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        if app.config.get(
            "SECURITY_HEADERS_ENABLED"
        ):
            add_security_headers(
                response,
                app
            )

        if current_user.is_authenticated and not request.path.startswith("/static/"):
            response.headers.setdefault(
                "Cache-Control",
                "no-store, private"
            )

        started_at = getattr(
            g,
            "request_started_at",
            None
        )

        duration_ms = None

        if started_at is not None:
            duration_ms = round(
                (
                    time.perf_counter()
                    - started_at
                ) * 1000,
                1
            )

        if hasattr(g, "rate_limit_limit"):
            response.headers["X-RateLimit-Limit"] = str(g.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(g.rate_limit_remaining)
            if getattr(g, "rate_limit_retry_after", 0):
                response.headers["Retry-After"] = str(g.rate_limit_retry_after)

        if not request.path.startswith(
            "/static/"
        ):
            app.logger.info(
                "request_complete",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms
                }
            )

        excluded_metric_paths = {
            "/api/health",
            "/api/health/live",
            "/api/health/ready",
            "/api/admin/analytics",
        }
        if (
            app.config.get("METRICS_ENABLED", True)
            and request.method != "OPTIONS"
            and not request.path.startswith("/static/")
            and request.path not in excluded_metric_paths
        ):
            user_id = (
                int(current_user.id)
                if current_user.is_authenticated
                else None
            )
            record_request_metric(
                request_id=request_id,
                method=request.method,
                path=request.path,
                endpoint=request.endpoint,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
            )

        return response

    @app.teardown_request
    def rollback_failed_transaction(
        exception
    ):
        if exception is not None:
            db.session.rollback()


def enforce_rate_limit(app):
    if not app.config.get("RATE_LIMIT_ENABLED", True) or app.config.get("TESTING"):
        return None

    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None

    endpoint = request.endpoint or "unknown"
    limit = app.config.get("RATE_LIMIT_API_PER_MINUTE", 120)
    window_seconds = 60
    category = "api"

    if endpoint == "auth.login":
        limit = app.config.get("RATE_LIMIT_LOGIN_ATTEMPTS", 10)
        window_seconds = app.config.get("RATE_LIMIT_LOGIN_WINDOW_SECONDS", 900)
        category = "login"
    elif endpoint == "chat_routes.chat":
        limit = app.config.get("RATE_LIMIT_CHAT_PER_MINUTE", 30)
        category = "chat"
    elif (
        "attachment" in endpoint
        or "document" in endpoint
        or "workspace.restore" in endpoint
    ):
        limit = app.config.get("RATE_LIMIT_UPLOADS_PER_10_MINUTES", 20)
        window_seconds = 600
        category = "upload"

    identity = (
        f"user:{current_user.id}"
        if current_user.is_authenticated
        else f"ip:{request.remote_addr or 'unknown'}"
    )
    allowed, remaining, retry_after = rate_limiter.check(
        f"{category}:{identity}",
        limit,
        window_seconds,
    )
    g.rate_limit_limit = limit
    g.rate_limit_remaining = remaining
    g.rate_limit_retry_after = retry_after

    if allowed:
        return None

    message = "Too many requests. Please wait before trying again."
    if request.path.startswith("/api/") or request.path == "/chat":
        response = jsonify({
            "error": message,
            "code": "rate_limit_exceeded",
            "request_id": getattr(g, "request_id", None),
        })
        response.status_code = 429
        return response

    return render_template(
        "auth_error.html",
        title="Please wait",
        message=message,
    ), 429


def add_security_headers(
    response,
    app
):
    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff"
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "DENY"
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "no-referrer"
    )

    response.headers.setdefault(
        "Permissions-Policy",
        (
            "camera=(), microphone=(self), "
            "geolocation=()"
        )
    )

    response.headers.setdefault(
        "Content-Security-Policy",
        (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    )

    if app.config.get(
        "ENABLE_HSTS"
    ):
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains"
        )


def register_error_handlers(
    app
):
    def api_error(
        message,
        status_code,
        code
    ):
        return jsonify({
            "error": message,
            "code": code,
            "request_id": getattr(
                g,
                "request_id",
                None
            )
        }), status_code

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.path.startswith("/api/") or request.path == "/chat":
            return api_error(
                "The security token is missing or expired. Refresh the page and try again.",
                400,
                "csrf_failed"
            )
        return render_template(
            "auth_error.html",
            title="Security check failed",
            message="Refresh the page and submit the form again."
        ), 400

    @app.errorhandler(400)
    def bad_request(_error):
        return api_error(
            "The request could not be processed.",
            400,
            "bad_request"
        )

    @app.errorhandler(404)
    def not_found(_error):
        return api_error(
            "Resource not found.",
            404,
            "not_found"
        )

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return api_error(
            "Method not allowed.",
            405,
            "method_not_allowed"
        )

    @app.errorhandler(413)
    def file_too_large(_error):
        max_size_mb = round(
            app.config[
                "MAX_CONTENT_LENGTH"
            ] / (1024 * 1024)
        )

        return api_error(
            (
                "The uploaded file is too large. "
                f"The maximum size is {max_size_mb} MB."
            ),
            413,
            "file_too_large"
        )

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()

        app.logger.exception(
            "unhandled_server_error",
            extra={
                "request_id": getattr(
                    g,
                    "request_id",
                    None
                )
            }
        )

        return api_error(
            "An unexpected server error occurred.",
            500,
            "internal_server_error"
        )


def register_cli_commands(
    app
):
    @app.cli.command("bootstrap-owner")
    @click.option("--email", prompt="Owner email")
    @click.option("--name", "display_name", prompt="Display name")
    @click.password_option(confirmation_prompt=True)
    def bootstrap_owner(email, display_name, password):
        """Create the first administrator and claim legacy workspace data."""
        try:
            user = get_user_by_email(email)
            if user:
                user.display_name = display_name.strip()[:120] or user.display_name
                user.is_admin = True
                user.active = True
                set_user_password(user, password)
            else:
                user = create_user(
                    email=email,
                    display_name=display_name,
                    password=password,
                    is_admin=True
                )

            chat_count = Chat.query.filter(Chat.user_id.is_(None)).update(
                {Chat.user_id: user.id},
                synchronize_session=False
            )
            document_count = GlobalDocument.query.filter(
                GlobalDocument.user_id.is_(None)
            ).update(
                {GlobalDocument.user_id: user.id},
                synchronize_session=False
            )

            website_count = 0
            for source in WebsiteSource.query.all():
                membership = db.session.execute(
                    db.select(user_website_sources.c.user_id).where(
                        user_website_sources.c.user_id == user.id,
                        user_website_sources.c.website_source_id == source.id
                    )
                ).first()
                if not membership:
                    db.session.execute(
                        user_website_sources.insert().values(
                            user_id=user.id,
                            website_source_id=source.id
                        )
                    )
                    website_count += 1

            social_count = 0
            for source in SocialSource.query.all():
                membership = db.session.execute(
                    db.select(user_social_sources.c.user_id).where(
                        user_social_sources.c.user_id == user.id,
                        user_social_sources.c.social_source_id == source.id
                    )
                ).first()
                if not membership:
                    db.session.execute(
                        user_social_sources.insert().values(
                            user_id=user.id,
                            social_source_id=source.id
                        )
                    )
                    social_count += 1

            db.session.commit()
            click.echo(f"Owner ready: {user.email}")
            click.echo(f"Claimed chats: {chat_count}")
            click.echo(f"Claimed global documents: {document_count}")
            click.echo(f"Linked website sources: {website_count}")
            click.echo(f"Linked social sources: {social_count}")

        except AuthenticationError as error:
            db.session.rollback()
            raise click.ClickException(str(error)) from error

    @app.cli.command("create-user")
    @click.option("--email", prompt="Email")
    @click.option("--name", "display_name", prompt="Display name")
    @click.option("--admin", is_flag=True, help="Grant administrator access.")
    @click.password_option(confirmation_prompt=True)
    def create_user_command(email, display_name, admin, password):
        """Create an additional local user account."""
        try:
            user = create_user(
                email=email,
                display_name=display_name,
                password=password,
                is_admin=admin
            )
            click.echo(f"Created user: {user.email}")
        except AuthenticationError as error:
            raise click.ClickException(str(error)) from error

    @app.cli.command("reset-user-password")
    @click.option("--email", prompt="Email")
    @click.password_option(confirmation_prompt=True)
    def reset_user_password(email, password):
        """Reset a local account password."""
        try:
            user = get_user_by_email(email)
            if not user:
                raise AuthenticationError("User account not found.")
            set_user_password(user, password)
            user.active = True
            db.session.commit()
            click.echo(f"Password reset: {user.email}")
        except AuthenticationError as error:
            raise click.ClickException(str(error)) from error

    @app.cli.command(
        "cleanup-uploads"
    )
    @click.option(
        "--delete",
        "delete_files",
        is_flag=True,
        help=(
            "Delete orphan files. "
            "Without this option, only list them."
        )
    )
    def cleanup_uploads(
        delete_files
    ):
        upload_folder = app.config[
            "UPLOAD_FOLDER"
        ]

        if delete_files:
            result = remove_orphan_uploads(
                upload_folder
            )

            click.echo(
                f"Removed {len(result['removed'])} "
                "orphan upload(s)."
            )

            for failure in result[
                "failures"
            ]:
                click.echo(
                    (
                        "Failed: "
                        f"{failure['path']} - "
                        f"{failure['error']}"
                    ),
                    err=True
                )

            return

        orphan_paths = find_orphan_uploads(
            upload_folder
        )

        if not orphan_paths:
            click.echo(
                "No orphan uploads found."
            )
            return

        click.echo(
            f"Found {len(orphan_paths)} "
            "orphan upload(s):"
        )

        for path in orphan_paths:
            click.echo(
                path
            )


def log_ocr_status(
    app
):
    status = get_ocr_status(
        app.config
    )

    if (
        status["enabled"]
        and status["available"]
    ):
        app.logger.info(
            (
                "OCR is ready. "
                "Language: %s"
            ),
            status["language"]
        )

    elif status["enabled"]:
        app.logger.warning(
            (
                "OCR is enabled, but "
                "Tesseract was not found."
            )
        )

    else:
        app.logger.info(
            "OCR is disabled."
        )


if __name__ == "__main__":
    application = create_app()

    application.run(
        host="127.0.0.1",
        port=5000,
        debug=application.config.get(
            "DEBUG",
            False
        ),
        threaded=True
    )
