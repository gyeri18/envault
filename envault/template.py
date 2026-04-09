"""Template management for envault — generate .env templates from vault contents."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envault.exceptions import EnvaultError, VaultNotFoundError
from envault.vault import VaultManager


class TemplateManager:
    """Generate .env.template files with keys but redacted values."""

    REDACTED = "<REDACTED>"

    def __init__(self, vault: VaultManager) -> None:
        self.vault = vault

    def generate(
        self,
        env_file: str | Path,
        output_path: Optional[str | Path] = None,
        project: str = "default",
        password: Optional[str] = None,
    ) -> Path:
        """Unlock the vault and write a template file with redacted values.

        Args:
            env_file: Path to the original .env file (used as output reference).
            output_path: Destination for the template. Defaults to <env_file>.template.
            project: Project name whose key to use for unlocking.
            password: Optional password for key derivation.

        Returns:
            Path to the written template file.
        """
        env_file = Path(env_file)
        if output_path is None:
            output_path = env_file.with_suffix(".template")
        output_path = Path(output_path)

        plaintext = self.vault.unlock(env_file, project=project, password=password)
        template_lines = self._redact(plaintext)

        output_path.write_text("\n".join(template_lines) + "\n", encoding="utf-8")
        return output_path

    def _redact(self, content: str) -> list[str]:
        """Return lines with values replaced by REDACTED placeholder."""
        result: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                result.append(line)
                continue
            if "=" in stripped:
                key, _, _ = stripped.partition("=")
                result.append(f"{key.strip()}={self.REDACTED}")
            else:
                result.append(line)
        return result

    def apply(
        self,
        template_path: str | Path,
        values: dict[str, str],
        output_path: str | Path,
    ) -> Path:
        """Fill a template file with provided values and write a .env file.

        Args:
            template_path: Path to the .env.template file.
            values: Mapping of KEY -> value to substitute.
            output_path: Destination .env file path.

        Returns:
            Path to the written .env file.
        """
        template_path = Path(template_path)
        output_path = Path(output_path)

        if not template_path.exists():
            raise EnvaultError(f"Template file not found: {template_path}")

        lines: list[str] = []
        for line in template_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key, _, val = stripped.partition("=")
                key = key.strip()
                if val == self.REDACTED and key in values:
                    lines.append(f"{key}={values[key]}")
                    continue
            lines.append(line)

        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path
