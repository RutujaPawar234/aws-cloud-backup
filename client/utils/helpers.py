"""Small formatting helpers for the UI."""
from __future__ import annotations

from datetime import datetime


def format_size(num_bytes: int) -> str:
    """Human-readable file size, e.g. 4.2 MB."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_date(iso_string: str) -> str:
    """Turn an ISO timestamp into e.g. 07-Oct-2026."""
    if not iso_string:
        return "-"
    try:
        cleaned = iso_string.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).strftime("%d-%b-%Y")
    except ValueError:
        return iso_string[:10]


def is_valid_email(email: str) -> bool:
    """Very light email sanity check for the client side."""
    email = email.strip()
    return "@" in email and "." in email.split("@")[-1] and len(email) >= 5
