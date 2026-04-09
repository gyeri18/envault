"""Tests for envault.tags.TagManager."""
from __future__ import annotations

import pytest

from envault.exceptions import EnvaultError
from envault.tags import TagManager


@pytest.fixture
def manager(tmp_path):
    return TagManager(config_dir=tmp_path)


class TestTagManager:
    def test_add_tag_creates_entry(self, manager):
        manager.add_tag("myproject", "production")
        assert "production" in manager.get_tags("myproject")

    def test_add_multiple_tags(self, manager):
        manager.add_tag("myproject", "production")
        manager.add_tag("myproject", "us-east")
        tags = manager.get_tags("myproject")
        assert "production" in tags
        assert "us-east" in tags

    def test_add_duplicate_tag_raises(self, manager):
        manager.add_tag("myproject", "staging")
        with pytest.raises(EnvaultError, match="already exists"):
            manager.add_tag("myproject", "staging")

    def test_add_empty_project_raises(self, manager):
        with pytest.raises(EnvaultError):
            manager.add_tag("", "sometag")

    def test_add_empty_tag_raises(self, manager):
        with pytest.raises(EnvaultError):
            manager.add_tag("myproject", "")

    def test_remove_tag(self, manager):
        manager.add_tag("myproject", "production")
        manager.remove_tag("myproject", "production")
        assert manager.get_tags("myproject") == []

    def test_remove_last_tag_removes_project_key(self, manager):
        manager.add_tag("myproject", "onlytag")
        manager.remove_tag("myproject", "onlytag")
        assert "myproject" not in manager.list_all()

    def test_remove_nonexistent_tag_raises(self, manager):
        with pytest.raises(EnvaultError, match="not found"):
            manager.remove_tag("myproject", "ghost")

    def test_get_tags_unknown_project_returns_empty(self, manager):
        assert manager.get_tags("unknown") == []

    def test_find_projects_by_tag(self, manager):
        manager.add_tag("proj_a", "prod")
        manager.add_tag("proj_b", "staging")
        manager.add_tag("proj_c", "prod")
        result = manager.find_projects_by_tag("prod")
        assert set(result) == {"proj_a", "proj_c"}

    def test_find_projects_by_nonexistent_tag_returns_empty(self, manager):
        assert manager.find_projects_by_tag("nope") == []

    def test_list_all_returns_full_mapping(self, manager):
        manager.add_tag("alpha", "v1")
        manager.add_tag("beta", "v2")
        data = manager.list_all()
        assert data == {"alpha": ["v1"], "beta": ["v2"]}

    def test_persistence_across_instances(self, tmp_path):
        m1 = TagManager(config_dir=tmp_path)
        m1.add_tag("myproject", "persistent")
        m2 = TagManager(config_dir=tmp_path)
        assert "persistent" in m2.get_tags("myproject")
