import re
from typing import Tuple, List

class Validator:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        if not re.match(r'^[a-zA-Z0-9_-]+', username):
            return False, "Username can only contain letters, numbers, underscores and hyphens"
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        return True, ""
    
    @staticmethod
    def validate_script_name(name: str) -> Tuple[bool, str]:
        if not name or len(name.strip()) == 0:
            return False, "Script name cannot be empty"
        if len(name) > 255:
            return False, "Script name too long"
        if not re.match(r'^[a-zA-Z0-9\s_-]+', name):
            return False, "Script name contains invalid characters"
        return True, ""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text.strip()