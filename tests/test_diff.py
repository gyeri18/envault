"""Tests for envault.diff.DiffManager."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from envault.diff import DiffEntry, DiffManager
from envault.exceptions import EnvaultError


VAULT_CONTENT = """DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=old_secret
OLD_VAR=will_be_removed
"""

CURRENT_CONTENT = """DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=new_secret
NEW_VAR=just_added
"""


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(CURRENT_CONTENT)
    return p


@pytest.fixture()
def mock_vault() -> MagicMock:
    vault = MagicMock()
    vault.unlock.return_value = VAULT_CONTENT
    return vault


@pytest.fixture()
def manager(mock_vault: MagicMock) -> DiffManager:
    return DiffManager(vault=mock_vault)


def test_diff_detects_added_key(manager: DiffManager, env_file: Path) -> None:
    entries = manager.diff("myproject", str(env_file))
    statuses = {e.key: e.status for e in entries}
    assert statuses["NEW_VAR"] == "added"


def test_diff_detects_removed_key(manager: DiffManager, env_file: Path) -> None:
    entries = manager.diff("myproject", str(env_file))
    statuses = {e.key: e.status for e in entries}
    assert statuses["OLD_VAR"] == "removed"


def test_diff_detects_changed_key(manager: DiffManager, env_file: Path) -> None:
    entries = manager.diff("myproject", str(env_file))
    statuses = {e.key: e.status for e in entries}
    assert statuses["SECRET_KEY"] == "changed"


def test_diff_detects_unchanged_key(manager: DiffManager, env_file: Path) -> None:
    entries = manager.diff("myproject", str(env_file))
    statuses = {e.key: e.status for e in entries}
    assert statuses["DB_HOST"] == "unchanged"
    assert statuses["DB_PORT"] == "unchanged"


def test_diff_show_values_populates_old_and_new(
    manager: DiffManager, env_file: Path
) -> None:
    entries = manager.diff("myproject", str(env_file), show_values=True)
    changed = next(e for e in entries if e.key == "SECRET_KEY")
    assert changed.old_value == "old_secret"
    assert changed.new_value == "new_secret"


def test_diff_hides_values_by_default(manager: DiffManager, env_file: Path) -> None:
    entries = manager.diff("myproject", str(env_file))
    changed = next(e for e in entries if e.key == "SECRET_KEY")
    assert changed.old_value is None
    assert changed.new_value is None


def test_diff_raises_on_missing_env_file(mock_vault: MagicMock) -> None:
    dm = DiffManager(vault=mock_vault)
    with pytest.raises(EnvaultError, match="Cannot read env file"):
        dm.diff("myproject", "/nonexistent/.env")


def test_diff_raises_when_vault_unlock_fails(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=val\n")
    vault = MagicMock()
    vault.unlock.side_effect = EnvaultError("bad key")
    dm = DiffManager(vault=vault)
    with pytest.raises(EnvaultError, match="Cannot unlock vault for diff"):
        dm.diff("myproject", str(env_file))
