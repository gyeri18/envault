"""Sort and organize .env file keys alphabetically or by custom group order."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from envault.exceptions import EnvaultError


class SortManager:
    """Manages sorting of .env file keys."""

    def __init__(self, env_path: Path) -> None:
        self.env_path = Path(env_path)

    def _parse_lines(
        self, content: str
    ) -> List[Tuple[str, str]]:
        """Return list of (raw_line, sort_key) tuples."""
        result: List[Tuple[str, str]] = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                result.append((line, ""))
            elif "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                result.append((line, key))
            else:
                result.append((line, ""))
        return result

    def sort(
        self,
        *,
        groups: Optional[List[str]] = None,
        reverse: bool = False,
        dry_run: bool = False,
    ) -> str:
        """Sort .env keys alphabetically or by prefix groups.

        Args:
            groups: Optional list of key prefixes defining section order.
            reverse: If True, sort in descending order.
            dry_run: If True, return sorted content without writing.

        Returns:
            The sorted file content as a string.
        """
        if not self.env_path.exists():
            raise EnvaultError(f"File not found: {self.env_path}")

        content = self.env_path.read_text(encoding="utf-8")
        pairs = self._parse_lines(content)

        # Separate blank/comment lines from key=value lines
        kv_lines = [(line, key) for line, key in pairs if key]
        other_lines = [line for line, key in pairs if not key]

        if groups:
            def group_order(item: Tuple[str, str]) -> Tuple[int, str]:
                key = item[1]
                for idx, prefix in enumerate(groups):
                    if key.startswith(prefix):
                        return (idx, key)
                return (len(groups), key)

            kv_lines.sort(key=group_order, reverse=reverse)
        else:
            kv_lines.sort(key=lambda x: x[1], reverse=reverse)

        sorted_content = "\n".join(line for line, _ in kv_lines) + "\n"

        if not dry_run:
            self.env_path.write_text(sorted_content, encoding="utf-8")

        return sorted_content

    def is_sorted(self) -> bool:
        """Return True if the file keys are already in alphabetical order."""
        if not self.env_path.exists():
            raise EnvaultError(f"File not found: {self.env_path}")
        content = self.env_path.read_text(encoding="utf-8")
        pairs = self._parse_lines(content)
        keys = [key for _, key in pairs if key]
        return keys == sorted(keys)
