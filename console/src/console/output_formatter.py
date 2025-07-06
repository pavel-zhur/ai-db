"""Output formatting for query results."""

import json
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table
from tabulate import tabulate

from .models import OutputFormat


class OutputFormatter:
    """Formats query results for display."""

    def __init__(self, console: Console, max_width: int = 120):
        self._console = console
        self._max_width = max_width

    def format_result(
        self,
        data: Any,
        format_type: OutputFormat,
        title: str | None = None,
        ai_comment: str | None = None,
    ) -> str:
        """Format query result based on output format.

        Args:
            data: Query result data
            format_type: Output format type
            title: Optional title for the result
            ai_comment: Optional AI-generated comment

        Returns:
            Formatted string representation
        """
        if ai_comment:
            self._console.print(f"[dim]{ai_comment}[/dim]")

        if format_type == OutputFormat.JSON:
            return self._format_json(data, title)
        elif format_type == OutputFormat.YAML:
            return self._format_yaml(data, title)
        else:  # TABLE
            return self._format_table(data, title)

    def _format_json(self, data: Any, title: str | None = None) -> str:
        """Format data as JSON."""
        if title:
            self._console.print(f"\n[bold]{title}[/bold]")
        formatted = json.dumps(data, indent=2, default=str)
        self._console.print(formatted)
        return formatted

    def _format_yaml(self, data: Any, title: str | None = None) -> str:
        """Format data as YAML."""
        if title:
            self._console.print(f"\n[bold]{title}[/bold]")
        formatted = yaml.dump(data, default_flow_style=False, sort_keys=False)
        self._console.print(formatted)
        return str(formatted)

    def _format_table(self, data: Any, title: str | None = None) -> str:
        """Format data as table."""
        if not data:
            self._console.print("[dim]No results[/dim]")
            return "No results"

        # Handle different data structures
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                return self._format_dict_list_table(data, title)
            else:
                return self._format_simple_list_table(data, title)
        elif isinstance(data, dict):
            return self._format_dict_table(data, title)
        else:
            # Fallback to string representation
            formatted = str(data)
            if title:
                self._console.print(f"\n[bold]{title}[/bold]")
            self._console.print(formatted)
            return formatted

    def _format_dict_list_table(self, data: list[dict[str, Any]], title: str | None = None) -> str:
        """Format list of dictionaries as table."""
        if not data:
            return "No results"

        # Get all unique keys
        all_keys: set[str] = set()
        for row in data:
            all_keys.update(row.keys())
        columns = sorted(all_keys)

        # Create Rich table
        table = Table(
            title=title, show_header=True, header_style="bold cyan", width=self._max_width
        )

        # Add columns
        for col in columns:
            table.add_column(col, overflow="fold")

        # Add rows
        for row in data:
            values = []
            for col in columns:
                value = row.get(col, "")
                # Handle nested structures
                if isinstance(value, dict | list):
                    value = json.dumps(value, default=str)
                else:
                    value = str(value)
                values.append(value)
            table.add_row(*values)

        self._console.print(table)

        # Also return tabulate version for string representation
        table_data = []
        for row in data:
            table_data.append([str(row.get(col, "")) for col in columns])
        return str(tabulate(table_data, headers=columns, tablefmt="grid"))

    def _format_simple_list_table(self, data: list[Any], title: str | None = None) -> str:
        """Format simple list as table."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Value", overflow="fold")

        for item in data:
            value = json.dumps(item, default=str) if isinstance(item, dict | list) else str(item)
            table.add_row(value)

        self._console.print(table)

        # Return tabulate version
        table_data = [[str(item)] for item in data]
        return str(tabulate(table_data, headers=["Value"], tablefmt="grid"))

    def _format_dict_table(self, data: dict[str, Any], title: str | None = None) -> str:
        """Format dictionary as table."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", overflow="fold")
        table.add_column("Value", overflow="fold")

        for key, value in data.items():
            if isinstance(value, dict | list):
                value_str = json.dumps(value, indent=2, default=str)
            else:
                value_str = str(value)
            table.add_row(key, value_str)

        self._console.print(table)

        # Return tabulate version
        table_data = [[k, str(v)] for k, v in data.items()]
        return str(tabulate(table_data, headers=["Key", "Value"], tablefmt="grid"))

    def format_error(self, error: str) -> None:
        """Format and display error message."""
        self._console.print(f"[red]Error:[/red] {error}")

    def format_success(self, message: str) -> None:
        """Format and display success message."""
        self._console.print(f"[green]✓[/green] {message}")

    def format_info(self, message: str) -> None:
        """Format and display info message."""
        self._console.print(f"[blue]Info:[/blue] {message}")

    def format_warning(self, message: str) -> None:
        """Format and display warning message."""
        self._console.print(f"[yellow]⚠[/yellow] {message}")
