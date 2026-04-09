"""Search and filter functionality for vault entries."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, List, Optional

from envault.exceptions import VaultError
from envault.vault import VaultManager


class SearchManager:
    """Search and filter decrypted environment variables."""

    def __init__(self, vault: VaultManager) -> None:
        self.vault = vault

    def search(
        self,
        project: str,
        pattern: str,
        *,
        key: Optional[bytes] = None,
        password: Optional[str] = None,
        use_regex: bool = False,
        keys_only: bool = False,
    ) -> Dict[str, str]:
        """Search vault entries by key name pattern.

        Args:
            project: Project name whose vault to search.
            pattern: Glob or regex pattern to match against variable names.
            key: Raw encryption key (mutually exclusive with password).
            password: Password to derive key from.
            use_regex: Treat *pattern* as a regular expression.
            keys_only: Return only matching keys with empty string values.

        Returns:
            Dict of matching key/value pairs.
        """
        entries = self.vault.unlock(project, key=key, password=password)

        if use_regex:
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                raise VaultError(f"Invalid regex pattern: {exc}") from exc
            matches = {
                k: v for k, v in entries.items() if compiled.search(k)
            }
        else:
            matches = {
                k: v
                for k, v in entries.items()
                if fnmatch.fnmatch(k, pattern)
            }

        if keys_only:
            return {k: "" for k in matches}

        return matches

    def list_keys(self, project: str, *, key: Optional[bytes] = None, password: Optional[str] = None) -> List[str]:
        """Return sorted list of all variable names in the vault."""
        entries = self.vault.unlock(project, key=key, password=password)
        return sorted(entries.keys())
