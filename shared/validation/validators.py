"""Comprehensive input validation and sanitization"""
import html
import logging
import re
import urllib.parse
from enum import Enum
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of validation with detailed feedback"""

    def __init__(self, valid: bool, message: str = "", errors: List[str] = None):
        self.valid = valid
        self.message = message
        self.errors = errors or []

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        return {"valid": self.valid, "message": self.message, "errors": self.errors}


class SecurityPatterns:
    """Dangerous patterns to detect"""

    DANGEROUS_PATTERNS = {
        "sql_injection": [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b.*\b(FROM|INTO|TABLE)\b)",
            r"(--|#|\/\*|\*\/)",
            r"(\bOR\b.*=.*|AND.*=.*)",
        ],
        "command_injection": [
            r"[;&|`$(){}[\]<>]",
            r"(bash|sh|cmd|powershell|eval|exec)\s*['\"]",
        ],
        "path_traversal": [
            r"\.\.[/\\]",
            r"(\/etc\/passwd|\/etc\/shadow|C:\\Windows)",
        ],
        "xss": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ],
    }

    DANGEROUS_COMMANDS = {
        "rm -rf /",
        "dd if=/dev/",
        "mkfs",
        "format",
        ":(){ :|:& };:",  # Fork bomb
    }


class InputValidator:
    """Comprehensive input validation"""

    # Compiled regex patterns for performance
    _patterns = {
        "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "username": re.compile(r"^[a-zA-Z0-9_-]{3,50}$"),
        "alphanumeric": re.compile(r"^[a-zA-Z0-9]+$"),
        "slug": re.compile(r"^[a-z0-9-]+$"),
        "semver": re.compile(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$"),
        "ip_address": re.compile(r"^(\d{1,3}\.){3}\d{1,3}$"),
        "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE),
    }

    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """Validate email address"""
        if not email:
            return ValidationResult(False, "Email is required")

        if len(email) > 255:
            return ValidationResult(False, "Email too long")

        if not cls._patterns["email"].match(email):
            return ValidationResult(False, "Invalid email format")

        return ValidationResult(True, "Valid email")

    @classmethod
    def validate_username(cls, username: str) -> ValidationResult:
        """Validate username"""
        if not username:
            return ValidationResult(False, "Username is required")

        if len(username) < 3:
            return ValidationResult(False, "Username must be at least 3 characters")

        if len(username) > 50:
            return ValidationResult(False, "Username must be less than 50 characters")

        if not cls._patterns["username"].match(username):
            return ValidationResult(
                False,
                "Username can only contain letters, numbers, underscores, and hyphens",
            )

        # Check for reserved usernames
        reserved = {"admin", "root", "system", "api", "test"}
        if username.lower() in reserved:
            return ValidationResult(False, "Username is reserved")

        return ValidationResult(True, "Valid username")

    @classmethod
    def validate_password(
        cls,
        password: str,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
    ) -> ValidationResult:
        """Validate password strength"""
        errors = []

        if not password:
            return ValidationResult(False, "Password is required")

        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters")

        if len(password) > 128:
            errors.append("Password too long (max 128 characters)")

        if require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if require_digit and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")

        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Check for common weak passwords
        weak_passwords = {
            "password",
            "password123",
            "12345678",
            "qwerty",
            "admin123",
            "letmein",
            "welcome",
        }
        if password.lower() in weak_passwords:
            errors.append("Password is too common")

        if errors:
            return ValidationResult(False, "Password is weak", errors)

        return ValidationResult(True, "Strong password")

    @classmethod
    def validate_script_name(cls, name: str) -> ValidationResult:
        """Validate script name"""
        if not name or not name.strip():
            return ValidationResult(False, "Script name is required")

        name = name.strip()

        if len(name) > 255:
            return ValidationResult(False, "Script name too long")

        if not re.match(r"^[a-zA-Z0-9\s_-]+$", name):
            return ValidationResult(False, "Script name contains invalid characters")

        return ValidationResult(True, "Valid script name")

    @classmethod
    def validate_cron_expression(cls, cron: str) -> ValidationResult:
        """Validate cron expression"""
        from croniter import croniter

        try:
            if not croniter.is_valid(cron):
                return ValidationResult(False, "Invalid cron expression")
            return ValidationResult(True, "Valid cron expression")
        except Exception as e:
            return ValidationResult(False, f"Invalid cron: {str(e)}")

    @classmethod
    def detect_security_threats(
        cls, content: str, check_types: Optional[List[str]] = None
    ) -> ValidationResult:
        """Detect security threats in content"""
        threats = []

        if check_types is None:
            check_types = list(SecurityPatterns.DANGEROUS_PATTERNS.keys())

        for threat_type in check_types:
            patterns = SecurityPatterns.DANGEROUS_PATTERNS.get(threat_type, [])
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(f"Potential {threat_type} detected")
                    break

        # Check dangerous commands
        for cmd in SecurityPatterns.DANGEROUS_COMMANDS:
            if cmd in content:
                threats.append(f"Dangerous command detected: {cmd}")

        if threats:
            return ValidationResult(False, "Security threats detected", threats)

        return ValidationResult(True, "No security threats detected")


class InputSanitizer:
    """Input sanitization"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Escape HTML special characters"""
        return html.escape(text, quote=True)

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Sanitize SQL input (use parameterized queries instead!)"""
        # Remove dangerous characters
        dangerous = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        for char in dangerous:
            text = text.replace(char, "")
        return text

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path"""
        # Remove path traversal attempts
        path = path.replace("..", "")
        path = path.replace("./", "")
        path = path.replace("~", "")

        # Remove null bytes
        path = path.replace("\0", "")

        return path

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        # Remove dangerous characters
        filename = re.sub(r"[^\w\s.-]", "", filename)

        # Remove leading/trailing dots and spaces
        filename = filename.strip(". ")

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:250] + ("." + ext if ext else "")

        return filename

    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL"""
        # Parse and validate
        parsed = urllib.parse.urlparse(url)

        # Only allow http/https
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid URL scheme")

        # Reconstruct safe URL
        return urllib.parse.urlunparse(parsed)

    @staticmethod
    def sanitize_command(command: str) -> str:
        """Sanitize shell command (WARNING: Use with extreme caution!)"""
        # Remove dangerous characters
        dangerous = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        for char in dangerous:
            command = command.replace(char, "")

        return command.strip()

    @staticmethod
    def strip_tags(text: str) -> str:
        """Remove HTML tags"""
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def truncate(text: str, max_length: int = 1000, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[: max_length - len(suffix)] + suffix


class RateLimitValidator:
    """Rate limiting validation"""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(
        self, key: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """Check if rate limit is exceeded"""
        current = await self.redis.incr(key)

        if current == 1:
            await self.redis.expire(key, window_seconds)

        remaining = max(0, limit - current)
        allowed = current <= limit

        return allowed, remaining


# Pre-compiled validators for common use cases
email_validator = InputValidator.validate_email
username_validator = InputValidator.validate_username
password_validator = InputValidator.validate_password
script_name_validator = InputValidator.validate_script_name
