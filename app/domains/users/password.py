"""
Password hashing - framework agnostic domain utility.

Uses Argon2 (via pwdlib) which is the current OWASP-recommended password hashing
algorithm. Verification is constant-time and handled by the underlying library.
"""

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _password_hash.verify(plain_password, password_hash)
