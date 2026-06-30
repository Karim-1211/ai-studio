import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault(
    "APP_ENV",
    "testing"
)

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite://"
)

import pytest

from app import create_app
from database import db


@pytest.fixture()
def app(
    tmp_path
):
    database_path = (
        tmp_path
        / "test.db"
    )

    upload_folder = (
        tmp_path
        / "uploads"
    )

    log_folder = (
        tmp_path
        / "logs"
    )

    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "AUTO_CREATE_DATABASE": False,
        "SQLALCHEMY_DATABASE_URI": (
            f"sqlite:///{database_path}"
        ),
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "UPLOAD_FOLDER": str(
            upload_folder
        ),
        "LOG_FOLDER": str(
            log_folder
        ),
        "SECURITY_HEADERS_ENABLED": True,
        "OCR_ENABLED": False
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(
    app
):
    return app.test_client()
