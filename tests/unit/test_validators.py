"""Unit tests for validators"""
import pytest

from shared.validation.validators import (
    InputSanitizer,
    InputValidator,
    SecurityPatterns,
)


class TestInputValidator:
    """Test input validation"""

    def test_validate_email_valid(self):
        result = InputValidator.validate_email("test@example.com")
        assert result.valid

    def test_validate_email_invalid(self):
        result = InputValidator.validate_email("invalid-email")
        assert not result.valid

    def test_validate_username_valid(self):
        result = InputValidator.validate_username("valid_user123")
        assert result.valid

    def test_validate_username_too_short(self):
        result = InputValidator.validate_username("ab")
        assert not result.valid
        assert "at least 3 characters" in result.message

    def test_validate_username_reserved(self):
        result = InputValidator.validate_username("admin")
        assert not result.valid
        assert "reserved" in result.message

    def test_validate_password_strong(self):
        result = InputValidator.validate_password("StrongP@ss123")
        assert result.valid

    def test_validate_password_weak(self):
        result = InputValidator.validate_password("weak")
        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_password_common(self):
        result = InputValidator.validate_password("password123")
        assert not result.valid
        assert any("common" in e for e in result.errors)

    def test_detect_sql_injection(self):
        content = "SELECT * FROM users WHERE id = 1 OR 1=1"
        result = InputValidator.detect_security_threats(content)
        assert not result.valid
        assert any("sql_injection" in e for e in result.errors)

    def test_detect_command_injection(self):
        content = "echo hello; rm -rf /"
        result = InputValidator.detect_security_threats(content)
        assert not result.valid

    def test_detect_xss(self):
        content = "<script>alert('xss')</script>"
        result = InputValidator.detect_security_threats(content)
        assert not result.valid


class TestInputSanitizer:
    """Test input sanitization"""

    def test_sanitize_html(self):
        dirty = "<script>alert('xss')</script>"
        clean = InputSanitizer.sanitize_html(dirty)
        assert "<script>" not in clean
        assert "&lt;script&gt;" in clean

    def test_sanitize_filename(self):
        dirty = "../../../etc/passwd"
        clean = InputSanitizer.sanitize_filename(dirty)
        assert ".." not in clean
        assert "/" not in clean

    def test_strip_tags(self):
        html = "<p>Hello <strong>World</strong></p>"
        clean = InputSanitizer.strip_tags(html)
        assert clean == "Hello World"

    def test_truncate(self):
        long_text = "a" * 1000
        truncated = InputSanitizer.truncate(long_text, max_length=100)
        assert len(truncated) <= 100
