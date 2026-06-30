import os
from datetime import timedelta

from dotenv import load_dotenv


BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


def read_boolean_environment(
    name,
    default=False
):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


def read_integer_environment(
    name,
    default,
    minimum,
    maximum
):
    try:
        value = int(
            os.getenv(name, str(default))
        )
    except (
        TypeError,
        ValueError
    ):
        value = default

    return max(
        minimum,
        min(maximum, value)
    )


def read_float_environment(
    name,
    default,
    minimum,
    maximum
):
    try:
        value = float(
            os.getenv(name, str(default))
        )
    except (
        TypeError,
        ValueError
    ):
        value = default

    return max(
        minimum,
        min(maximum, value)
    )


APP_ENV = (
    os.getenv(
        "APP_ENV",
        "development"
    )
    .strip()
    .lower()
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-only-change-me"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
).rstrip("/")


AI_PROVIDER = (
    os.getenv("AI_PROVIDER", "ollama")
    .strip()
    .lower()
)

if AI_PROVIDER == "claude":
    AI_PROVIDER = "anthropic"

if AI_PROVIDER not in {"ollama", "openai", "openrouter", "gemini", "anthropic"}:
    AI_PROVIDER = "ollama"

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY", "").strip()
    or None
)

OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    .strip()
    .rstrip("/")
    or "https://api.openai.com/v1"
)

OPENAI_MODEL = (
    os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    or "gpt-4o-mini"
)

OPENAI_MODELS = [
    item.strip()
    for item in os.getenv(
        "OPENAI_MODELS",
        OPENAI_MODEL
    ).split(",")
    if item.strip()
]

OPENROUTER_API_KEY = (
    os.getenv("OPENROUTER_API_KEY", "").strip()
    or None
)

OPENROUTER_BASE_URL = (
    os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    .strip()
    .rstrip("/")
    or "https://openrouter.ai/api/v1"
)

OPENROUTER_MODEL = (
    os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    or "openai/gpt-4o-mini"
)

OPENROUTER_MODELS = [
    item.strip()
    for item in os.getenv(
        "OPENROUTER_MODELS",
        OPENROUTER_MODEL
    ).split(",")
    if item.strip()
]

GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY", "").strip()
    or None
)

GEMINI_BASE_URL = (
    os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
    .strip()
    .rstrip("/")
    or "https://generativelanguage.googleapis.com/v1beta"
)

GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    or "gemini-1.5-flash"
)

GEMINI_MODELS = [
    item.strip()
    for item in os.getenv(
        "GEMINI_MODELS",
        GEMINI_MODEL
    ).split(",")
    if item.strip()
]

ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY", "").strip()
    or None
)

ANTHROPIC_BASE_URL = (
    os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
    .strip()
    .rstrip("/")
    or "https://api.anthropic.com/v1"
)

ANTHROPIC_VERSION = (
    os.getenv("ANTHROPIC_VERSION", "2023-06-01").strip()
    or "2023-06-01"
)

ANTHROPIC_MODEL = (
    os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest").strip()
    or "claude-3-5-haiku-latest"
)

ANTHROPIC_MODELS = [
    item.strip()
    for item in os.getenv(
        "ANTHROPIC_MODELS",
        ANTHROPIC_MODEL
    ).split(",")
    if item.strip()
]

if OPENAI_MODEL not in OPENAI_MODELS:
    OPENAI_MODELS.insert(0, OPENAI_MODEL)

if OPENROUTER_MODEL not in OPENROUTER_MODELS:
    OPENROUTER_MODELS.insert(0, OPENROUTER_MODEL)

if GEMINI_MODEL not in GEMINI_MODELS:
    GEMINI_MODELS.insert(0, GEMINI_MODEL)

if ANTHROPIC_MODEL not in ANTHROPIC_MODELS:
    ANTHROPIC_MODELS.insert(0, ANTHROPIC_MODEL)

EMBEDDING_PROVIDER = (
    os.getenv("EMBEDDING_PROVIDER", AI_PROVIDER)
    .strip()
    .lower()
)

if EMBEDDING_PROVIDER == "claude":
    EMBEDDING_PROVIDER = "anthropic"

