"""Tests for OData input sanitization."""

import pytest

from exactonline_mcp.client import sanitize_odata_string


class TestSanitizeOdataString:
    """Test cases for sanitize_odata_string function."""

    def test_normal_string_unchanged(self):
        """Normal strings should pass through unchanged."""
        assert sanitize_odata_string("1300") == "1300"
        assert sanitize_odata_string("ABC123") == "ABC123"
        assert sanitize_odata_string("test") == "test"

    def test_single_quotes_escaped(self):
        """Single quotes should be doubled for OData escaping."""
        assert sanitize_odata_string("O'Brien") == "O''Brien"
        assert sanitize_odata_string("Test's value") == "Test''s value"
        assert sanitize_odata_string("''") == "''''"

    def test_rejects_or_operator(self):
        """Should reject strings containing ' or ' operator."""
        with pytest.raises(ValueError, match="Invalid characters"):
            sanitize_odata_string("' or 1 eq 1 or '")

    def test_rejects_and_operator(self):
        """Should reject strings containing ' and ' operator."""
        with pytest.raises(ValueError, match="Invalid characters"):
            sanitize_odata_string("test and other")

    def test_rejects_eq_operator(self):
        """Should reject strings containing ' eq ' operator."""
        with pytest.raises(ValueError, match="Invalid characters"):
            sanitize_odata_string("' eq '")

    def test_rejects_comparison_operators(self):
        """Should reject strings containing comparison operators."""
        operators = [" ne ", " gt ", " lt ", " ge ", " le "]
        for op in operators:
            with pytest.raises(ValueError, match="Invalid characters"):
                sanitize_odata_string(f"value{op}other")

    def test_case_insensitive_detection(self):
        """Operator detection should be case insensitive."""
        with pytest.raises(ValueError, match="Invalid characters"):
            sanitize_odata_string("' OR 1 EQ 1 OR '")

    def test_rejects_non_string_input(self):
        """Should reject non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            sanitize_odata_string(123)  # type: ignore
        with pytest.raises(ValueError, match="must be a string"):
            sanitize_odata_string(None)  # type: ignore

    def test_empty_string_allowed(self):
        """Empty string should be allowed."""
        assert sanitize_odata_string("") == ""

    def test_whitespace_allowed(self):
        """Strings with whitespace (but no operators) should be allowed."""
        assert sanitize_odata_string("test value") == "test value"
        assert sanitize_odata_string("  spaces  ") == "  spaces  "
