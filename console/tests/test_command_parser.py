"""Test command parser."""

import pytest

from console.command_parser import CommandParser
from console.models import CommandType


@pytest.fixture
def parser() -> CommandParser:
    return CommandParser()


class TestCommandParser:
    """Test command parsing functionality."""

    def test_transaction_commands(self, parser: CommandParser) -> None:
        """Test transaction command parsing."""
        assert parser.parse("begin")[0] == CommandType.TRANSACTION_BEGIN
        assert parser.parse("BEGIN TRANSACTION")[0] == CommandType.TRANSACTION_BEGIN
        assert parser.parse("  begin  ")[0] == CommandType.TRANSACTION_BEGIN

        assert parser.parse("commit")[0] == CommandType.TRANSACTION_COMMIT
        assert parser.parse("COMMIT TRANSACTION")[0] == CommandType.TRANSACTION_COMMIT

        assert parser.parse("rollback")[0] == CommandType.TRANSACTION_ROLLBACK
        assert parser.parse("ROLLBACK TRANSACTION")[0] == CommandType.TRANSACTION_ROLLBACK

    def test_help_command(self, parser: CommandParser) -> None:
        """Test help command parsing."""
        assert parser.parse("help")[0] == CommandType.HELP
        assert parser.parse("?")[0] == CommandType.HELP
        assert parser.parse("  HELP  ")[0] == CommandType.HELP

    def test_exit_command(self, parser: CommandParser) -> None:
        """Test exit command parsing."""
        assert parser.parse("exit")[0] == CommandType.EXIT
        assert parser.parse("quit")[0] == CommandType.EXIT
        assert parser.parse("bye")[0] == CommandType.EXIT
        assert parser.parse("  EXIT  ")[0] == CommandType.EXIT

    def test_output_format_command(self, parser: CommandParser) -> None:
        """Test output format command parsing."""
        cmd_type, params = parser.parse("output format table")
        assert cmd_type == CommandType.OUTPUT_FORMAT
        assert params == "table"

        cmd_type, params = parser.parse("OUTPUT FORMAT JSON")
        assert cmd_type == CommandType.OUTPUT_FORMAT
        assert params == "json"

        cmd_type, params = parser.parse("output format yaml")
        assert cmd_type == CommandType.OUTPUT_FORMAT
        assert params == "yaml"

        # Invalid format defaults to query
        cmd_type, params = parser.parse("output format invalid")
        assert cmd_type == CommandType.QUERY

    def test_export_command(self, parser: CommandParser) -> None:
        """Test export command parsing."""
        cmd_type, params = parser.parse("export SELECT * FROM users to output.csv")
        assert cmd_type == CommandType.EXPORT
        assert params == "SELECT * FROM users|output.csv"

        cmd_type, params = parser.parse("export show all data to /tmp/data.json")
        assert cmd_type == CommandType.EXPORT
        assert params == "show all data|/tmp/data.json"

    def test_schema_commands(self, parser: CommandParser) -> None:
        """Test schema modification command detection."""
        schema_commands = [
            "CREATE TABLE users (id INT, name VARCHAR)",
            "alter table products add column price decimal",
            "DROP TABLE old_data",
            "create schema analytics",
            "CREATE DATABASE testdb",
        ]

        for cmd in schema_commands:
            assert parser.parse(cmd)[0] == CommandType.SCHEMA_MODIFY

    def test_data_commands(self, parser: CommandParser) -> None:
        """Test data modification command detection."""
        data_commands = [
            "INSERT INTO users VALUES (1, 'John')",
            "update products set price = 10.99",
            "DELETE FROM logs WHERE date < '2023-01-01'",
            "merge into target using source",
        ]

        for cmd in data_commands:
            assert parser.parse(cmd)[0] == CommandType.DATA_MODIFY

    def test_view_commands(self, parser: CommandParser) -> None:
        """Test view command detection."""
        view_commands = [
            "CREATE VIEW active_users AS SELECT * FROM users WHERE active = true",
            "alter view customer_summary add column total_spent",
        ]

        for cmd in view_commands:
            assert parser.parse(cmd)[0] == CommandType.VIEW_MODIFY

    def test_frontend_commands(self, parser: CommandParser) -> None:
        """Test frontend generation command detection."""
        frontend_commands = [
            "generate ui for user management",
            "create frontend dashboard",
            "build interface for products",
            "make ui with tables and forms",
            "generate component for customer list",
            "create dashboard showing analytics",
        ]

        for cmd in frontend_commands:
            assert parser.parse(cmd)[0] == CommandType.FRONTEND_GENERATE

    def test_query_commands(self, parser: CommandParser) -> None:
        """Test query command detection (default)."""
        query_commands = [
            "SELECT * FROM users",
            "show all customers",
            "find products with price > 100",
            "what are the top selling items",
            "list recent orders",
        ]

        for cmd in query_commands:
            assert parser.parse(cmd)[0] == CommandType.QUERY

    def test_destructive_operation_detection(self, parser: CommandParser) -> None:
        """Test destructive operation detection."""
        destructive_commands = [
            "DROP TABLE users",
            "truncate table logs",
            "DELETE FROM customers",
            "drop database production",
            "DROP SCHEMA analytics",
            "ALTER TABLE users DROP COLUMN email",
        ]

        for cmd in destructive_commands:
            assert parser.detect_destructive_operation(cmd) is True

        safe_commands = [
            "SELECT * FROM users",
            "INSERT INTO users VALUES (1, 'test')",
            "UPDATE users SET active = true",
            "CREATE TABLE new_table (id INT)",
        ]

        for cmd in safe_commands:
            assert parser.detect_destructive_operation(cmd) is False