if EMBEDDING_PROVIDER not in {"ollama", "gemini", "openai", "openrouter", "anthropic"}:
    EMBEDDING_PROVIDER = AI_PROVIDER

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-004" if EMBEDDING_PROVIDER == "gemini" else "embeddinggemma"
).strip()

VISION_MODEL = (
    os.getenv("VISION_MODEL", "").strip()
    or None
)

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. "
        "Create a .env file in the project root."
    )


SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 1800
}


UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

# Flask request limit includes multipart/form-data overhead, so it is
# intentionally a little larger than the default 20 MB per-file limit.
MAX_CONTENT_LENGTH = read_integer_environment(
    "MAX_CONTENT_LENGTH",
    default=25 * 1024 * 1024,
    minimum=1 * 1024 * 1024,
    maximum=100 * 1024 * 1024
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "txt",
    "png",
    "jpg",
    "jpeg",
    "webp"
}

ATTACHMENT_ALLOWED_EXTENSIONS = {
    "pdf",
    "docx",
    "txt",
    "png",
    "jpg",
    "jpeg",
    "webp"
}

ATTACHMENT_MAX_FILES = read_integer_environment(
    "ATTACHMENT_MAX_FILES",
    default=5,
    minimum=1,
    maximum=10
)

ATTACHMENT_MAX_FILE_BYTES = read_integer_environment(
    "ATTACHMENT_MAX_FILE_BYTES",
    default=20 * 1024 * 1024,
    minimum=100_000,
    maximum=50 * 1024 * 1024
)

ATTACHMENT_MAX_TOTAL_BYTES = read_integer_environment(
    "ATTACHMENT_MAX_TOTAL_BYTES",
    default=40 * 1024 * 1024,
    minimum=100_000,
    maximum=100 * 1024 * 1024
)


RAG_TOP_K = read_integer_environment(
    "RAG_TOP_K",
    default=5,
    minimum=1,
    maximum=20
)

RAG_CHUNK_SIZE = read_integer_environment(
    "RAG_CHUNK_SIZE",
    default=450,
    minimum=100,
    maximum=2000
)

RAG_CHUNK_OVERLAP = read_integer_environment(
    "RAG_CHUNK_OVERLAP",
    default=80,
    minimum=0,
    maximum=500
)

if RAG_CHUNK_OVERLAP >= RAG_CHUNK_SIZE:
    RAG_CHUNK_OVERLAP = max(
        0,
        RAG_CHUNK_SIZE // 5
    )


OCR_ENABLED = read_boolean_environment(
    "OCR_ENABLED",
    default=True
)

TESSERACT_CMD = (
    os.getenv(
        "TESSERACT_CMD",
        ""
    ).strip()
    or None
)

OCR_LANGUAGE = (
    os.getenv(
        "OCR_LANGUAGE",
        "eng"
    ).strip()
    or "eng"
)

OCR_TESSERACT_CONFIG = (
    os.getenv(
        "OCR_TESSERACT_CONFIG",
        "--oem 3 --psm 3"
    ).strip()
)

OCR_MIN_TEXT_CHARACTERS = (
    read_integer_environment(
        "OCR_MIN_TEXT_CHARACTERS",
        default=40,
        minimum=1,
        maximum=500
    )
)

MAX_PDF_PAGES = read_integer_environment(
    "MAX_PDF_PAGES",
    default=100,
    minimum=1,
    maximum=500
)

OCR_MAX_PDF_PAGES = (
    read_integer_environment(
        "OCR_MAX_PDF_PAGES",
        default=25,
        minimum=1,
        maximum=100
    )
)

OCR_PDF_DPI = read_integer_environment(
    "OCR_PDF_DPI",
    default=200,
    minimum=100,
    maximum=300
)

OCR_MAX_IMAGE_PIXELS = (
    read_integer_environment(
        "OCR_MAX_IMAGE_PIXELS",
        default=25_000_000,
        minimum=1_000_000,
        maximum=100_000_000
    )
)


WEBSITE_CONNECT_TIMEOUT = read_float_environment(
    "WEBSITE_CONNECT_TIMEOUT",
    default=5.0,
    minimum=1.0,
    maximum=30.0
)

WEBSITE_READ_TIMEOUT = read_float_environment(
    "WEBSITE_READ_TIMEOUT",
    default=15.0,
    minimum=1.0,
    maximum=60.0
)

WEBSITE_MAX_RESPONSE_BYTES = read_integer_environment(
    "WEBSITE_MAX_RESPONSE_BYTES",
    default=2_000_000,
    minimum=100_000,
    maximum=10_000_000
)

WEBSITE_MAX_REDIRECTS = read_integer_environment(
    "WEBSITE_MAX_REDIRECTS",
    default=3,
    minimum=0,
    maximum=10
)

WEBSITE_MAX_TEXT_CHARACTERS = read_integer_environment(
    "WEBSITE_MAX_TEXT_CHARACTERS",
    default=500_000,
    minimum=1_000,
    maximum=2_000_000
)

WEBSITE_MIN_TEXT_CHARACTERS = read_integer_environment(
    "WEBSITE_MIN_TEXT_CHARACTERS",
    default=120,
    minimum=20,
    maximum=5_000
)

WEBSITE_RESPECT_ROBOTS = read_boolean_environment(
    "WEBSITE_RESPECT_ROBOTS",
    default=True
)

WEBSITE_USER_AGENT = (
    os.getenv(
        "WEBSITE_USER_AGENT",
        "AI-Studio-KnowledgeIndexer/1.0"
    ).strip()
    or "AI-Studio-KnowledgeIndexer/1.0"
)



WEBSITE_CRAWLER_DEFAULT_MAX_PAGES = read_integer_environment(
    "WEBSITE_CRAWLER_DEFAULT_MAX_PAGES",
    default=25,
    minimum=1,
    maximum=100
)

WEBSITE_CRAWLER_MAX_PAGES = read_integer_environment(
    "WEBSITE_CRAWLER_MAX_PAGES",
    default=100,
    minimum=1,
    maximum=250
)

WEBSITE_CRAWLER_DEFAULT_DEPTH = read_integer_environment(
    "WEBSITE_CRAWLER_DEFAULT_DEPTH",
    default=2,
    minimum=0,
    maximum=5
)

WEBSITE_CRAWLER_MAX_DEPTH = read_integer_environment(
    "WEBSITE_CRAWLER_MAX_DEPTH",
    default=5,
    minimum=0,
    maximum=8
)

WEBSITE_CRAWLER_DISCOVERY_BYTES = read_integer_environment(
    "WEBSITE_CRAWLER_DISCOVERY_BYTES",
    default=750_000,
    minimum=100_000,
    maximum=5_000_000
)

WEBSITE_CRAWLER_SITEMAP_BYTES = read_integer_environment(
    "WEBSITE_CRAWLER_SITEMAP_BYTES",
    default=1_000_000,
    minimum=100_000,
    maximum=10_000_000
)

WEBSITE_CRAWLER_MAX_SITEMAPS = read_integer_environment(
    "WEBSITE_CRAWLER_MAX_SITEMAPS",
    default=8,
    minimum=1,
    maximum=50
)


SOCIAL_MAX_MANUAL_CHARACTERS = read_integer_environment(
    "SOCIAL_MAX_MANUAL_CHARACTERS",
    default=200_000,
    minimum=1_000,
    maximum=1_000_000
)

SOCIAL_MIN_TEXT_CHARACTERS = read_integer_environment(
    "SOCIAL_MIN_TEXT_CHARACTERS",
    default=40,
    minimum=20,
    maximum=5_000
)

GOOGLE_MAPS_API_KEY = (
    os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    or None
)

GOOGLE_PLACES_LANGUAGE_CODE = (
    os.getenv("GOOGLE_PLACES_LANGUAGE_CODE", "en").strip()
    or "en"
)

GOOGLE_PLACES_MAX_REVIEWS = read_integer_environment(
    "GOOGLE_PLACES_MAX_REVIEWS",
    default=5,
    minimum=0,
    maximum=5
)

WORKSPACE_BACKUP_MAX_MEMBERS = read_integer_environment(
    "WORKSPACE_BACKUP_MAX_MEMBERS",
    default=5_000,
    minimum=100,
    maximum=50_000
)

