"""Tag management for envault projects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.exceptions import EnvaultError


class TagManager:
    """Manage tags associated with envault projects."""

    TAGS_FILE = "tags.json"

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".envault"
        self._ensure_config_dir()
        self._tags_path = self.config_dir / self.TAGS_FILE

    def _ensure_config_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, List[str]]:
        if not self._tags_path.exists():
            return {}
        with self._tags_path.open("r") as fh:
            return json.load(fh)

    def _save(self, data: Dict[str, List[str]]) -> None:
        with self._tags_path.open("w") as fh:
            json.dump(data, fh, indent=2)

    def add_tag(self, project: str, tag: str) -> None:
        """Add a tag to a project. Raises EnvaultError if tag already exists."""
        if not project or not tag:
            raise EnvaultError("Project name and tag must be non-empty strings.")
        data = self._load()
        tags = data.setdefault(project, [])
        if tag in tags:
            raise EnvaultError(f"Tag '{tag}' already exists for project '{project}'.")
        tags.append(tag)
        self._save(data)

    def remove_tag(self, project: str, tag: str) -> None:
        """Remove a tag from a project. Raises EnvaultError if tag not found."""
        data = self._load()
        tags = data.get(project, [])
        if tag not in tags:
            raise EnvaultError(f"Tag '{tag}' not found for project '{project}'.")
        tags.remove(tag)
        if not tags:
            del data[project]
        self._save(data)

    def get_tags(self, project: str) -> List[str]:
        """Return all tags for a project."""
        return list(self._load().get(project, []))

    def find_projects_by_tag(self, tag: str) -> List[str]:
        """Return all projects that have the given tag."""
        return [proj for proj, tags in self._load().items() if tag in tags]

    def list_all(self) -> Dict[str, List[str]]:
        """Return the full project->tags mapping."""
        return dict(self._load())

    def rename_tag(self, project: str, old_tag: str, new_tag: str) -> None:
        """Rename a tag for a project.

        Raises EnvaultError if the old tag does not exist, if the new tag name
        is empty, or if the new tag already exists on the project.
        """
        if not new_tag:
            raise EnvaultError("New tag name must be a non-empty string.")
        data = self._load()
        tags = data.get(project, [])
        if old_tag not in tags:
            raise EnvaultError(f"Tag '{old_tag}' not found for project '{project}'.")
        if new_tag in tags:
            raise EnvaultError(f"Tag '{new_tag}' already exists for project '{project}'.")
        tags[tags.index(old_tag)] = new_tag
        self._save(data)
