from functools import wraps
from urllib.parse import urljoin, urlsplit

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from database import db
from database.models import User, utcnow
from services.auth_service import (
    AuthenticationError,
    authenticate_user,
    create_user,
    normalize_email,
    set_user_password,
    validate_display_name,
    validate_password,
)
from services.deletion_service import delete_user_with_files
from services.audit_service import record_audit


auth_routes = Blueprint("auth", __name__)


def _safe_next_url(value):
    if not value:
        return None
    target = urlsplit(urljoin(request.host_url, value))
    host = urlsplit(request.host_url)
    if target.scheme not in {"http", "https"}:
        return None
    if target.netloc != host.netloc:
        return None
    return target.path + (f"?{target.query}" if target.query else "")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            return render_template("forbidden.html"), 403
        return view(*args, **kwargs)

    return wrapped


@auth_routes.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    has_users = db.session.query(User.id).first() is not None

    if not has_users:
        return redirect(url_for("auth.register"))

    next_url = _safe_next_url(request.args.get("next") or request.form.get("next"))

    if request.method == "POST":
        user, error = authenticate_user(
            request.form.get("email"),
            request.form.get("password"),
        )
        if user:
            login_user(
                user,
                remember=request.form.get("remember") == "on",
                fresh=True,
            )
            record_audit(
                "auth.login",
                actor_user_id=user.id,
                target_user_id=user.id,
                entity_type="user",
                entity_id=user.id,
            )
            return redirect(next_url or url_for("home"))
        flash(error or "Unable to sign in.", "error")

    return render_template(
        "auth.html",
        mode="login",
        next_url=next_url,
        allow_registration=current_app.config.get("ALLOW_REGISTRATION", False),
        has_users=has_users,
    )


@auth_routes.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    has_users = db.session.query(User.id).first() is not None
    first_owner_setup = not has_users

    if not current_app.config.get("ALLOW_REGISTRATION", False) and not first_owner_setup:
        flash("Public registration is disabled.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        try:
            password = validate_password(
                request.form.get("password"),
                request.form.get("password_confirmation")
            )
            user = create_user(
                email=request.form.get("email"),
                display_name=request.form.get("display_name"),
                password=password,
                is_admin=first_owner_setup,
            )
            login_user(user, fresh=True)
            return redirect(url_for("home"))
        except AuthenticationError as error:
            db.session.rollback()
            flash(str(error), "error")

    return render_template(
        "auth.html",
        mode="register",
        allow_registration=True,
        has_users=has_users,
        first_owner_setup=first_owner_setup,
    )


@auth_routes.route("/logout", methods=["POST"])
@login_required
def logout():
    record_audit(
        "auth.logout",
        target_user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
    )
    logout_user()
    return redirect(url_for("auth.login"))


@auth_routes.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "profile":
                current_user.display_name = validate_display_name(
                    request.form.get("display_name")
                )
                requested_email = normalize_email(request.form.get("email"))
                conflict = User.query.filter(
                    User.email == requested_email,
                    User.id != current_user.id,
                ).first()
                if conflict:
                    raise AuthenticationError(
                        "Another account already uses this email address."
                    )
                current_user.email = requested_email
                current_user.updated_at = utcnow()
                db.session.commit()
                record_audit(
                    "account.profile_updated",
                    target_user_id=current_user.id,
                    entity_type="user",
                    entity_id=current_user.id,
                )
                flash("Account details updated.", "success")

            elif action == "password":
                if not current_user.check_password(
                    request.form.get("current_password") or ""
                ):
                    raise AuthenticationError("Current password is incorrect.")
                set_user_password(
                    current_user,
                    request.form.get("new_password"),
                    request.form.get("new_password_confirmation"),
                )
                record_audit(
                    "account.password_updated",
                    target_user_id=current_user.id,
                    entity_type="user",
                    entity_id=current_user.id,
                )
                flash("Password updated.", "success")

            else:
                raise AuthenticationError("Unsupported account action.")

        except AuthenticationError as error:
            db.session.rollback()
            flash(str(error), "error")

        return redirect(url_for("auth.account"))

    return render_template("account.html")


@auth_routes.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    if not current_user.check_password(request.form.get("password") or ""):
        flash("Password is incorrect. Account was not deleted.", "error")
        return redirect(url_for("auth.account"))

    if current_user.is_admin:
        other_admin = User.query.filter(
            User.is_admin.is_(True),
            User.active.is_(True),
            User.id != current_user.id,
        ).first()
        if not other_admin:
            flash(
                "Create another active administrator before deleting this account.",
                "error",
            )
            return redirect(url_for("auth.account"))

    user = current_user._get_current_object()
    logout_user()
    delete_user_with_files(user)
    flash("Your account and private workspace were deleted.", "success")
    return redirect(url_for("auth.login"))


@auth_routes.route("/api/auth/me", methods=["GET"])
@login_required
def current_account_api():
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "is_admin": current_user.is_admin,
    })


@auth_routes.route("/admin/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    if request.method == "POST":
        try:
            created_user = create_user(
                email=request.form.get("email"),
                display_name=request.form.get("display_name"),
                password=request.form.get("password"),
                is_admin=request.form.get("is_admin") == "on",
            )
            record_audit(
                "admin.user_created",
                target_user_id=created_user.id,
                entity_type="user",
                entity_id=created_user.id,
                details={"is_admin": bool(created_user.is_admin)},
            )
            flash("User account created.", "success")
        except AuthenticationError as error:
            flash(str(error), "error")
        return redirect(url_for("auth.admin_users"))

    users = User.query.order_by(User.created_at.asc()).all()
    return render_template("admin_users.html", users=users)


@auth_routes.route("/admin/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User account not found.", "error")
    elif user.id == current_user.id:
        flash("You cannot disable your own account.", "error")
    else:
        user.active = not user.active
        user.updated_at = utcnow()
        db.session.commit()
        record_audit(
            "admin.user_status_changed",
            target_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            details={"active": bool(user.active)},
        )
        flash("User status updated.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_routes.route("/admin/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def toggle_user_admin(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User account not found.", "error")
    elif user.id == current_user.id:
        flash("You cannot remove your own administrator role.", "error")
    else:
        user.is_admin = not user.is_admin
        user.updated_at = utcnow()
        db.session.commit()
        record_audit(
            "admin.user_role_changed",
            target_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            details={"is_admin": bool(user.is_admin)},
        )
        flash("Administrator role updated.", "success")
    return redirect(url_for("auth.admin_users"))


@auth_routes.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User account not found.", "error")
    elif user.id == current_user.id:
        flash("Use Account Settings to delete your own account.", "error")
    else:
        deleted_user_id = user.id
        deleted_email = user.email
        delete_user_with_files(user)
        record_audit(
            "admin.user_deleted",
            entity_type="user",
            entity_id=deleted_user_id,
            details={"email": deleted_email},
        )
        flash("User account and private workspace deleted.", "success")
    return redirect(url_for("auth.admin_users"))
