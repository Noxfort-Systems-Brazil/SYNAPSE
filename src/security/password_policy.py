# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Password Policy Enforcement & Validation (SOLID: SRP & OCP).
Implements modern security standards aligned with OWASP & NIST guidelines.
"""

import re
import string
from typing import List, Optional

from src.security.interfaces import IPasswordPolicy
from src.security.models import PasswordValidationResult


class ModernPasswordPolicy(IPasswordPolicy):
    """
    Validates password complexity against modern security standards:
    - Minimum 8 characters (up to 128)
    - At least one uppercase character (A-Z)
    - At least one lowercase character (a-z)
    - At least one numeric digit (0-9)
    - At least one special symbol (!@#$%^&*...)
    - No leading or trailing whitespace
    """

    DEFAULT_SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`\"'\\")

    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        disallow_surrounding_whitespace: bool = True,
        allowed_special_chars: Optional[set[str]] = None,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.disallow_surrounding_whitespace = disallow_surrounding_whitespace
        self.allowed_special_chars = (
            allowed_special_chars if allowed_special_chars is not None else self.DEFAULT_SPECIAL_CHARS
        )

    def validate(self, password: str) -> PasswordValidationResult:
        """
        Validates password against all configured complexity requirements.
        Returns a PasswordValidationResult containing is_valid and list of error messages.
        """
        errors: List[str] = []

        if not isinstance(password, str) or not password:
            return PasswordValidationResult(
                is_valid=False,
                errors=["A senha não pode estar vazia."]
            )

        if self.disallow_surrounding_whitespace and (password.startswith(" ") or password.endswith(" ")):
            errors.append("A senha não deve começar nem terminar com espaços.")

        if len(password) < self.min_length:
            errors.append(f"A senha deve conter no mínimo {self.min_length} caracteres.")

        if len(password) > self.max_length:
            errors.append(f"A senha deve conter no máximo {self.max_length} caracteres.")

        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("A senha deve conter pelo menos uma letra maiúscula (A-Z).")

        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("A senha deve conter pelo menos uma letra minúscula (a-z).")

        if self.require_digit and not any(c.isdigit() for c in password):
            errors.append("A senha deve conter pelo menos um número (0-9).")

        if self.require_special:
            has_special = any(c in self.allowed_special_chars for c in password)
            if not has_special:
                errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&*...).")

        return PasswordValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def calculate_strength(self, password: str) -> int:
        """
        Calculates password strength score from 0 (very weak) to 4 (excellent).
        """
        if not password:
            return 0

        score = 0
        if len(password) >= self.min_length:
            score += 1
        if any(c.isupper() for c in password) and any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in self.allowed_special_chars for c in password):
            score += 1

        # Bonus for extra length (>= 12 characters)
        if score == 4 and len(password) >= 12:
            return 4

        return score
