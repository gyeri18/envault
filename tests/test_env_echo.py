"""Tests for envault.env_echo."""
import pytest
from pathlib import Path

from envault.env_echo import EchoManager, EchoResult, EchoError


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def env_file(tmp_dir: Path) -> Path:
    return _write(
        tmp_dir / ".env",
        "DB_HOST=localhost\nDB_PASSWORD=s3cr3t\nAPP_NAME=myapp\n# comment\nNO_VALUE\n",
    )


@pytest.fixture
def manager(env_file: Path) -> EchoManager:
    return EchoManager(env_file)


def test_echo_returns_all_pairs(manager: EchoManager) -> None:
    result = manager.echo()
    assert result.pairs == {"DB_HOST": "localhost", "DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}


def test_echo_selected_keys(manager: EchoManager) -> None:
    result = manager.echo(keys=["DB_HOST", "APP_NAME"])
    assert list(result.pairs.keys()) == ["DB_HOST", "APP_NAME"]


def test_echo_missing_key_raises(manager: EchoManager) -> None:
    with pytest.raises(EchoError, match="MISSING_KEY"):
        manager.echo(keys=["MISSING_KEY"])


def test_echo_mask_all(manager: EchoManager) -> None:
    result = manager.echo(mask=True)
    assert set(result.masked_keys) == set(result.pairs.keys())
    text = result.as_text()
    assert "s3cr3t" not in text
    assert "localhost" not in text


def test_echo_auto_mask_detects_password(manager: EchoManager) -> None:
    result = manager.echo(auto_mask=True)
    assert "DB_PASSWORD" in result.masked_keys
    assert "DB_HOST" not in result.masked_keys


def test_echo_explicit_mask_keys(manager: EchoManager) -> None:
    result = manager.echo(mask_keys=["APP_NAME"])
    assert "APP_NAME" in result.masked_keys
    assert "DB_HOST" not in result.masked_keys


def test_as_text_format(manager: EchoManager) -> None:
    result = manager.echo(keys=["DB_HOST"])
    assert result.as_text() == "DB_HOST=localhost"


def test_as_export_format(manager: EchoManager) -> None:
    result = manager.echo(keys=["APP_NAME"])
    assert result.as_export() == "export APP_NAME=myapp"


def test_as_text_masked_value(manager: EchoManager) -> None:
    result = manager.echo(keys=["DB_PASSWORD"], mask_keys=["DB_PASSWORD"])
    assert result.as_text() == "DB_PASSWORD=****"


def test_missing_file_raises(tmp_dir: Path) -> None:
    mgr = EchoManager(tmp_dir / "nonexistent.env")
    with pytest.raises(EchoError, match="not found"):
        mgr.echo()


def test_echo_result_type(manager: EchoManager) -> None:
    result = manager.echo()
    assert isinstance(result, EchoResult)
