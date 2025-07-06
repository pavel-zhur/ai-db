"""Command parsing for the console."""

import re
from typing import ClassVar

from .models import CommandType


class CommandParser:
    """Parse user commands and detect special commands."""

    # Special command patterns
    _PATTERNS: ClassVar[dict[CommandType, re.Pattern[str]]] = {
        CommandType.TRANSACTION_BEGIN: re.compile(r"^\s*begin\s*(?:transaction)?\s*$", re.I),
        CommandType.TRANSACTION_COMMIT: re.compile(r"^\s*commit\s*(?:transaction)?\s*$", re.I),
        CommandType.TRANSACTION_ROLLBACK: re.compile(r"^\s*rollback\s*(?:transaction)?\s*$", re.I),
        CommandType.HELP: re.compile(r"^\s*(?:help|\?)\s*$", re.I),
        CommandType.EXIT: re.compile(r"^\s*(?:exit|quit|bye)\s*$", re.I),
        CommandType.OUTPUT_FORMAT: re.compile(r"^\s*output\s+format\s+(\w+)\s*$", re.I),
        CommandType.EXPORT: re.compile(r"^\s*export\s+(.+?)\s+to\s+(.+)$", re.I),
    }

    # Schema modification keywords
    _SCHEMA_KEYWORDS: ClassVar[list[str]] = [
        "create table",
        "alter table",
        "drop table",
        "create schema",
        "create database",
        "create view",
        "drop view",
        "alter view",
    ]

    # Data modification keywords
    _DATA_KEYWORDS: ClassVar[list[str]] = ["insert", "update", "delete", "merge", "upsert"]

    # Frontend generation keywords
    _FRONTEND_KEYWORDS: ClassVar[list[str]] = [
        "generate ui",
        "create ui",
        "build ui",
        "make ui",
        "generate frontend",
        "create frontend",
        "build frontend",
        "generate interface",
        "create interface",
        "build interface",
        "generate component",
        "create component",
        "build component",
        "generate page",
        "create page",
        "build page",
        "generate dashboard",
        "create dashboard",
        "build dashboard",
        "generate form",
        "create form",
        "build form",
    ]

    def parse(self, command: str) -> tuple[CommandType, str | None]:
        """Parse command and return type and optional parameters.

        Args:
            command: User input command

        Returns:
            Tuple of (command_type, parameters)
        """
        command = command.strip()

        # Check special commands first
        for cmd_type, pattern in self._PATTERNS.items():
            match = pattern.match(command)
            if match:
                if cmd_type == CommandType.OUTPUT_FORMAT:
                    format_str = match.group(1).lower()
                    if format_str in ["table", "json", "yaml"]:
                        return cmd_type, format_str
                    else:
                        return CommandType.QUERY, command  # Invalid format
                elif cmd_type == CommandType.EXPORT:
                    return cmd_type, f"{match.group(1)}|{match.group(2)}"
                else:
                    return cmd_type, None

        # Check if it's a frontend generation request
        command_lower = command.lower()
        for keyword in self._FRONTEND_KEYWORDS:
            if keyword in command_lower:
                return CommandType.FRONTEND_GENERATE, command

        # Check for view creation/modification first (more specific than schema)
        if (
            "create view" in command_lower
            or "alter view" in command_lower
            or "drop view" in command_lower
        ):
            return CommandType.VIEW_MODIFY, command

        # Check if it's a schema modification
        for keyword in self._SCHEMA_KEYWORDS:
            if keyword in command_lower:
                return CommandType.SCHEMA_MODIFY, command

        # Check if it's a data modification
        for keyword in self._DATA_KEYWORDS:
            if command_lower.startswith(keyword):
                return CommandType.DATA_MODIFY, command

        # Default to query
        return CommandType.QUERY, command

    def detect_destructive_operation(self, command: str) -> bool:
        """Check if command is potentially destructive.

        Args:
            command: User command

        Returns:
            True if command is destructive
        """
        destructive_patterns = [
            r"\bdrop\s+table\b",
            r"\btruncate\s+table\b",
            r"\bdelete\s+from\b",
            r"\bdrop\s+database\b",
            r"\bdrop\s+schema\b",
            r"\balter\s+table\s+.*\s+drop\b",
        ]

        command_lower = command.lower()
        return any(re.search(pattern, command_lower) for pattern in destructive_patterns)
