"""Logging configuration for the console."""

import logging
import traceback
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


class TraceLogger:
    """Logger for tracing conversation history to file."""

    def __init__(self, trace_file: Path):
        self._trace_file = trace_file
        self._trace_file.parent.mkdir(parents=True, exist_ok=True)

    def log_input(self, query: str) -> None:
        """Log user input."""
        timestamp = datetime.now().isoformat()
        with open(self._trace_file, "a") as f:
            f.write(f"[{timestamp}] USER: {query}\n")

    def log_output(self, response: str) -> None:
        """Log system response."""
        timestamp = datetime.now().isoformat()
        with open(self._trace_file, "a") as f:
            f.write(f"[{timestamp}] SYSTEM: {response}\n")

    def log_error(self, error: str, include_traceback: bool = True) -> None:
        """Log error with optional stack trace."""
        timestamp = datetime.now().isoformat()
        with open(self._trace_file, "a") as f:
            f.write(f"[{timestamp}] ERROR: {error}\n")
            if include_traceback:
                tb = traceback.format_exc()
                if tb and tb != "NoneType: None\n":
                    f.write(f"[{timestamp}] TRACEBACK:\n{tb}\n")


def setup_logging(
    log_file: Path, trace_file: Path, debug_mode: bool = False, console: Console | None = None
) -> TraceLogger:
    """Set up logging configuration.

    Args:
        log_file: Path to the main log file
        trace_file: Path to the trace file
        debug_mode: Whether to enable debug logging
        console: Rich console for output (if debug_mode is True)

    Returns:
        TraceLogger instance for conversation tracing
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler - always logs everything
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - only in debug mode
    if debug_mode and console:
        console_handler = RichHandler(console=console, show_time=True, show_path=False, markup=True)
        console_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

    # Create trace logger
    trace_logger = TraceLogger(trace_file)

    return trace_logger
