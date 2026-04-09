"""Tests for storage management."""
import pytest
import tempfile
import shutil
from pathlib import Path
from envault.storage import StorageManager
from envault.crypto import CryptoManager


class TestStorageManager:
    """Test cases for StorageManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_config_dir):
        """Create a StorageManager with temporary config directory."""
        return StorageManager(config_dir=temp_config_dir)

    def test_config_dir_creation(self, temp_config_dir):
        """Test that config directory is created."""
        storage = StorageManager(config_dir=temp_config_dir)
        assert temp_config_dir.exists()
        assert temp_config_dir.is_dir()

    def test_save_and_get_project_key(self, storage):
        """Test saving and retrieving a project key."""
        project_path = "/home/user/project"
        key = CryptoManager.generate_key()
        
        storage.save_project_key(project_path, key)
        retrieved = storage.get_project_key(project_path)
        
        assert retrieved is not None
        assert retrieved["key"] == key.decode('utf-8')

    def test_save_project_key_with_salt(self, storage):
        """Test saving a project key with salt."""
        project_path = "/home/user/project"
        key = CryptoManager.generate_key()
        salt = CryptoManager.generate_salt()
        
        storage.save_project_key(project_path, key, salt)
        retrieved = storage.get_project_key(project_path)
        
        assert retrieved is not None
        assert retrieved["key"] == key.decode('utf-8')
        assert retrieved["salt"] == salt.hex()

    def test_get_nonexistent_project_key(self, storage):
        """Test retrieving a key for non-existent project."""
        result = storage.get_project_key("/nonexistent/project")
        assert result is None

    def test_delete_project_key(self, storage):
        """Test deleting a project key."""
        project_path = "/home/user/project"
        key = CryptoManager.generate_key()
        
        storage.save_project_key(project_path, key)
        assert storage.get_project_key(project_path) is not None
        
        deleted = storage.delete_project_key(project_path)
        assert deleted is True
        assert storage.get_project_key(project_path) is None

    def test_delete_nonexistent_key(self, storage):
        """Test deleting a non-existent key."""
        deleted = storage.delete_project_key("/nonexistent/project")
        assert deleted is False

    def test_multiple_projects(self, storage):
        """Test managing keys for multiple projects."""
        project1 = "/home/user/project1"
        project2 = "/home/user/project2"
        key1 = CryptoManager.generate_key()
        key2 = CryptoManager.generate_key()
        
        storage.save_project_key(project1, key1)
        storage.save_project_key(project2, key2)
        
        retrieved1 = storage.get_project_key(project1)
        retrieved2 = storage.get_project_key(project2)
        
        assert retrieved1["key"] == key1.decode('utf-8')
        assert retrieved2["key"] == key2.decode('utf-8')
        assert retrieved1["key"] != retrieved2["key"]
