# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import hashlib
from typing import Tuple


class MasterCredentialValidator:
    """
    Validates master and default emergency credentials using SHA-256 digests.
    Decoupled from user storage and account lifecycles.
    """

    def __init__(
        self,
        master_user: str,
        master_hash: str,
        default_user: str,
        default_hash: str,
    ):
        self.master_user = master_user
        self.master_hash = master_hash
        self.default_user = default_user
        self.default_hash = default_hash

    def is_protected_master(self, username: str) -> bool:
        """Returns True if the username matches any protected master identity."""
        return username in (self.master_user, self.default_user)

    def verify_master(self, username: str, password: str) -> Tuple[bool, bool]:
        """
        Verifies credentials against master identities.
        Returns:
            (is_authenticated_master, is_master_attempt)
            - is_authenticated_master: True if username matches master and hash matches.
            - is_master_attempt: True if username matches master regardless of password.
        """
        if not self.is_protected_master(username):
            return False, False

        raw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if username == self.master_user and raw_hash == self.master_hash:
            return True, True
        if username == self.default_user and raw_hash == self.default_hash:
            return True, True

        return False, True
