"""
CipherVault Pro — General helper utilities.
"""

import os
import uuid
import hashlib
import base64
import secrets
from datetime import datetime, timezone
from typing import Optional
from werkzeug.utils import secure_filename
from flask import current_app


# ---------------------------------------------------------------------------
# File utilities
# ---------------------------------------------------------------------------

def allowed_image(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


def allowed_enc_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = current_app.config.get("ALLOWED_ENC_EXTENSIONS", set())
    # Also allow .enc, .bin
    return ext in allowed | {"enc", "bin"}


def save_upload(file_storage, folder: str) -> tuple[str, str]:
    """
    Save a Werkzeug FileStorage object to *folder*.

    Returns (stored_name, full_path) where stored_name is a UUID-based filename.
    """
    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "bin"
    stored = f"{uuid.uuid4().hex}.{ext}"
    full_path = os.path.join(folder, stored)
    file_storage.save(full_path)
    return stored, full_path


def save_bytes(data: bytes, folder: str, ext: str = "enc") -> tuple[str, str]:
    """
    Write raw bytes to *folder*.

    Returns (stored_name, full_path).
    """
    stored = f"{uuid.uuid4().hex}.{ext}"
    full_path = os.path.join(folder, stored)
    with open(full_path, "wb") as f:
        f.write(data)
    return stored, full_path


def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def delete_file(path: str) -> bool:
    try:
        if os.path.exists(path):
            os.remove(path)
            return True
    except OSError:
        pass
    return False


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# Token / secret helpers
# ---------------------------------------------------------------------------

def generate_token(length: int = 48) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token (for DB storage)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------

def paginate(query, page: int, per_page: int = 10):
    """Return a Flask-SQLAlchemy Pagination object."""
    return query.paginate(page=page, per_page=per_page, error_out=False)


# ---------------------------------------------------------------------------
# Avatar colour palette
# ---------------------------------------------------------------------------
AVATAR_COLOURS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
    "#f97316", "#eab308", "#22c55e", "#06b6d4",
]


def pick_avatar_colour(username: str) -> str:
    """Deterministically pick an avatar colour from username."""
    idx = sum(ord(c) for c in username) % len(AVATAR_COLOURS)
    return AVATAR_COLOURS[idx]


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def time_until(dt: Optional[datetime]) -> Optional[str]:
    """Human-readable 'time until' string."""
    if dt is None:
        return None
    now = utcnow()
    if dt <= now:
        return "Expired"
    delta = dt - now
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        return f"{total_seconds // 60}m"
    elif total_seconds < 86400:
        return f"{total_seconds // 3600}h {(total_seconds % 3600) // 60}m"
    else:
        days = total_seconds // 86400
        return f"{days}d {(total_seconds % 86400) // 3600}h"
