# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Domain Models and Enums for the Security Subsystem (SOLID: SRP).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """Available user roles in the system."""
    OPERATOR = "OPERATOR"
    SUPERUSER = "SUPERUSER"
    MASTER = "MASTER"

    @classmethod
    def is_valid_assignable_role(cls, role: str) -> bool:
        """Returns True if the role can be assigned to custom users."""
        return role in (cls.OPERATOR.value, cls.SUPERUSER.value)


@dataclass
class User:
    """Represents a registered user identity."""
    username: str
    password_hash: str
    role: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class AuthResult:
    """Encapsulates the result of an authentication attempt."""
    success: bool
    role_or_error: str


@dataclass
class PasswordValidationResult:
    """Encapsulates the validation outcome of a password policy check."""
    is_valid: bool
    errors: list[str]

