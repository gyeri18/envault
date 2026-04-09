"""Storage management for envault keys and encrypted files."""
import os
import json
from pathlib import Path
from typing import Optional, Dict


class StorageManager:
    """Manages storage of encryption keys and project configurations."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize storage manager.
        
        Args:
            config_dir: Directory for storing envault configuration.
                       Defaults to ~/.envault
        """
        self.config_dir = config_dir or Path.home() / ".envault"
        self.keys_file = self.config_dir / "keys.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Set restrictive permissions on config directory
        os.chmod(self.config_dir, 0o700)

    def save_project_key(self, project_path: str, key: bytes, salt: bytes = None) -> None:
        """Save encryption key for a project.
        
        Args:
            project_path: Absolute path to the project.
            key: The encryption key to store.
            salt: Optional salt used for key derivation.
        """
        keys_data = self._load_keys_data()
        
        project_data = {
            "key": key.decode('utf-8'),
        }
        
        if salt:
            project_data["salt"] = salt.hex()
        
        keys_data[project_path] = project_data
        self._save_keys_data(keys_data)

    def get_project_key(self, project_path: str) -> Optional[Dict[str, str]]:
        """Retrieve encryption key for a project.
        
        Args:
            project_path: Absolute path to the project.
            
        Returns:
            Dictionary containing 'key' and optionally 'salt', or None if not found.
        """
        keys_data = self._load_keys_data()
        return keys_data.get(project_path)

    def _load_keys_data(self) -> Dict:
        """Load keys data from storage."""
        if not self.keys_file.exists():
            return {}
        
        with open(self.keys_file, 'r') as f:
            return json.load(f)

    def _save_keys_data(self, data: Dict) -> None:
        """Save keys data to storage."""
        with open(self.keys_file, 'w') as f:
            json.dump(data, f, indent=2)
        # Set restrictive permissions on keys file
        os.chmod(self.keys_file, 0o600)

    def delete_project_key(self, project_path: str) -> bool:
        """Delete encryption key for a project.
        
        Args:
            project_path: Absolute path to the project.
            
        Returns:
            True if key was deleted, False if not found.
        """
        keys_data = self._load_keys_data()
        if project_path in keys_data:
            del keys_data[project_path]
            self._save_keys_data(keys_data)
            return True
        return False
