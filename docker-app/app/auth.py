from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any


AUTH_COOKIE = "yahaha_session"
PBKDF2_ITERATIONS = 310_000
DEFAULT_SESSION_DAYS = 180


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def auth_config(config: dict[str, Any]) -> dict[str, Any]:
    value = config.get("auth")
    return value if isinstance(value, dict) else {}


def is_auth_configured(config: dict[str, Any]) -> bool:
    value = auth_config(config)
    return bool(value.get("username") and value.get("password_hash") and value.get("token_secret"))


def hash_password(password: str, *, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_urlsafe(18)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_value}${_b64encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(_b64encode(digest), expected)
    except (TypeError, ValueError):
        return False


def configure_auth(config: dict[str, Any], username: str, password: str) -> dict[str, Any]:
    next_config = dict(config)
    next_config["auth"] = {
        "username": username.strip(),
        "password_hash": hash_password(password),
        "token_secret": secrets.token_urlsafe(48),
        "session_days": DEFAULT_SESSION_DAYS,
    }
    return next_config


def issue_token(config: dict[str, Any], username: str) -> str:
    value = auth_config(config)
    days = max(1, min(3650, int(value.get("session_days") or DEFAULT_SESSION_DAYS)))
    payload = {
        "sub": username,
        "exp": int(time.time()) + days * 86400,
        "nonce": secrets.token_urlsafe(8),
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        str(value.get("token_secret") or "").encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded}.{_b64encode(signature)}"


def verify_token(config: dict[str, Any], token: str) -> str | None:
    value = auth_config(config)
    try:
        encoded, provided = token.split(".", 1)
        expected = hmac.new(
            str(value.get("token_secret") or "").encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_b64encode(expected), provided):
            return None
        payload = json.loads(_b64decode(encoded))
        username = str(payload.get("sub") or "")
        if not username or username != str(value.get("username") or ""):
            return None
        if int(payload.get("exp") or 0) <= int(time.time()):
            return None
        return username
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def request_token(authorization: str | None, cookie_token: str | None) -> str:
    header = str(authorization or "").strip()
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return str(cookie_token or "").strip()
