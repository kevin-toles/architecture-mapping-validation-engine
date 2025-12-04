#!/usr/bin/env python3
"""
JSONL Logger Module
===================

Pure logging utilities for the observability platform.
This module handles ONLY:
- Writing JSON records to JSONL files
- Validating JSONL log files
- ID and timestamp generation utilities

Reference: ARCHITECTURE_GUIDELINES - separation of concerns
Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle

This module intentionally does NOT contain:
- Scenario definitions
- Scenario execution logic
- Architecture context definitions
- HTTP/API execution

Those concerns belong in separate modules.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# Configuration
# =============================================================================

# Schema version and generator identification
SCHEMA_VERSION = "1.0.0"
GENERATOR_ID = "frontend_driver_v1"

# Default log file location (can be overridden via set_log_file)
_OBSERVABILITY_ROOT = Path(__file__).parent.parent
_DEFAULT_LOG_FILE = _OBSERVABILITY_ROOT / "logs" / "system_observability_log.jsonl"

# Module-level mutable state for log file path
# Reference: ANTI_PATTERN_ANALYSIS 1.2 - annotate with Optional for None-initialized
_current_log_file: Optional[Path] = None


def _get_log_file() -> Path:
    """Get the current log file path, defaulting to standard location."""
    return _current_log_file if _current_log_file is not None else _DEFAULT_LOG_FILE


# Public constant for external access
LOG_FILE = _DEFAULT_LOG_FILE


def set_log_file(path: Path) -> None:
    """
    Set the log file path for testing or custom configurations.
    
    Args:
        path: Path to the JSONL log file
    """
    global _current_log_file
    _current_log_file = path


def reset_log_file() -> None:
    """Reset log file to default location."""
    global _current_log_file
    _current_log_file = None


# =============================================================================
# ID Generation Utilities
# =============================================================================

def new_id(prefix: str) -> str:
    """
    Generate a unique ID with prefix.
    
    Args:
        prefix: Prefix string (e.g., 'trc', 'evt', 'svc')
        
    Returns:
        Unique ID in format 'prefix_hexstring' (e.g., 'trc_01HF...')
    """
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def now_iso() -> str:
    """
    Return current timestamp in ISO format.
    
    Returns:
        Timestamp in format 'YYYY-MM-DDTHH:MM:SS.mmmZ'
    """
    return datetime.now(tz=None).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# =============================================================================
# JSONL Logging Functions
# =============================================================================

def ensure_log_directory() -> None:
    """
    Create log directory if it doesn't exist.
    
    Uses mkdir with parents=True for nested directory creation.
    Idempotent - safe to call multiple times.
    """
    log_file = _get_log_file()
    log_file.parent.mkdir(parents=True, exist_ok=True)


def log_record(record: Dict[str, Any]) -> None:
    """
    Append a single JSON record to the JSONL log file.
    
    Each record is written as one line with no pretty-printing
    for efficient append-only logging.
    
    Args:
        record: Dictionary to serialize as JSON
    """
    ensure_log_directory()
    log_file = _get_log_file()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")


def log_records(records: List[Dict[str, Any]]) -> None:
    """
    Append multiple records to the JSONL log file.
    
    Writes all records in a single file operation for efficiency.
    Preserves record order.
    
    Args:
        records: List of dictionaries to serialize as JSON
    """
    ensure_log_directory()
    log_file = _get_log_file()
    with open(log_file, "a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")


# =============================================================================
# Log Validation
# =============================================================================

def validate_log() -> Dict[str, Any]:
    """
    Validate the JSONL log file and return statistics.
    
    Returns:
        Dictionary containing:
        - total_records: Number of records in log
        - record_types: Count of each record_type value
        - error_count: Number of parse errors
        - errors: List of error details (line number, error message)
    """
    log_file = _get_log_file()
    
    result: Dict[str, Any] = {
        "total_records": 0,
        "record_types": {},
        "error_count": 0,
        "errors": [],
    }
    
    if not log_file.exists():
        return result
    
    with open(log_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
                
            try:
                record = json.loads(line)
                result["total_records"] += 1
                
                # Count record types
                record_type = record.get("record_type", "unknown")
                result["record_types"][record_type] = (
                    result["record_types"].get(record_type, 0) + 1
                )
                
            except json.JSONDecodeError as e:
                result["error_count"] += 1
                result["errors"].append({
                    "line": line_num,
                    "error": str(e),
                    "content": line[:100],  # First 100 chars for debugging
                })
    
    return result


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "LOG_FILE",
    "SCHEMA_VERSION",
    "GENERATOR_ID",
    "ensure_log_directory",
    "log_record",
    "log_records",
    "new_id",
    "now_iso",
    "reset_log_file",
    "set_log_file",
    "validate_log",
]
