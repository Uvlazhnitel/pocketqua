from cryptography.fernet import Fernet

from app.config import get_settings


def _get_cipher() -> Fernet:
    key = get_settings().encryption_key
    if not key:
        raise ValueError("ENCRYPTION_KEY is not configured")
    return Fernet(key.encode())


def encrypt_secret(value: str) -> str:
    return _get_cipher().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    if value.startswith("plain:"):
        return value.split("plain:", 1)[1]
    return _get_cipher().decrypt(value.encode()).decode()
