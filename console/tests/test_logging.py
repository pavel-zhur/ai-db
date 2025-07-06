"""Test logging functionality."""

import logging
from pathlib import Path

from console.logging import TraceLogger, setup_logging


def test_trace_logger(tmp_path: Path) -> None:
    """Test trace logger functionality."""
    trace_file = tmp_path / "trace.log"
    logger = TraceLogger(trace_file)

    # Log various entries
    logger.log_input("SELECT * FROM users")
    logger.log_output("3 rows returned")
    logger.log_error("Connection failed")

    # Verify file contents
    contents = trace_file.read_text()
    assert "USER: SELECT * FROM users" in contents
    assert "SYSTEM: 3 rows returned" in contents
    assert "ERROR: Connection failed" in contents

    # Verify timestamps are included
    lines = contents.strip().split("\n")
    assert len(lines) == 3
    for line in lines:
        assert line.startswith("[")
        assert "]" in line


def test_setup_logging(tmp_path: Path) -> None:
    """Test logging setup."""
    log_file = tmp_path / "app.log"
    trace_file = tmp_path / "trace.log"

    # Setup without debug mode
    trace_logger = setup_logging(log_file=log_file, trace_file=trace_file, debug_mode=False)

    # Verify trace logger is returned
    assert isinstance(trace_logger, TraceLogger)

    # Log something
    logger = logging.getLogger(__name__)
    logger.info("Test message")
    logger.debug("Debug message")

    # Verify log file exists and contains info but not debug (root logger level controls)
    assert log_file.exists()
    log_contents = log_file.read_text()
    assert "Test message" in log_contents
    assert "Debug message" not in log_contents  # Root logger level is INFO

    # Test with debug mode
    from rich.console import Console

    console = Console()

    trace_logger2 = setup_logging(
        log_file=log_file, trace_file=trace_file, debug_mode=True, console=console
    )

    assert isinstance(trace_logger2, TraceLogger)


def test_trace_logger_creates_directory(tmp_path: Path) -> None:
    """Test that trace logger creates parent directory if needed."""
    trace_file = tmp_path / "subdir" / "trace.log"
    logger = TraceLogger(trace_file)

    logger.log_input("test")

    assert trace_file.exists()
    assert trace_file.parent.exists()