WORKSPACE_BACKUP_MAX_UNCOMPRESSED_BYTES = read_integer_environment(
    "WORKSPACE_BACKUP_MAX_UNCOMPRESSED_BYTES",
    default=1_000_000_000,
    minimum=10_000_000,
    maximum=5_000_000_000
)

LOG_FOLDER = os.path.join(
    BASE_DIR,
    "logs"
)

LOG_LEVEL = (
    os.getenv(
        "LOG_LEVEL",
        "INFO"
    )
    .strip()
    .upper()
)

LOG_MAX_BYTES = read_integer_environment(
    "LOG_MAX_BYTES",
    default=2_000_000,
    minimum=100_000,
    maximum=50_000_000
)

LOG_BACKUP_COUNT = read_integer_environment(
    "LOG_BACKUP_COUNT",
    default=5,
    minimum=1,
    maximum=20
)


HEALTH_HTTP_TIMEOUT = read_float_environment(
    "HEALTH_HTTP_TIMEOUT",
    default=3.0,
    minimum=0.5,
    maximum=30.0
)

AUTO_CREATE_DATABASE = read_boolean_environment(
    "AUTO_CREATE_DATABASE",
    default=False
)

SECURITY_HEADERS_ENABLED = read_boolean_environment(
    "SECURITY_HEADERS_ENABLED",
    default=True
)

ENABLE_HSTS = read_boolean_environment(
    "ENABLE_HSTS",
    default=False
)

TRUST_PROXY_HEADERS = read_boolean_environment(
    "TRUST_PROXY_HEADERS",
    default=False
)


AUTH_REQUIRED = read_boolean_environment(
    "AUTH_REQUIRED",
    default=True
)

ALLOW_REGISTRATION = read_boolean_environment(
    "ALLOW_REGISTRATION",
    default=False
)

SESSION_COOKIE_SECURE = read_boolean_environment(
    "SESSION_COOKIE_SECURE",
    default=APP_ENV == "production"
)

SESSION_COOKIE_SAMESITE = (
    os.getenv("SESSION_COOKIE_SAMESITE", "Lax").strip().title()
    or "Lax"
)

if SESSION_COOKIE_SAMESITE not in {"Lax", "Strict", "None"}:
    SESSION_COOKIE_SAMESITE = "Lax"

REMEMBER_COOKIE_DAYS = read_integer_environment(
    "REMEMBER_COOKIE_DAYS",
    default=30,
    minimum=1,
    maximum=365
)

LOGIN_MAX_ATTEMPTS = read_integer_environment(
    "LOGIN_MAX_ATTEMPTS",
    default=5,
    minimum=3,
    maximum=20
)

LOGIN_LOCK_MINUTES = read_integer_environment(
    "LOGIN_LOCK_MINUTES",
    default=15,
    minimum=1,
    maximum=1440
)

PASSWORD_MIN_LENGTH = read_integer_environment(
    "PASSWORD_MIN_LENGTH",
    default=10,
    minimum=8,
    maximum=64
)


METRICS_ENABLED = read_boolean_environment(
    "METRICS_ENABLED",
    default=True
)

HEALTH_HISTORY_INTERVAL_SECONDS = read_integer_environment(
    "HEALTH_HISTORY_INTERVAL_SECONDS",
    default=300,
    minimum=30,
    maximum=86400
)

RATE_LIMIT_ENABLED = read_boolean_environment(
    "RATE_LIMIT_ENABLED",
    default=True
)

RATE_LIMIT_CHAT_PER_MINUTE = read_integer_environment(
    "RATE_LIMIT_CHAT_PER_MINUTE",
    default=30,
    minimum=1,
    maximum=600
)

RATE_LIMIT_API_PER_MINUTE = read_integer_environment(
    "RATE_LIMIT_API_PER_MINUTE",
    default=120,
    minimum=10,
    maximum=5000
)

RATE_LIMIT_UPLOADS_PER_10_MINUTES = read_integer_environment(
    "RATE_LIMIT_UPLOADS_PER_10_MINUTES",
    default=20,
    minimum=1,
    maximum=500
)

RATE_LIMIT_LOGIN_ATTEMPTS = read_integer_environment(
    "RATE_LIMIT_LOGIN_ATTEMPTS",
    default=10,
    minimum=3,
    maximum=100
)

