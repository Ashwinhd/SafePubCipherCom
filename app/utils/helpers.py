"""
CipherVault Pro — Helper Functions
Utility functions for authentication, tokens, and validation.
"""

import secrets
import string
from datetime import datetime, timezone
from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user


def utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def pick_avatar_colour(username: str) -> str:
    """
    Deterministically pick an avatar colour based on username hash.
    Ensures the same user always gets the same colour.
    """
    colours = [
        "#6366f1",  # Indigo
        "#ec4899",  # Pink
        "#f43f5e",  # Rose
        "#f97316",  # Orange
        "#eab308",  # Yellow
        "#22c55e",  # Green
        "#06b6d4",  # Cyan
        "#3b82f6",  # Blue
        "#8b5cf6",  # Violet
        "#d946ef",  # Fuchsia
    ]
    hash_val = sum(ord(c) for c in username)
    return colours[hash_val % len(colours)]


def generate_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    Used for password reset links, message sharing tokens, etc.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a filename has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: Set of allowed extensions (e.g., {'png', 'jpg', 'pdf'})
    
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions
