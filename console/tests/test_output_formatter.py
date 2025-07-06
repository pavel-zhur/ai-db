"""Test output formatter."""

import json
from io import StringIO

import pytest
import yaml
from rich.console import Console

from console.models import OutputFormat
from console.output_formatter import OutputFormatter


@pytest.fixture
def formatter() -> OutputFormatter:
    """Create formatter with string console."""
    console = Console(file=StringIO(), force_terminal=True, width=120)
    return OutputFormatter(console, max_width=120)


class TestOutputFormatter:
    """Test output formatting functionality."""

    def test_format_json(self, formatter: OutputFormatter) -> None:
        """Test JSON formatting."""
        data = {"id": 1, "name": "Test", "active": True}
        result = formatter.format_result(data, OutputFormat.JSON, title="Test Data")

        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed == data

    def test_format_yaml(self, formatter: OutputFormatter) -> None:
        """Test YAML formatting."""
        data = {"id": 1, "name": "Test", "items": ["a", "b", "c"]}
        result = formatter.format_result(data, OutputFormat.YAML, title="Test Data")

        # Verify it's valid YAML
        parsed = yaml.safe_load(result)
        assert parsed == data

    def test_format_table_dict_list(self, formatter: OutputFormatter) -> None:
        """Test table formatting for list of dictionaries."""
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

        result = formatter.format_result(data, OutputFormat.TABLE, title="Users")

        assert "id" in result
        assert "name" in result
        assert "age" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result

    def test_format_table_simple_list(self, formatter: OutputFormatter) -> None:
        """Test table formatting for simple list."""
        data = ["apple", "banana", "cherry"]

        result = formatter.format_result(data, OutputFormat.TABLE)

        assert "apple" in result
        assert "banana" in result
        assert "cherry" in result

    def test_format_table_dict(self, formatter: OutputFormatter) -> None:
        """Test table formatting for dictionary."""
        data = {"count": 100, "status": "active", "last_updated": "2024-01-01"}

        result = formatter.format_result(data, OutputFormat.TABLE)

        assert "count" in result
        assert "100" in result
        assert "status" in result
        assert "active" in result

    def test_format_nested_data(self, formatter: OutputFormatter) -> None:
        """Test formatting nested data structures."""
        data = [
            {
                "id": 1,
                "user": {"name": "Alice", "email": "alice@example.com"},
                "items": ["item1", "item2"],
            }
        ]

        # JSON format should handle nested data
        json_result = formatter.format_result(data, OutputFormat.JSON)
        parsed = json.loads(json_result)
        assert parsed[0]["user"]["name"] == "Alice"

        # Table format should convert nested to string
        table_result = formatter.format_result(data, OutputFormat.TABLE)
        assert "Alice" in table_result
        assert "item1" in table_result

    def test_format_empty_data(self, formatter: OutputFormatter) -> None:
        """Test formatting empty data."""
        result = formatter.format_result([], OutputFormat.TABLE)
        assert "No results" in result

        result = formatter.format_result(None, OutputFormat.TABLE)
        assert "No results" in result

    def test_format_with_ai_comment(self, formatter: OutputFormatter) -> None:
        """Test formatting with AI comment."""
        data = {"result": "success"}

        # Capture console output
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        formatter = OutputFormatter(console, max_width=120)

        formatter.format_result(data, OutputFormat.JSON, ai_comment="Query executed successfully")

        output = string_io.getvalue()
        assert "Query executed successfully" in output

    def test_format_error(self, formatter: OutputFormatter) -> None:
        """Test error formatting."""
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        formatter = OutputFormatter(console, max_width=120)

        formatter.format_error("Something went wrong")
        output = string_io.getvalue()

        assert "Error:" in output
        assert "Something went wrong" in output

    def test_format_success(self, formatter: OutputFormatter) -> None:
        """Test success message formatting."""
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        formatter = OutputFormatter(console, max_width=120)

        formatter.format_success("Operation completed")
        output = string_io.getvalue()

        assert "✓" in output
        assert "Operation completed" in output

    def test_format_info(self, formatter: OutputFormatter) -> None:
        """Test info message formatting."""
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        formatter = OutputFormatter(console, max_width=120)

        formatter.format_info("Processing...")
        output = string_io.getvalue()

        assert "Info:" in output
        assert "Processing" in output

    def test_format_warning(self, formatter: OutputFormatter) -> None:
        """Test warning message formatting."""
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True)
        formatter = OutputFormatter(console, max_width=120)

        formatter.format_warning("Be careful")
        output = string_io.getvalue()

        assert "⚠" in output
        assert "Be careful" in output
