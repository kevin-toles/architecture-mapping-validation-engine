#!/usr/bin/env python3
"""
Tests for JSONL Logger Module
==============================

TDD RED phase: These tests define the expected interface for the
jsonl_logger module, which should contain ONLY logging utilities.

Reference: ARCHITECTURE_GUIDELINES - separation of concerns
Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest


class TestJSONLLoggerInterface:
    """Test the public interface of jsonl_logger module."""

    def test_module_exports_log_record_function(self) -> None:
        """Verify log_record function is exported from module."""
        from observability_platform.src.jsonl_logger import log_record
        assert callable(log_record)

    def test_module_exports_log_records_function(self) -> None:
        """Verify log_records function is exported from module."""
        from observability_platform.src.jsonl_logger import log_records
        assert callable(log_records)

    def test_module_exports_validate_log_function(self) -> None:
        """Verify validate_log function is exported from module."""
        from observability_platform.src.jsonl_logger import validate_log
        assert callable(validate_log)

    def test_module_exports_ensure_log_directory_function(self) -> None:
        """Verify ensure_log_directory function is exported from module."""
        from observability_platform.src.jsonl_logger import ensure_log_directory
        assert callable(ensure_log_directory)

    def test_module_exports_log_file_path(self) -> None:
        """Verify LOG_FILE constant is exported from module."""
        from observability_platform.src.jsonl_logger import LOG_FILE
        assert isinstance(LOG_FILE, Path)

    def test_module_exports_new_id_function(self) -> None:
        """Verify new_id helper is exported for ID generation."""
        from observability_platform.src.jsonl_logger import new_id
        assert callable(new_id)

    def test_module_exports_now_iso_function(self) -> None:
        """Verify now_iso helper is exported for timestamp generation."""
        from observability_platform.src.jsonl_logger import now_iso
        assert callable(now_iso)


class TestLogRecordFunction:
    """Test log_record() function behavior."""

    def test_log_record_writes_single_json_line(self, tmp_path: Path) -> None:
        """Verify log_record writes exactly one JSON line."""
        from observability_platform.src.jsonl_logger import log_record, set_log_file

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        record = {"type": "test", "message": "hello"}
        log_record(record)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1

    def test_log_record_writes_valid_json(self, tmp_path: Path) -> None:
        """Verify log_record writes parseable JSON."""
        from observability_platform.src.jsonl_logger import log_record, set_log_file

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        record = {"type": "test", "data": {"nested": True}}
        log_record(record)

        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed == record

    def test_log_record_appends_to_existing_file(self, tmp_path: Path) -> None:
        """Verify log_record appends, doesn't overwrite."""
        from observability_platform.src.jsonl_logger import log_record, set_log_file

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        log_record({"id": 1})
        log_record({"id": 2})

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == 1
        assert json.loads(lines[1])["id"] == 2


class TestLogRecordsFunction:
    """Test log_records() function behavior."""

    def test_log_records_writes_multiple_lines(self, tmp_path: Path) -> None:
        """Verify log_records writes multiple JSON lines."""
        from observability_platform.src.jsonl_logger import log_records, set_log_file

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        records = [{"id": i} for i in range(5)]
        log_records(records)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 5

    def test_log_records_preserves_order(self, tmp_path: Path) -> None:
        """Verify log_records preserves record order."""
        from observability_platform.src.jsonl_logger import log_records, set_log_file

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        records = [{"order": i} for i in range(3)]
        log_records(records)

        lines = log_file.read_text().strip().split("\n")
        for i, line in enumerate(lines):
            assert json.loads(line)["order"] == i


