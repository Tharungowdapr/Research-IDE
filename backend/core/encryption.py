"""
API Key Encryption/Decryption Utility
Provides secure storage for sensitive API keys using Fernet (AES-128)
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from core.config import settings


class APIKeyEncryption:
    """Handles encryption and decryption of API keys"""
    
    def __init__(self):
        """Initialize encryption key from settings"""
        # Use ENCRYPTION_KEY from settings or generate one
        key_material = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else os.environ.get('ENCRYPTION_KEY', 'default-key-change-in-production').encode()
        
        # Derive a 32-byte key from the key material using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'researchide_salt',  # In production, use a random salt stored securely
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_material))
        self.cipher = Fernet(derived_key)
    
    def encrypt(self, api_key: str) -> str:
        """
        Encrypt an API key
        
        Args:
            api_key: The plain text API key
            
        Returns:
            Base64-encoded encrypted key
        """
        if not api_key:
            return ""
        
        encrypted = self.cipher.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """
        Decrypt an API key
        
        Args:
            encrypted_key: Base64-encoded encrypted key
            
        Returns:
            Plain text API key
        """
        if not encrypted_key:
            return ""
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")


# Global instance
_encryption = None

def get_encryption() -> APIKeyEncryption:
    """Get or create the encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = APIKeyEncryption()
    return _encryption


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key (convenience function)"""
    return get_encryption().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key (convenience function)"""
    return get_encryption().decrypt(encrypted_key)
