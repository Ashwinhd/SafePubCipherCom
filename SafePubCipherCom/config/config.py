"""
CipherVault Pro — Application Configuration
Handles development, testing, and production environments.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "cv-super-secret-key-change-in-production-32chars!")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    VAULT_FOLDER = os.path.join(BASE_DIR, "vault")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}
    ALLOWED_ENC_EXTENSIONS = {"txt", "pdf", "docx", "csv", "json", "xml"}

    # Encryption defaults
    PBKDF2_ITERATIONS = 200_000
    PBKDF2_SALT_LEN = 32
    DEFAULT_ALGORITHM = "AES-256"

    # Self-destruct message defaults
    MAX_DESTRUCT_HOURS = 168  # 7 days
    DEFAULT_DESTRUCT_HOURS = 24

    # Typing trainer
    TYPING_TEXTS = [
        "The quick brown fox jumps over the lazy dog.",
        "Cryptography is the practice of securing communications.",
        "Encryption transforms readable data into an unreadable format.",
        "A strong password is your first line of defense.",
        "Steganography hides secret information inside ordinary files.",
    ]

    # Mail (optional — for password reset)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@ciphervault.local")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DEV_DATABASE_URL")
        or f"sqlite:///{os.path.join(BASE_DIR, 'ciphervault_dev.db')}"
    )


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{os.path.join(BASE_DIR, 'ciphervault.db')}"
    )
    PBKDF2_ITERATIONS = 300_000


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
