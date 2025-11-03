from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os

class EncryptionService:
    def __init__(self):
        encryption_key = os.getenv("ENCRYPTION_KEY", "your-encryption-key-32-chars")
        
        # Derive a proper Fernet key from the encryption key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'opscraft_salt',  # In production, use a random salt per secret
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string"""
        encrypted = self.fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt encrypted string"""
        decoded = base64.urlsafe_b64decode(encrypted.encode())
        decrypted = self.fernet.decrypt(decoded)
        return decrypted.decode()