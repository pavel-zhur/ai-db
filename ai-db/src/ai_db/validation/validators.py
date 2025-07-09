"""Data validation using JSON Schema."""

import logging
from typing import Any

from jsonschema import Draft7Validator, validate
from jsonschema import ValidationError as JsonSchemaError

from ai_db.core.models import Column, Table
from ai_db.exceptions import ValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data against table schemas."""

    def validate_row(self, row: dict[str, Any], table: Table) -> None:
        """Validate a single row against table schema."""
        schema = self._table_to_json_schema(table)

        try:
            validate(instance=row, schema=schema)
        except JsonSchemaError as e:
            raise ValidationError(
                f"Row validation failed for table {table.name}: {e.message}", details=[str(e)]
            ) from e

    def validate_rows(self, rows: list[dict[str, Any]], table: Table) -> list[str]:
        """Validate multiple rows and return all errors."""
        errors = []
        schema = self._table_to_json_schema(table)
        validator = Draft7Validator(schema)

        for i, row in enumerate(rows):
            row_errors = list(validator.iter_errors(row))
            for error in row_errors:
                errors.append(f"Row {i}: {error.message}")

        return errors

    def validate_table_data(
        self,
        data: list[dict[str, Any]],
        table: Table,
        raise_on_error: bool = True,
    ) -> list[str] | None:
        """Validate all data in a table."""
        errors = self.validate_rows(data, table)

        if errors and raise_on_error:
            raise ValidationError(
                f"Table {table.name} validation failed", details=errors[:10]  # Limit error details
            )

        return errors if errors else None

    def _table_to_json_schema(self, table: Table) -> dict[str, Any]:
        """Convert table definition to JSON Schema."""
        properties = {}
        required = []

        for column in table.columns:
            col_schema = self._column_to_json_schema(column)
            properties[column.name] = col_schema

            if not column.nullable and column.default is None:
                required.append(column.name)

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

        return schema

    def _column_to_json_schema(self, column: Column) -> dict[str, Any]:
        """Convert column definition to JSON Schema property."""
        # Map database types to JSON Schema types
        type_mapping = {
            "string": "string",
            "text": "string",
            "integer": "integer",
            "bigint": "integer",
            "float": "number",
            "double": "number",
            "decimal": "number",
            "boolean": "boolean",
            "date": "string",  # with format
            "datetime": "string",  # with format
            "time": "string",  # with format
            "array": "array",
            "object": "object",
        }

        json_type = type_mapping.get(column.type.lower(), "string")

        schema: dict[str, Any] = {"type": json_type}

        # Add format for date/time types
        if column.type.lower() == "date":
            schema["format"] = "date"
        elif column.type.lower() == "datetime":
            schema["format"] = "date-time"
        elif column.type.lower() == "time":
            schema["format"] = "time"

        # Handle nullable
        if column.nullable:
            schema = {"anyOf": [schema, {"type": "null"}]}

        # Add description
        if column.description:
            schema["description"] = column.description

        return schema
