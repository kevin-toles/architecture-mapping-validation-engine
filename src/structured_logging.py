"""
WBS 2.8.1.1: Structured Logging Configuration

JSON-formatted structured logging with correlation ID support.

Reference Documents:
- GUIDELINES pp. 2309-2319: Prometheus for metrics collection and structured logging
- Newman: "log when timeouts occur, look at what happens, and change them"

Features:
- JSON structured log output
- Correlation ID context propagation
- Log level configuration
- Timestamp and level processors
"""

import json
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Optional


# Correlation ID context variable for request tracing
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from context."""
    _correlation_id.set(None)


class StructuredLogger:
    """
    Structured JSON logger with correlation ID support.
    
    Outputs JSON log entries with:
    - timestamp
    - level
    - logger name
    - correlation_id (when set)
    - event message
    - additional structured data
    """
    
    # Log level ordering
    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    
    def __init__(
        self,
        name: str,
        stream: Optional[StringIO] = None,
        level: str = "INFO",
    ) -> None:
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (module/component identifier)
            stream: Output stream (default: stdout)
            level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.stream = stream or sys.stdout
        self.level = level.upper()
        self.level_value = self.LOG_LEVELS.get(self.level, 20)
    
    def _should_log(self, level: str) -> bool:
        """Check if message at given level should be logged."""
        level_value = self.LOG_LEVELS.get(level.upper(), 20)
        return level_value >= self.level_value
    
    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        """
        Write a structured log entry.
        
        Args:
            level: Log level
            event: Event message
            **kwargs: Additional structured fields
        """
        if not self._should_log(level):
            return
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.lower(),
            "logger": self.name,
            "logger_name": self.name,
            "event": event,
            "correlation_id": get_correlation_id(),
        }
        
        # Add any additional fields
        log_entry.update(kwargs)
        
        # Write JSON to stream
        log_json = json.dumps(log_entry)
        if isinstance(self.stream, StringIO):
            self.stream.write(log_json + "\n")
        else:
            print(log_json, file=self.stream)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self._log("DEBUG", event, **kwargs)
    
    def info(self, event: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self._log("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self._log("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        self._log("ERROR", event, **kwargs)
    
    def critical(self, event: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""
        self._log("CRITICAL", event, **kwargs)


def get_logger(
    name: str,
    stream: Optional[StringIO] = None,
    level: str = "INFO",
) -> StructuredLogger:
    """
    Get a configured structured logger.
    
    Args:
        name: Logger name (module/component identifier)
        stream: Output stream (default: stdout)
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured StructuredLogger instance
    """
    return StructuredLogger(name=name, stream=stream, level=level)
