"""Export decrypted .env contents to various formats."""

import json
from pathlib import Path
from typing import Dict, Optional

from envault.exceptions import ExportError, VaultNotFoundError
from envault.vault import VaultManager


class ExportManager:
    """Handles exporting decrypted vault contents to different formats."""

    SUPPORTED_FORMATS = ("dotenv", "json", "shell")

    def __init__(self, vault: VaultManager):
        self.vault = vault

    def export(
        self,
        project_name: str,
        fmt: str = "dotenv",
        password: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """Decrypt vault and return contents in the requested format."""
        if fmt not in self.SUPPORTED_FORMATS:
            raise ExportError(
                f"Unsupported format '{fmt}'. Choose from: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        env_path = self.vault.unlock(project_name, password=password)
        if not env_path.exists():
            raise VaultNotFoundError(f"No unlocked env found for project '{project_name}'")

        pairs = self._parse_env_file(env_path)

        if fmt == "dotenv":
            result = self._to_dotenv(pairs)
        elif fmt == "json":
            result = self._to_json(pairs)
        elif fmt == "shell":
            result = self._to_shell(pairs)

        if output_path:
            output_path.write_text(result)

        return result

    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        pairs: Dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
        return pairs

    def _to_dotenv(self, pairs: Dict[str, str]) -> str:
        return "\n".join(f"{k}={v}" for k, v in pairs.items()) + "\n"

    def _to_json(self, pairs: Dict[str, str]) -> str:
        return json.dumps(pairs, indent=2) + "\n"

    def _to_shell(self, pairs: Dict[str, str]) -> str:
        return "\n".join(f"export {k}={v}" for k, v in pairs.items()) + "\n"
