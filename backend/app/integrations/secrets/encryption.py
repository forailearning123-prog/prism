"""
Encryption Service
Provides encryption/decryption for sensitive data at rest.
"""

from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    Uses Fernet symmetric encryption for simplicity and security.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            encryption_key: Base64-encoded 32-byte key. If not provided,
                          will use ENCRYPTION_KEY environment variable.
                          Must be set in production!
        """
        if encryption_key:
            self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # Try to get from environment
            env_key = os.getenv("ENCRYPTION_KEY")
            if env_key:
                self.key = env_key.encode()
            else:
                # Generate a new key (for development only - not secure for production)
                self.key = Fernet.generate_key()
                print("WARNING: Generated temporary encryption key. Set ENCRYPTION_KEY in production!")
        
        self.fernet = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string.
        
        Args:
            data: Plain text to encrypt
            
        Returns:
            Encrypted string (base64-encoded)
        """
        if not data:
            return ""
        
        encrypted = self.fernet.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string.
        
        Args:
            encrypted_data: Encrypted string to decrypt
            
        Returns:
            Decrypted plain text
        """
        if not encrypted_data:
            return ""
        
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_dict(self, data: dict) -> str:
        """
        Encrypt a dictionary by converting to JSON and encrypting.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted string
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt a dictionary.
        
        Args:
            encrypted_data: Encrypted string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """
        Derive an encryption key from a password.
        
        Args:
            password: Password to derive key from
            salt: Salt bytes (generated if not provided)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt