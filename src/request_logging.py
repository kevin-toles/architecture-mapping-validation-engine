"""
WBS 2.8.1.2: Request Logging Middleware

ASGI middleware for logging HTTP requests/responses with correlation ID support.

Reference Documents:
- GUIDELINES pp. 2309-2319: Observability patterns
- ARCHITECTURE.md Line 30: Request/response logging

Features:
- JSON structured logging
- Correlation ID generation and propagation
- Request method, path, status code, duration logging
- Health check path exclusion
- Non-HTTP request passthrough (WebSocket, lifespan)
"""

import json
import time
import uuid
from contextvars import ContextVar
from io import StringIO
from typing import Any, Callable, List, Optional

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


class RequestLoggingMiddleware:
    """
    ASGI middleware for structured request/response logging.
    
    Features:
    - Logs HTTP method, path, status code, and duration
    - Generates or propagates correlation IDs
    - Supports exclusion of health check paths
    - Passes through non-HTTP requests (WebSocket, lifespan)
    - JSON structured log output
    """
    
    def __init__(
        self,
        app: Callable,
        log_stream: Optional[StringIO] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize request logging middleware.
        
        Args:
            app: ASGI application to wrap
            log_stream: Optional stream for log output (default: stdout)
            exclude_paths: List of paths to exclude from logging
        """
        self.app = app
        self.log_stream = log_stream
        self.exclude_paths = exclude_paths or []
    
    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        """
        Process ASGI request.
        
        Args:
            scope: ASGI scope dictionary
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Pass through non-HTTP requests
        if scope.get("type") not in ("http",):
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        headers = dict(scope.get("headers", []))
        
        # Check if path should be excluded
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return
        
        # Get or generate correlation ID
        correlation_id = self._get_correlation_id_from_headers(headers)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set correlation ID in context
        set_correlation_id(correlation_id)
        
        # Track response status
        response_status = [None]  # Use list for mutation in closure
        start_time = time.perf_counter()
        
        async def send_wrapper(message: dict[str, Any]) -> None:
            """Wrapper to capture response status."""
            if message.get("type") == "http.response.start":
                response_status[0] = message.get("status", 0)
            await send(message)
        
        try:
            # Call the app
            await self.app(scope, receive, send_wrapper)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log successful request
            self._log_request(
                method=method,
                path=path,
                status=response_status[0],
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log error
            self._log_error(
                method=method,
                path=path,
                error=str(e),
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            raise
        finally:
            # Clear correlation ID
            clear_correlation_id()
    
    def _get_correlation_id_from_headers(
        self, headers: dict[bytes, bytes]
    ) -> Optional[str]:
        """Extract correlation ID from request headers."""
        # Check for X-Correlation-ID header (case-insensitive)
        for key, value in headers.items():
            if key.lower() == b"x-correlation-id":
                return value.decode("utf-8")
        return None
    
    def _log_request(
        self,
        method: str,
        path: str,
        status: Optional[int],
        duration_ms: float,
        correlation_id: str,
    ) -> None:
        """Log a completed request."""
        log_entry = {
            "method": method,
            "path": path,
            "status": status,
            "status_code": status,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": correlation_id,
        }
        self._write_log(log_entry)
    
    def _log_error(
        self,
        method: str,
        path: str,
        error: str,
        duration_ms: float,
        correlation_id: str,
    ) -> None:
        """Log a request that resulted in an error."""
        log_entry = {
            "method": method,
            "path": path,
            "error": error,
            "exception": error,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": correlation_id,
        }
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: dict[str, Any]) -> None:
        """Write log entry to stream."""
        log_json = json.dumps(log_entry)
        if self.log_stream:
            self.log_stream.write(log_json + "\n")
        else:
            print(log_json)
