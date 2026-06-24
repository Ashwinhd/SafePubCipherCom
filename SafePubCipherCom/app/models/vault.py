"""
VaultFile — encrypted files stored per user.
EncryptionLog — audit trail of all encrypt/decrypt operations.
SelfDestructMessage — one-time read or time-expiring messages.
TypingScore — typing trainer results.
"""

from datetime import datetime, timezone
from app import db


class VaultFile(db.Model):
    __tablename__ = "vault_files"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # File metadata
    original_name = db.Column(db.String(256), nullable=False)
    stored_name = db.Column(db.String(256), nullable=False, unique=True)  # UUID-based
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    file_type = db.Column(db.String(64), nullable=True)

    # Encryption metadata
    algorithm = db.Column(db.String(32), nullable=False)  # AES-256, Blowfish, 3DES
    is_steganographic = db.Column(db.Boolean, default=False, nullable=False)

    # Description / notes
    description = db.Column(db.String(512), nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<VaultFile {self.original_name} [{self.algorithm}]>"

    @property
    def size_human(self) -> str:
        """Human-readable file size."""
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class EncryptionLog(db.Model):
    __tablename__ = "encryption_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    operation = db.Column(db.String(16), nullable=False)   # encrypt / decrypt / stego_hide / stego_extract
    algorithm = db.Column(db.String(32), nullable=True)
    file_name = db.Column(db.String(256), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.String(512), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EncryptionLog {self.operation} {self.algorithm} by user {self.user_id}>"


class SelfDestructMessage(db.Model):
    __tablename__ = "self_destruct_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Unique public token (UUID) used in shareable link
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Encrypted content (encrypted with app secret + user passphrase)
    encrypted_content = db.Column(db.Text, nullable=False)
    algorithm = db.Column(db.String(32), nullable=False, default="AES-256")

    # Destruction rules
    max_reads = db.Column(db.Integer, default=1, nullable=False)  # 0 = unlimited
    read_count = db.Column(db.Integer, default=0, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_destroyed = db.Column(db.Boolean, default=False, nullable=False)

    # Metadata
    title = db.Column(db.String(128), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    destroyed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_available(self) -> bool:
        if self.is_destroyed:
            return False
        if self.is_expired:
            return False
        if self.max_reads > 0 and self.read_count >= self.max_reads:
            return False
        return True

    def __repr__(self) -> str:
        return f"<SelfDestructMessage {self.token}>"


class TypingScore(db.Model):
    __tablename__ = "typing_scores"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    wpm = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)  # 0.0 – 100.0
    difficulty = db.Column(db.String(16), nullable=False, default="medium")  # easy / medium / hard
    duration_seconds = db.Column(db.Integer, nullable=False)
    text_snippet = db.Column(db.String(256), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<TypingScore {self.wpm:.1f} WPM {self.accuracy:.1f}% by user {self.user_id}>"
