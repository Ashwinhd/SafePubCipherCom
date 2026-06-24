"""
User model — authentication, profile, and relationships.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Profile
    full_name = db.Column(db.String(128), nullable=True)
    avatar_color = db.Column(db.String(7), default="#6366f1")  # hex color for avatar
    bio = db.Column(db.String(256), nullable=True)

    # Security
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    failed_logins = db.Column(db.Integer, default=0, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    reset_token = db.Column(db.String(256), nullable=True)
    reset_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    vault_files = db.relationship(
        "VaultFile", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )
    encrypt_logs = db.relationship(
        "EncryptionLog", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    messages = db.relationship(
        "SelfDestructMessage", backref="creator", lazy="dynamic", cascade="all, delete-orphan"
    )
    typing_scores = db.relationship(
        "TypingScore", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    @property
    def initials(self) -> str:
        if self.full_name:
            parts = self.full_name.split()
            return "".join(p[0].upper() for p in parts[:2])
        return self.username[:2].upper()