RATE_LIMIT_LOGIN_WINDOW_SECONDS = read_integer_environment(
    "RATE_LIMIT_LOGIN_WINDOW_SECONDS",
    default=900,
    minimum=60,
    maximum=86400
)


class BaseConfig:
    SECRET_KEY = SECRET_KEY

    SQLALCHEMY_DATABASE_URI = (
        SQLALCHEMY_DATABASE_URI
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = (
        SQLALCHEMY_TRACK_MODIFICATIONS
    )

    SQLALCHEMY_ENGINE_OPTIONS = (
        SQLALCHEMY_ENGINE_OPTIONS
    )

    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    ATTACHMENT_ALLOWED_EXTENSIONS = ATTACHMENT_ALLOWED_EXTENSIONS
    ATTACHMENT_MAX_FILES = ATTACHMENT_MAX_FILES
    ATTACHMENT_MAX_FILE_BYTES = ATTACHMENT_MAX_FILE_BYTES
    ATTACHMENT_MAX_TOTAL_BYTES = ATTACHMENT_MAX_TOTAL_BYTES
    VISION_MODEL = VISION_MODEL
    AI_PROVIDER = AI_PROVIDER
    OPENAI_API_KEY = OPENAI_API_KEY
    OPENAI_BASE_URL = OPENAI_BASE_URL
    OPENAI_MODEL = OPENAI_MODEL
    OPENAI_MODELS = OPENAI_MODELS
    OPENROUTER_API_KEY = OPENROUTER_API_KEY
    OPENROUTER_BASE_URL = OPENROUTER_BASE_URL
    OPENROUTER_MODEL = OPENROUTER_MODEL
    OPENROUTER_MODELS = OPENROUTER_MODELS
    GEMINI_API_KEY = GEMINI_API_KEY
    GEMINI_BASE_URL = GEMINI_BASE_URL
    GEMINI_MODEL = GEMINI_MODEL
    GEMINI_MODELS = GEMINI_MODELS
    ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
    ANTHROPIC_BASE_URL = ANTHROPIC_BASE_URL
    ANTHROPIC_VERSION = ANTHROPIC_VERSION
    ANTHROPIC_MODEL = ANTHROPIC_MODEL
    ANTHROPIC_MODELS = ANTHROPIC_MODELS

    EMBEDDING_PROVIDER = EMBEDDING_PROVIDER
    EMBEDDING_MODEL = EMBEDDING_MODEL

    RAG_TOP_K = RAG_TOP_K
    RAG_CHUNK_SIZE = RAG_CHUNK_SIZE
    RAG_CHUNK_OVERLAP = RAG_CHUNK_OVERLAP

    OCR_ENABLED = OCR_ENABLED
    TESSERACT_CMD = TESSERACT_CMD
    OCR_LANGUAGE = OCR_LANGUAGE
    OCR_TESSERACT_CONFIG = (
        OCR_TESSERACT_CONFIG
    )
    OCR_MIN_TEXT_CHARACTERS = (
        OCR_MIN_TEXT_CHARACTERS
    )
    MAX_PDF_PAGES = MAX_PDF_PAGES
    OCR_MAX_PDF_PAGES = OCR_MAX_PDF_PAGES
    OCR_PDF_DPI = OCR_PDF_DPI
    OCR_MAX_IMAGE_PIXELS = (
        OCR_MAX_IMAGE_PIXELS
    )

    WEBSITE_CONNECT_TIMEOUT = WEBSITE_CONNECT_TIMEOUT
    WEBSITE_READ_TIMEOUT = WEBSITE_READ_TIMEOUT
    WEBSITE_MAX_RESPONSE_BYTES = WEBSITE_MAX_RESPONSE_BYTES
    WEBSITE_MAX_REDIRECTS = WEBSITE_MAX_REDIRECTS
    WEBSITE_MAX_TEXT_CHARACTERS = WEBSITE_MAX_TEXT_CHARACTERS
    WEBSITE_MIN_TEXT_CHARACTERS = WEBSITE_MIN_TEXT_CHARACTERS
    WEBSITE_RESPECT_ROBOTS = WEBSITE_RESPECT_ROBOTS
    WEBSITE_USER_AGENT = WEBSITE_USER_AGENT
    WEBSITE_CRAWLER_DEFAULT_MAX_PAGES = WEBSITE_CRAWLER_DEFAULT_MAX_PAGES
    WEBSITE_CRAWLER_MAX_PAGES = WEBSITE_CRAWLER_MAX_PAGES
    WEBSITE_CRAWLER_DEFAULT_DEPTH = WEBSITE_CRAWLER_DEFAULT_DEPTH
    WEBSITE_CRAWLER_MAX_DEPTH = WEBSITE_CRAWLER_MAX_DEPTH
    WEBSITE_CRAWLER_DISCOVERY_BYTES = WEBSITE_CRAWLER_DISCOVERY_BYTES
    WEBSITE_CRAWLER_SITEMAP_BYTES = WEBSITE_CRAWLER_SITEMAP_BYTES
    WEBSITE_CRAWLER_MAX_SITEMAPS = WEBSITE_CRAWLER_MAX_SITEMAPS
    SOCIAL_MAX_MANUAL_CHARACTERS = SOCIAL_MAX_MANUAL_CHARACTERS
    SOCIAL_MIN_TEXT_CHARACTERS = SOCIAL_MIN_TEXT_CHARACTERS
    GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_API_KEY
    GOOGLE_PLACES_LANGUAGE_CODE = GOOGLE_PLACES_LANGUAGE_CODE
    GOOGLE_PLACES_MAX_REVIEWS = GOOGLE_PLACES_MAX_REVIEWS
    WORKSPACE_BACKUP_MAX_MEMBERS = WORKSPACE_BACKUP_MAX_MEMBERS
    WORKSPACE_BACKUP_MAX_UNCOMPRESSED_BYTES = WORKSPACE_BACKUP_MAX_UNCOMPRESSED_BYTES

    LOG_FOLDER = LOG_FOLDER
    LOG_LEVEL = LOG_LEVEL
    LOG_MAX_BYTES = LOG_MAX_BYTES
    LOG_BACKUP_COUNT = LOG_BACKUP_COUNT

    HEALTH_HTTP_TIMEOUT = HEALTH_HTTP_TIMEOUT
    AUTO_CREATE_DATABASE = AUTO_CREATE_DATABASE
    SECURITY_HEADERS_ENABLED = (
        SECURITY_HEADERS_ENABLED
    )
    ENABLE_HSTS = ENABLE_HSTS
    TRUST_PROXY_HEADERS = TRUST_PROXY_HEADERS

    AUTH_REQUIRED = AUTH_REQUIRED
    ALLOW_REGISTRATION = ALLOW_REGISTRATION
    SESSION_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_DURATION = timedelta(
        days=REMEMBER_COOKIE_DAYS
    )
    LOGIN_MAX_ATTEMPTS = LOGIN_MAX_ATTEMPTS
    LOGIN_LOCK_MINUTES = LOGIN_LOCK_MINUTES
    PASSWORD_MIN_LENGTH = PASSWORD_MIN_LENGTH

    METRICS_ENABLED = METRICS_ENABLED
    HEALTH_HISTORY_INTERVAL_SECONDS = HEALTH_HISTORY_INTERVAL_SECONDS
    RATE_LIMIT_ENABLED = RATE_LIMIT_ENABLED
    RATE_LIMIT_CHAT_PER_MINUTE = RATE_LIMIT_CHAT_PER_MINUTE
    RATE_LIMIT_API_PER_MINUTE = RATE_LIMIT_API_PER_MINUTE
    RATE_LIMIT_UPLOADS_PER_10_MINUTES = RATE_LIMIT_UPLOADS_PER_10_MINUTES
    RATE_LIMIT_LOGIN_ATTEMPTS = RATE_LIMIT_LOGIN_ATTEMPTS
    RATE_LIMIT_LOGIN_WINDOW_SECONDS = RATE_LIMIT_LOGIN_WINDOW_SECONDS

    WTF_CSRF_TIME_LIMIT = None

    JSON_SORT_KEYS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    AUTO_CREATE_DATABASE = False


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    AUTO_CREATE_DATABASE = False
    AUTH_REQUIRED = False
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }


def get_config_class():
    if APP_ENV == "production":
        return ProductionConfig

    if APP_ENV == "testing":
        return TestingConfig

    return DevelopmentConfig
