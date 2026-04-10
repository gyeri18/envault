"""Copy .env files between profiles or paths with optional key filtering."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envault.exceptions import EnvaultError


class CopyManager:
    """Copy environment variables between files with optional key filtering."""

    def __init__(self, base_dir: Path = Path(".")) -> None:
        self.base_dir = Path(base_dir)

    def _parse_env_file(self, path: Path) -> dict[str, str]:
        """Parse a .env file into a key/value dict, ignoring comments and blanks."""
        if not path.exists():
            raise EnvaultError(f"Source file not found: {path}")
        pairs: dict[str, str] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
        return pairs

    def _write_env_file(self, path: Path, pairs: dict[str, str]) -> None:
        """Write key/value pairs to a .env file."""
        lines = [f"{k}={v}" for k, v in pairs.items()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""))

    def copy(
        self,
        src: Path,
        dst: Path,
        keys: Optional[List[str]] = None,
        overwrite: bool = True,
    ) -> List[str]:
        """Copy env vars from *src* to *dst*.

        Args:
            src: Source .env file path.
            dst: Destination .env file path.
            keys: If provided, only these keys are copied. ``None`` copies all.
            overwrite: When ``True`` existing keys in *dst* are overwritten;
                       when ``False`` existing keys are preserved.

        Returns:
            List of key names that were actually written.
        """
        src_pairs = self._parse_env_file(src)

        if keys is not None:
            missing = [k for k in keys if k not in src_pairs]
            if missing:
                raise EnvaultError(
                    f"Keys not found in source: {', '.join(missing)}"
                )
            src_pairs = {k: src_pairs[k] for k in keys}

        dst_pairs: dict[str, str] = {}
        if dst.exists():
            dst_pairs = self._parse_env_file(dst)

        written: List[str] = []
        for k, v in src_pairs.items():
            if not overwrite and k in dst_pairs:
                continue
            dst_pairs[k] = v
            written.append(k)

        self._write_env_file(dst, dst_pairs)
        return written
