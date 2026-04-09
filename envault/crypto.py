"""Cryptographic operations for envault."""
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64


class CryptoManager:
    """Handles encryption and decryption of .env files."""

    def __init__(self, project_key: bytes = None):
        """Initialize crypto manager with a project key.
        
        Args:
            project_key: The encryption key for the project. If None, generates new key.
        """
        self.key = project_key if project_key else self.generate_key()
        self.cipher = Fernet(self.key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new Fernet encryption key.
        
        Returns:
            A new Fernet key as bytes.
        """
        return Fernet.generate_key()

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: The password to derive key from.
            salt: Salt for key derivation.
            
        Returns:
            A Fernet-compatible key derived from the password.
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt plaintext data.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Encrypted data as bytes.
        """
        return self.cipher.encrypt(plaintext.encode())

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt ciphertext data.
        
        Args:
            ciphertext: The encrypted bytes to decrypt.
            
        Returns:
            Decrypted string.
        """
        return self.cipher.decrypt(ciphertext).decode()

    @staticmethod
    def generate_salt() -> bytes:
        """Generate a random salt for key derivation.
        
        Returns:
            16 bytes of random data.
        """
        return os.urandom(16)
