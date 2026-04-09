"""Tests for cryptographic operations."""
import pytest
from envault.crypto import CryptoManager


class TestCryptoManager:
    """Test cases for CryptoManager."""

    def test_generate_key(self):
        """Test key generation."""
        key = CryptoManager.generate_key()
        assert isinstance(key, bytes)
        assert len(key) == 44  # Fernet keys are 44 bytes when base64 encoded

    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption."""
        crypto = CryptoManager()
        plaintext = "SECRET_KEY=mysecret123\nAPI_TOKEN=abc123"
        
        encrypted = crypto.encrypt(plaintext)
        assert isinstance(encrypted, bytes)
        assert encrypted != plaintext.encode()
        
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == plaintext

    def test_different_keys_produce_different_results(self):
        """Test that different keys produce different encrypted outputs."""
        plaintext = "SECRET=test"
        
        crypto1 = CryptoManager()
        crypto2 = CryptoManager()
        
        encrypted1 = crypto1.encrypt(plaintext)
        encrypted2 = crypto2.encrypt(plaintext)
        
        assert encrypted1 != encrypted2

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption fails with wrong key."""
        plaintext = "SECRET=test"
        
        crypto1 = CryptoManager()
        crypto2 = CryptoManager()
        
        encrypted = crypto1.encrypt(plaintext)
        
        with pytest.raises(Exception):
            crypto2.decrypt(encrypted)

    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        password = "my_secure_password"
        salt = CryptoManager.generate_salt()
        
        key1 = CryptoManager.derive_key_from_password(password, salt)
        key2 = CryptoManager.derive_key_from_password(password, salt)
        
        assert key1 == key2
        assert isinstance(key1, bytes)

    def test_different_salts_produce_different_keys(self):
        """Test that different salts produce different keys."""
        password = "my_secure_password"
        salt1 = CryptoManager.generate_salt()
        salt2 = CryptoManager.generate_salt()
        
        key1 = CryptoManager.derive_key_from_password(password, salt1)
        key2 = CryptoManager.derive_key_from_password(password, salt2)
        
        assert key1 != key2

    def test_generate_salt(self):
        """Test salt generation."""
        salt = CryptoManager.generate_salt()
        assert isinstance(salt, bytes)
        assert len(salt) == 16
