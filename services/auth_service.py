from datetime import timedelta

from flask import current_app
from sqlalchemy import func

from database import db
from database.models import User, utcnow


class AuthenticationError(ValueError):
    pass


def normalize_email(value):
    email = str(value or "").strip().casefold()
    if not email or "@" not in email or len(email) > 320:
        raise AuthenticationError("Enter a valid email address.")
    local, _, domain = email.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise AuthenticationError("Enter a valid email address.")
    return email


def validate_display_name(value):
    display_name = " ".join(str(value or "").strip().split())
    if len(display_name) < 2:
        raise AuthenticationError("Display name must contain at least 2 characters.")
    if len(display_name) > 120:
        raise AuthenticationError("Display name cannot exceed 120 characters.")
    return display_name


def validate_password(password, confirmation=None):
    password = str(password or "")
    minimum = int(current_app.config.get("PASSWORD_MIN_LENGTH", 10))
    if len(password) < minimum:
        raise AuthenticationError(
            f"Password must contain at least {minimum} characters."
        )
    if len(password) > 128:
        raise AuthenticationError("Password cannot exceed 128 characters.")
    if confirmation is not None and password != confirmation:
        raise AuthenticationError("Password confirmation does not match.")
    return password


def get_user_by_email(email):
    normalized = normalize_email(email)
    return User.query.filter(func.lower(User.email) == normalized).first()


def create_user(email, display_name, password, is_admin=False):
    normalized = normalize_email(email)
    display_name = validate_display_name(display_name)
    password = validate_password(password)

    if User.query.filter(func.lower(User.email) == normalized).first():
        raise AuthenticationError("An account with this email already exists.")

    user = User(
        email=normalized,
        display_name=display_name,
        is_admin=bool(is_admin),
        active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    try:
        normalized = normalize_email(email)
    except AuthenticationError:
        return None, "Email or password is incorrect."

    user = User.query.filter(func.lower(User.email) == normalized).first()
    if not user:
        return None, "Email or password is incorrect."

    if not user.active:
        return None, "This account is disabled."

    now = utcnow()
    if user.locked_until and user.locked_until > now:
        return None, "Too many failed attempts. Try again later."

    if not user.check_password(str(password or "")):
        user.failed_login_attempts = int(user.failed_login_attempts or 0) + 1
        maximum = int(current_app.config.get("LOGIN_MAX_ATTEMPTS", 5))
        if user.failed_login_attempts >= maximum:
            minutes = int(current_app.config.get("LOGIN_LOCK_MINUTES", 15))
            user.locked_until = now + timedelta(minutes=minutes)
            user.failed_login_attempts = 0
        user.updated_at = now
        db.session.commit()
        return None, "Email or password is incorrect."

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    user.updated_at = now
    db.session.commit()
    return user, None


def set_user_password(user, password, confirmation=None):
    password = validate_password(password, confirmation)
    user.set_password(password)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()
    return user
