"""Import environment variables from external sources into envault vaults."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.exceptions import EnvaultError, ValidationError
from envault.vault import VaultManager


class ImportManager:
    """Handles importing env vars from dotenv, JSON, or shell-export files."""

    SUPPORTED_FORMATS = ("dotenv", "json", "shell")

    def __init__(self, vault: VaultManager) -> None:
        self._vault = vault

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_file(
        self,
        source: Path,
        project: str,
        fmt: str = "dotenv",
        password: Optional[str] = None,
        overwrite: bool = False,
    ) -> Dict[str, str]:
        """Parse *source* and lock its contents into the vault for *project*.

        Returns the parsed key/value mapping that was stored.
        """
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValidationError(
                f"Unsupported format '{fmt}'. Choose from: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        if not source.exists():
            raise EnvaultError(f"Source file not found: {source}")

        raw = source.read_text(encoding="utf-8")

        parsers = {
            "dotenv": self._parse_dotenv,
            "json": self._parse_json,
            "shell": self._parse_shell,
        }
        mapping = parsers[fmt](raw)

        if not mapping:
            raise ValidationError("Source file contains no valid key=value pairs.")

        # Merge with existing vault content when not overwriting
        if not overwrite:
            try:
                existing = self._vault.unlock(project, password=password)
                existing.update(mapping)
                mapping = existing
            except EnvaultError:
                pass  # No existing vault — that's fine

        env_content = "\n".join(f"{k}={v}" for k, v in mapping.items())
        tmp = source.parent / ".envault_import_tmp"
        try:
            tmp.write_text(env_content, encoding="utf-8")
            self._vault.lock(project, tmp, password=password)
        finally:
            if tmp.exists():
                tmp.unlink()

        return mapping

    # ------------------------------------------------------------------
    # Private parsers
    # ------------------------------------------------------------------

    def _parse_dotenv(self, text: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"\'')
        return result

    def _parse_json(self, text: str) -> Dict[str, str]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValidationError("JSON root must be an object.")
        return {str(k): str(v) for k, v in data.items()}

    def _parse_shell(self, text: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"\'')
        return result
