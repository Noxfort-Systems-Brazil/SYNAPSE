# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Password Hashing and Cryptographic Services (SOLID: SRP & OCP).
"""

import os
import hashlib
import binascii
from typing import Optional

from src.security.interfaces import IPasswordHasher


class Pbkdf2PasswordHasher(IPasswordHasher):
    """
    Password hashing strategy using PBKDF2 HMAC SHA-256 with 100,000 iterations.
    Serializes format as 'hex_salt:hex_digest'.
    """

    def __init__(self, iterations: int = 100000, salt_length: int = 16):
        self.iterations = iterations
        self.salt_length = salt_length

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        """Hashes a password with a random or provided salt."""
        if salt is None:
            salt = os.urandom(self.salt_length)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return f"{binascii.hexlify(salt).decode('utf-8')}:{binascii.hexlify(pwd_hash).decode('utf-8')}"

    def verify_password(self, password: str, stored_hash_str: str) -> bool:
        """Verifies a plain password against a stored 'salt:hash' string."""
        try:
            salt_hex, hash_hex = stored_hash_str.split(":")
            salt = binascii.unhexlify(salt_hex)
            stored_hash = binascii.unhexlify(hash_hex)
            new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
            return new_hash == stored_hash
        except Exception:
            return False


class Sha256Hasher:
    """
    Lightweight SHA-256 hasher used for master superuser fallback verification.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Computes hexadecimal SHA-256 digest of password string."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @classmethod
    def verify_password(cls, password: str, expected_hash: str) -> bool:
        """Verifies if sha256(password) matches expected hash."""
        return cls.hash_password(password) == expected_hash
