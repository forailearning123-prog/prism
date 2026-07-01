import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet

from app.config import get_settings


def _build_fernet() -> Fernet:
    secret = get_settings().secret_key.encode("utf-8")
    key = hashlib.sha256(secret).digest()
    token = base64.urlsafe_b64encode(key)
    return Fernet(token)


def encrypt_sensitive_payload(data: dict[str, Any]) -> str:
    encrypted = _build_fernet().encrypt(json.dumps(data).encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_sensitive_payload(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    decrypted = _build_fernet().decrypt(value.encode("utf-8"))
    return json.loads(decrypted.decode("utf-8"))
