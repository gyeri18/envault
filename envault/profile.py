"""Profile management for envault — support multiple named profiles per project (e.g. dev, staging, prod)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from envault.exceptions import ProfileError, VaultNotFoundError
from envault.vault import VaultManager


DEFAULT_PROFILE = "default"


class ProfileManager:
    """Manages multiple named env profiles for a single project."""

    def __init__(self, project_name: str, config_dir: Optional[str] = None) -> None:
        self.project_name = project_name
        self.vault = VaultManager(config_dir=config_dir)
        base = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._profiles_dir = base / "profiles" / project_name
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    def _env_path(self, profile: str) -> Path:
        return self._profiles_dir / f"{profile}.env"

    def _vault_path(self, profile: str) -> Path:
        return self._profiles_dir / f"{profile}.vault"

    def list_profiles(self) -> List[str]:
        """Return sorted list of existing profile names."""
        return sorted(
            p.stem for p in self._profiles_dir.glob("*.vault")
        )

    def lock_profile(self, env_file: str, profile: str = DEFAULT_PROFILE,
                     password: Optional[str] = None) -> Path:
        """Encrypt *env_file* under *profile* name and return vault path."""
        vault_path = self._vault_path(profile)
        project_key = f"{self.project_name}:{profile}"
        self.vault.lock(
            env_file=env_file,
            project_name=project_key,
            output_path=str(vault_path),
            password=password,
        )
        return vault_path

    def unlock_profile(self, profile: str = DEFAULT_PROFILE,
                       output_path: Optional[str] = None,
                       password: Optional[str] = None) -> str:
        """Decrypt *profile* vault and return the plaintext content."""
        vault_path = self._vault_path(profile)
        if not vault_path.exists():
            raise VaultNotFoundError(
                f"No vault found for profile '{profile}' in project '{self.project_name}'."
            )
        project_key = f"{self.project_name}:{profile}"
        dest = output_path or str(self._env_path(profile))
        return self.vault.unlock(
            project_name=project_key,
            vault_path=str(vault_path),
            output_path=dest,
            password=password,
        )

    def delete_profile(self, profile: str) -> None:
        """Remove vault (and cached env) for *profile*."""
        if profile == DEFAULT_PROFILE:
            raise ProfileError("Cannot delete the default profile.")
        for path in (self._vault_path(profile), self._env_path(profile)):
            if path.exists():
                path.unlink()
