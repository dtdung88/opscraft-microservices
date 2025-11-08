from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import os
import secrets

class EncryptionHelper:
    @staticmethod
    def generate_key() -> bytes:
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_value(value: str, key: bytes) -> str:
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt_value(encrypted_value: str, key: bytes) -> str:
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = f.decrypt(decoded)
        return decrypted.decode()
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_value(value: str) -> str:
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()
