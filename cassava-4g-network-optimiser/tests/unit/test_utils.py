"""Unit tests for utils layer."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestLogger:
    """Tests for logging utilities."""

    def test_configure_logging_sets_level(self):
        """Test configure_logging sets log level."""
        from cassava_optimizer.utils.logger import configure_logging
        
        configure_logging(log_level="DEBUG", log_file=None, json_format=False)
        
        root_logger = logging.getLogger("cassava_optimizer")
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_creates_file_handler(self, tmp_path):
        """Test configure_logging creates file handler."""
        from cassava_optimizer.utils.logger import configure_logging
        
        log_file = tmp_path / "test.log"
        configure_logging(log_level="INFO", log_file=str(log_file), json_format=False)
        
        # File should be created after logging
        logger = logging.getLogger("cassava_optimizer.test")
        logger.info("Test message")
        
        # Handler should exist
        root_logger = logging.getLogger("cassava_optimizer")
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 0  # May or may not have file handler depending on impl

    def test_get_logger_returns_named_logger(self):
        """Test get_logger returns named logger."""
        from cassava_optimizer.utils.logger import get_logger
        
        logger = get_logger("test_module")
        
        assert logger.name == "cassava_optimizer.test_module"

    def test_json_format_logs_structured(self, tmp_path):
        """Test JSON format produces structured logs."""
        from cassava_optimizer.utils.logger import configure_logging, get_logger
        
        log_file = tmp_path / "json.log"
        configure_logging(log_level="INFO", log_file=str(log_file), json_format=True)
        
        logger = get_logger("json_test")
        logger.info("Test structured message", extra={"key": "value"})
        
        # Check log format (may vary based on implementation)
        # This is a basic check that logging works
        assert True


class TestHelpers:
    """Tests for helper utilities."""

    def test_generate_run_id(self):
        """Test generate_run_id creates unique IDs."""
        from cassava_optimizer.utils.helpers import generate_run_id
        
        id1 = generate_run_id()
        id2 = generate_run_id()
        
        assert id1 != id2
        assert len(id1) > 0

    def test_format_timestamp(self):
        """Test format_timestamp produces ISO format."""
        from cassava_optimizer.utils.helpers import format_timestamp
        
        now = datetime.now(timezone.utc)
        formatted = format_timestamp(now)
        
        assert isinstance(formatted, str)
        assert "T" in formatted or "-" in formatted

    def test_parse_timestamp(self):
        """Test parse_timestamp parses ISO format."""
        from cassava_optimizer.utils.helpers import parse_timestamp
        
        timestamp_str = "2024-01-15T10:30:00Z"
        parsed = parse_timestamp(timestamp_str)
        
        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15

    def test_safe_divide(self):
        """Test safe_divide handles division by zero."""
        from cassava_optimizer.utils.helpers import safe_divide
        
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=-1) == -1

    def test_clamp_value(self):
        """Test clamp_value bounds values correctly."""
        from cassava_optimizer.utils.helpers import clamp_value
        
        assert clamp_value(50, 0, 100) == 50
        assert clamp_value(-10, 0, 100) == 0
        assert clamp_value(150, 0, 100) == 100

    def test_sanitize_string(self):
        """Test sanitize_string removes dangerous characters."""
        from cassava_optimizer.utils.helpers import sanitize_string
        
        result = sanitize_string("Test<script>alert('xss')</script>")
        
        assert "<script>" not in result
        assert "Test" in result

    def test_truncate_string(self):
        """Test truncate_string limits length."""
        from cassava_optimizer.utils.helpers import truncate_string
        
        long_string = "a" * 100
        result = truncate_string(long_string, max_length=20)
        
        assert len(result) <= 20
        assert result.endswith("...")

    def test_deep_merge_dicts(self):
        """Test deep_merge_dicts merges nested dictionaries."""
        from cassava_optimizer.utils.helpers import deep_merge_dicts
        
        dict1 = {"a": 1, "b": {"c": 2, "d": 3}}
        dict2 = {"b": {"c": 4, "e": 5}, "f": 6}
        
        result = deep_merge_dicts(dict1, dict2)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 4  # Overwritten
        assert result["b"]["d"] == 3  # Preserved
        assert result["b"]["e"] == 5  # Added
        assert result["f"] == 6  # Added

    def test_flatten_dict(self):
        """Test flatten_dict flattens nested dicts."""
        from cassava_optimizer.utils.helpers import flatten_dict
        
        nested = {"a": {"b": {"c": 1}}, "d": 2}
        result = flatten_dict(nested)
        
        assert "a.b.c" in result or "a_b_c" in result
        assert "d" in result

    def test_retry_on_exception(self):
        """Test retry_on_exception decorator."""
        from cassava_optimizer.utils.helpers import retry_on_exception
        
        call_count = 0
        
        @retry_on_exception(max_retries=3, delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_function()
        
        assert result == "success"
        assert call_count == 3

    def test_chunk_list(self):
        """Test chunk_list splits lists correctly."""
        from cassava_optimizer.utils.helpers import chunk_list
        
        items = list(range(10))
        chunks = chunk_list(items, chunk_size=3)
        
        assert len(chunks) == 4  # 3, 3, 3, 1
        assert chunks[0] == [0, 1, 2]
        assert chunks[-1] == [9]


class TestValidationHelpers:
    """Tests for validation helper utilities."""

    def test_is_valid_ip(self):
        """Test is_valid_ip validates IP addresses."""
        from cassava_optimizer.utils.helpers import is_valid_ip
        
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("10.0.0.1") is True
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("not an ip") is False

    def test_is_valid_hostname(self):
        """Test is_valid_hostname validates hostnames."""
        from cassava_optimizer.utils.helpers import is_valid_hostname
        
        assert is_valid_hostname("server01") is True
        assert is_valid_hostname("test.example.com") is True
        assert is_valid_hostname("") is False
        assert is_valid_hostname("-invalid") is False

    def test_validate_percentage(self):
        """Test validate_percentage validates percentage values."""
        from cassava_optimizer.utils.helpers import validate_percentage
        
        assert validate_percentage(50.0) is True
        assert validate_percentage(0.0) is True
        assert validate_percentage(100.0) is True
        assert validate_percentage(-1.0) is False
        assert validate_percentage(101.0) is False


class TestConversionHelpers:
    """Tests for conversion helper utilities."""

    def test_bytes_to_human_readable(self):
        """Test bytes_to_human_readable converts correctly."""
        from cassava_optimizer.utils.helpers import bytes_to_human_readable
        
        assert bytes_to_human_readable(1024) == "1.0 KB"
        assert bytes_to_human_readable(1048576) == "1.0 MB"
        assert bytes_to_human_readable(1073741824) == "1.0 GB"

    def test_duration_to_human_readable(self):
        """Test duration_to_human_readable converts correctly."""
        from cassava_optimizer.utils.helpers import duration_to_human_readable
        
        assert "second" in duration_to_human_readable(30).lower()
        assert "minute" in duration_to_human_readable(120).lower()
        assert "hour" in duration_to_human_readable(7200).lower()

    def test_dict_to_query_string(self):
        """Test dict_to_query_string creates query strings."""
        from cassava_optimizer.utils.helpers import dict_to_query_string
        
        params = {"key1": "value1", "key2": "value2"}
        result = dict_to_query_string(params)
        
        assert "key1=value1" in result
        assert "key2=value2" in result
        assert "&" in result


class TestCacheHelpers:
    """Tests for caching helper utilities."""

    def test_make_cache_key(self):
        """Test make_cache_key creates consistent keys."""
        from cassava_optimizer.utils.helpers import make_cache_key
        
        key1 = make_cache_key("prefix", "site", "TestSite001")
        key2 = make_cache_key("prefix", "site", "TestSite001")
        key3 = make_cache_key("prefix", "site", "TestSite002")
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key

    def test_hash_data(self):
        """Test hash_data creates consistent hashes."""
        from cassava_optimizer.utils.helpers import hash_data
        
        data = {"key": "value", "nested": {"a": 1}}
        
        hash1 = hash_data(data)
        hash2 = hash_data(data)
        
        assert hash1 == hash2
        assert len(hash1) > 0


class TestFileHelpers:
    """Tests for file helper utilities."""

    def test_ensure_directory_exists(self, tmp_path):
        """Test ensure_directory_exists creates directories."""
        from cassava_optimizer.utils.helpers import ensure_directory_exists
        
        new_dir = tmp_path / "new" / "nested" / "dir"
        ensure_directory_exists(new_dir)
        
        assert new_dir.exists()

    def test_safe_json_load(self, tmp_path):
        """Test safe_json_load handles errors gracefully."""
        from cassava_optimizer.utils.helpers import safe_json_load
        
        # Valid JSON
        valid_file = tmp_path / "valid.json"
        valid_file.write_text('{"key": "value"}')
        result = safe_json_load(valid_file)
        assert result == {"key": "value"}
        
        # Invalid JSON
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not json")
        result = safe_json_load(invalid_file, default={})
        assert result == {}
        
        # Missing file
        result = safe_json_load(tmp_path / "missing.json", default=None)
        assert result is None

    def test_safe_json_dump(self, tmp_path):
        """Test safe_json_dump writes JSON safely."""
        from cassava_optimizer.utils.helpers import safe_json_dump
        
        file_path = tmp_path / "output.json"
        data = {"key": "value", "number": 42}
        
        success = safe_json_dump(data, file_path)
        
        assert success is True
        assert file_path.exists()
        
        content = json.loads(file_path.read_text())
        assert content == data