class TestValidateLogFunction:
    """Test validate_log() function behavior."""

    def test_validate_log_returns_dict(self, tmp_path: Path) -> None:
        """Verify validate_log returns validation results dict."""
        from observability_platform.src.jsonl_logger import (
            log_record,
            set_log_file,
            validate_log,
        )

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        log_record({"type": "meta"})
        result = validate_log()

        assert isinstance(result, dict)
        assert "total_records" in result

    def test_validate_log_counts_records(self, tmp_path: Path) -> None:
        """Verify validate_log counts total records."""
        from observability_platform.src.jsonl_logger import (
            log_records,
            set_log_file,
            validate_log,
        )

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        log_records([{"id": i} for i in range(10)])
        result = validate_log()

        assert result["total_records"] == 10

    def test_validate_log_identifies_record_types(self, tmp_path: Path) -> None:
        """Verify validate_log categorizes record types."""
        from observability_platform.src.jsonl_logger import (
            log_records,
            set_log_file,
            validate_log,
        )

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        log_records([
            {"record_type": "meta"},
            {"record_type": "event"},
            {"record_type": "event"},
        ])
        result = validate_log()

        assert "record_types" in result
        assert result["record_types"].get("meta") == 1
        assert result["record_types"].get("event") == 2

    def test_validate_log_reports_errors(self, tmp_path: Path) -> None:
        """Verify validate_log reports parsing errors."""
        from observability_platform.src.jsonl_logger import set_log_file, validate_log

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        # Write invalid JSON
        log_file.write_text("not valid json\n")
        result = validate_log()

        assert result["error_count"] > 0


class TestHelperFunctions:
    """Test utility helper functions."""

    def test_new_id_generates_unique_ids(self) -> None:
        """Verify new_id generates unique IDs with prefix."""
        from observability_platform.src.jsonl_logger import new_id

        ids = {new_id("test") for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_new_id_includes_prefix(self) -> None:
        """Verify new_id includes the provided prefix."""
        from observability_platform.src.jsonl_logger import new_id

        result = new_id("trc")
        assert result.startswith("trc_")

    def test_now_iso_returns_valid_timestamp(self) -> None:
        """Verify now_iso returns ISO format timestamp."""
        from observability_platform.src.jsonl_logger import now_iso

        result = now_iso()
        # Should match pattern: 2025-11-30T12:34:56.789Z
        assert "T" in result
        assert result.endswith("Z")
        assert len(result) == 24  # YYYY-MM-DDTHH:MM:SS.mmmZ


class TestEnsureLogDirectory:
    """Test ensure_log_directory() function behavior."""

    def test_ensure_log_directory_creates_directory(self, tmp_path: Path) -> None:
        """Verify ensure_log_directory creates parent dirs."""
        from observability_platform.src.jsonl_logger import (
            ensure_log_directory,
            set_log_file,
        )

        nested_path = tmp_path / "a" / "b" / "c" / "test.jsonl"
        set_log_file(nested_path)

        ensure_log_directory()
        assert nested_path.parent.exists()

    def test_ensure_log_directory_idempotent(self, tmp_path: Path) -> None:
        """Verify ensure_log_directory can be called multiple times."""
        from observability_platform.src.jsonl_logger import (
            ensure_log_directory,
            set_log_file,
        )

        log_file = tmp_path / "test.jsonl"
        set_log_file(log_file)

        # Should not raise
        ensure_log_directory()
        ensure_log_directory()
        ensure_log_directory()


class TestModuleDoesNotContainScenarios:
    """Verify jsonl_logger does NOT contain scenario execution logic.
    
    Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle
    """

    def test_no_scenario_class_in_module(self) -> None:
        """Verify Scenario class is NOT in jsonl_logger."""
        import observability_platform.src.jsonl_logger as logger_module

        assert not hasattr(logger_module, "Scenario")

    def test_no_run_scenario_function(self) -> None:
        """Verify run_scenario function is NOT in jsonl_logger."""
        import observability_platform.src.jsonl_logger as logger_module

        assert not hasattr(logger_module, "run_scenario")

    def test_no_get_scenario_definitions_function(self) -> None:
        """Verify get_scenario_definitions is NOT in jsonl_logger."""
        import observability_platform.src.jsonl_logger as logger_module

        assert not hasattr(logger_module, "get_scenario_definitions")

    def test_no_execute_local_function(self) -> None:
        """Verify execute_local_function is NOT in jsonl_logger."""
        import observability_platform.src.jsonl_logger as logger_module

        assert not hasattr(logger_module, "execute_local_function")
