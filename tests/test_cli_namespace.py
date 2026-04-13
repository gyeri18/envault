"""Tests for envault.cli_namespace."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_namespace import namespace_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def config_dir(tmp_path):
    return str(tmp_path / ".envault")


def test_create_command_success(runner, config_dir):
    result = runner.invoke(
        namespace_group, ["create", "db", "DB_", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "created" in result.output
    assert "db" in result.output


def test_create_command_duplicate_exits_1(runner, config_dir):
    runner.invoke(namespace_group, ["create", "db", "DB_", "--config-dir", config_dir])
    result = runner.invoke(
        namespace_group, ["create", "db", "DB_", "--config-dir", config_dir]
    )
    assert result.exit_code == 1
    assert "Error" in result.output


def test_delete_command_success(runner, config_dir):
    runner.invoke(namespace_group, ["create", "app", "APP_", "--config-dir", config_dir])
    result = runner.invoke(
        namespace_group, ["delete", "app", "--config-dir", config_dir]
    )
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_missing_exits_1(runner, config_dir):
    result = runner.invoke(
        namespace_group, ["delete", "ghost", "--config-dir", config_dir]
    )
    assert result.exit_code == 1


def test_list_shows_namespaces(runner, config_dir):
    runner.invoke(namespace_group, ["create", "db", "DB_", "--config-dir", config_dir])
    runner.invoke(namespace_group, ["create", "cache", "CACHE_", "--config-dir", config_dir])
    result = runner.invoke(namespace_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "db" in result.output
    assert "cache" in result.output


def test_list_empty_shows_message(runner, config_dir):
    result = runner.invoke(namespace_group, ["list", "--config-dir", config_dir])
    assert result.exit_code == 0
    assert "No namespaces" in result.output
