"""Security utilities: password hashing, session tokens, and tool authentication.

Uses Python standard library (hashlib, hmac, secrets) without adding extra dependencies.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional

from pathlib import Path
from dotenv import load_dotenv

# Constant configuration
PBKDF2_ITERATIONS = 100_000
HASH_ALGO = "sha256"

# Load .env from project root
ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_tool_token() -> str:
    """Retrieve PRIYA_TOOL_TOKEN from environment. Returns empty string if unset."""
    load_dotenv(dotenv_path=ENV_PATH, override=False)
    return os.environ.get("PRIYA_TOOL_TOKEN", "").strip()



def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        HASH_ALGO,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2:{HASH_ALGO}:{PBKDF2_ITERATIONS}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password in constant time against PBKDF2 hash format."""
    try:
        header, salt, expected_hex = hashed_password.split("$")
        algo, iterations_str = header.split(":")[1:]
        iterations = int(iterations_str)

        key = hashlib.pbkdf2_hmac(
            algo,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate cryptographically secure 256-bit URL-safe token."""
    return secrets.token_urlsafe(32)


def verify_tool_token(header_value: Optional[str]) -> bool:
    """
    Validate incoming Authorization header for Bolna custom tool calls in constant time.
    Expected: 'Bearer <PRIYA_TOOL_TOKEN>'
    Fails safely (returns False) if PRIYA_TOOL_TOKEN is empty or missing.
    """
    expected_token = get_tool_token()
    if not expected_token:
        # Safe failure: missing token fails closed
        return False

    if not header_value:
        return False
    
    parts = header_value.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    
    token = parts[1]
    return hmac.compare_digest(token, expected_token)

