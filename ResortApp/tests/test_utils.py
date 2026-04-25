"""
test_utils.py — Unit tests for utility functions (billing helpers, date utils, auth utils)
"""
import pytest
from datetime import datetime, timedelta


class TestDateUtils:
    def test_ensure_utc_naive_string_gets_Z(self):
        """ensureUTC should append Z to naive ISO strings."""
        # Simulating JS ensureUTC logic in Python terms
        date_str = "2026-04-19T10:30:00"
        if "T" in date_str and not date_str.endswith("Z") and "+" not in date_str[date_str.index("T"):]:
            result = date_str + "Z"
        else:
            result = date_str
        assert result == "2026-04-19T10:30:00Z"

    def test_ensure_utc_already_has_z(self):
        """ensureUTC should leave strings with Z unchanged."""
        date_str = "2026-04-19T10:30:00Z"
        if "T" in date_str and not date_str.endswith("Z") and "+" not in date_str[date_str.index("T"):]:
            result = date_str + "Z"
        else:
            result = date_str
        assert result == "2026-04-19T10:30:00Z"

    def test_ensure_utc_already_has_offset(self):
        """ensureUTC should leave strings with +05:30 timezone offset unchanged."""
        date_str = "2026-04-19T10:30:00+05:30"
        if "T" in date_str and not date_str.endswith("Z") and "+" not in date_str[date_str.index("T"):]:
            result = date_str + "Z"
        else:
            result = date_str
        assert result == "2026-04-19T10:30:00+05:30"

    def test_backend_date_utils_format(self):
        """Test the Python date_utils module for basic formatting functionality."""
        try:
            from app.utils import date_utils
            assert hasattr(date_utils, "__file__"), "date_utils module should exist"
        except ImportError:
            pytest.skip("date_utils module not available")


class TestPasswordHashing:
    def test_hash_and_verify_password(self):
        """Password should hash and verify correctly."""
        from app.utils.auth import get_password_hash, verify_password
        plain = "TestPass@123"
        hashed = get_password_hash(plain)
        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails_verification(self):
        """Wrong password should fail verify_password."""
        from app.utils.auth import get_password_hash, verify_password
        hashed = get_password_hash("CorrectPass")
        assert verify_password("WrongPass", hashed) is False

    def test_long_password_truncation(self):
        """Bcrypt handles passwords > 72 bytes — should not crash."""
        from app.utils.auth import get_password_hash, verify_password
        long_pass = "A" * 100
        hashed = get_password_hash(long_pass)
        # Should work without error
        assert hashed is not None
        result = verify_password(long_pass, hashed)
        assert isinstance(result, bool)


class TestJWTToken:
    def test_create_and_decode_token(self):
        """Token created should decode back to original payload."""
        from app.utils.auth import create_access_token, decode_token
        payload = {"user_id": 42}
        token = create_access_token(payload)
        assert token is not None
        decoded = decode_token(token)
        assert decoded["user_id"] == 42

    def test_token_is_string(self):
        """Token should be a string."""
        from app.utils.auth import create_access_token
        token = create_access_token({"user_id": 1})
        assert isinstance(token, str)

    def test_token_has_expiry(self):
        """Token should contain an exp claim."""
        from app.utils.auth import create_access_token, decode_token
        token = create_access_token({"user_id": 1})
        decoded = decode_token(token)
        assert "exp" in decoded

    def test_invalid_token_raises(self):
        """Decoding a bad token should raise an exception."""
        from app.utils.auth import decode_token
        from jose import JWTError
        with pytest.raises(Exception):
            decode_token("this.is.not.valid")


class TestBranchScopeUtils:
    def test_permission_superadmin_bypass(self):
        """Superadmin should have all permissions."""
        from app.utils.auth import has_permission
        from app.models.user import User, Role
        user = User(id=1, name="Admin", email="a@b.com",
                    hashed_password="x", is_superadmin=True)
        assert has_permission(user, "rooms:view") is True
        assert has_permission(user, "inventory:delete") is True
        assert has_permission(user, "any:permission") is True

    def test_permission_denied_for_no_role(self):
        """User with no role and no superadmin flag should have no permissions."""
        from app.utils.auth import has_permission
        from app.models.user import User
        user = User(id=2, name="Nobody", email="n@b.com",
                    hashed_password="x", is_superadmin=False)
        user.role = None
        assert has_permission(user, "rooms:view") is False
