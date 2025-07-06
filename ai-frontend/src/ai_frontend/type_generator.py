"""TypeScript type generation from AI-DB schemas."""

import json
import logging
from typing import Any, Dict, List, Optional, Set

from ai_frontend.utils import to_pascal_case

logger = logging.getLogger(__name__)


class TypeScriptGenerator:
    """Generate TypeScript types from JSON schemas."""
    
    def __init__(self):
        self._generated_types: Set[str] = set()
        
    def generate_from_schema(self, schema: Dict[str, Any]) -> str:
        """Generate TypeScript types from AI-DB schema.
        
        Args:
            schema: AI-DB schema dictionary
            
        Returns:
            TypeScript type definitions
        """
        self._generated_types.clear()
        
        lines = [
            "// Auto-generated TypeScript types from AI-DB schema",
            "// Do not edit manually - regenerate from schema instead",
            "",
        ]
        
        # Generate types for each table
        if "tables" in schema:
            for table_name, table_schema in schema["tables"].items():
                lines.extend(self._generate_table_types(table_name, table_schema))
                lines.append("")
        
        # Generate view types if present
        if "views" in schema:
            for view_name, view_schema in schema["views"].items():
                lines.extend(self._generate_view_types(view_name, view_schema))
                lines.append("")
        
        # Generate API response types
        lines.extend(self._generate_api_types())
        
        return "\n".join(lines)
    
    def _generate_table_types(
        self, table_name: str, table_schema: Dict[str, Any]
    ) -> List[str]:
        """Generate types for a single table."""
        type_name = to_pascal_case(table_name)
        self._generated_types.add(type_name)
        
        lines = [f"export interface {type_name} {{"]
        
        # Add fields from columns
        if "columns" in table_schema:
            for col_name, col_schema in table_schema["columns"].items():
                ts_type = self._json_schema_to_ts_type(col_schema)
                optional = col_schema.get("nullable", False) or not col_schema.get(
                    "required", True
                )
                field_name = col_name
                
                if optional:
                    lines.append(f"  {field_name}?: {ts_type};")
                else:
                    lines.append(f"  {field_name}: {ts_type};")
        
        lines.append("}")
        
        # Generate create/update DTOs
        lines.extend(self._generate_dto_types(type_name, table_schema))
        
        return lines
    
    def _generate_view_types(
        self, view_name: str, view_schema: Dict[str, Any]
    ) -> List[str]:
        """Generate types for a view."""
        type_name = to_pascal_case(view_name) + "View"
        self._generated_types.add(type_name)
        
        lines = [f"export interface {type_name} {{"]
        
        # Views should have their result schema defined
        if "result_schema" in view_schema:
            for field_name, field_schema in view_schema["result_schema"].items():
                ts_type = self._json_schema_to_ts_type(field_schema)
                optional = field_schema.get("nullable", False)
                
                if optional:
                    lines.append(f"  {field_name}?: {ts_type};")
                else:
                    lines.append(f"  {field_name}: {ts_type};")
        
        lines.append("}")
        
        return lines
    
    def _generate_dto_types(
        self, base_type: str, table_schema: Dict[str, Any]
    ) -> List[str]:
        """Generate Data Transfer Object types for create/update operations."""
        lines = []
        
        # Create DTO - exclude auto-generated fields
        create_type = f"Create{base_type}DTO"
        lines.append(f"export interface {create_type} {{")
        
        if "columns" in table_schema:
            for col_name, col_schema in table_schema["columns"].items():
                # Skip auto-generated fields
                if col_schema.get("auto_increment") or col_schema.get("generated"):
                    continue
                    
                ts_type = self._json_schema_to_ts_type(col_schema)
                optional = col_schema.get("nullable", False) or col_schema.get(
                    "default"
                ) is not None
                
                if optional:
                    lines.append(f"  {col_name}?: {ts_type};")
                else:
                    lines.append(f"  {col_name}: {ts_type};")
        
        lines.append("}")
        lines.append("")
        
        # Update DTO - all fields optional
        update_type = f"Update{base_type}DTO"
        lines.append(f"export interface {update_type} {{")
        
        if "columns" in table_schema:
            for col_name, col_schema in table_schema["columns"].items():
                # Skip immutable fields
                if col_schema.get("immutable") or col_schema.get("auto_increment"):
                    continue
                    
                ts_type = self._json_schema_to_ts_type(col_schema)
                lines.append(f"  {col_name}?: {ts_type};")
        
        lines.append("}")
        
        return lines
    
    def _generate_api_types(self) -> List[str]:
        """Generate common API response types."""
        return [
            "// API Response Types",
            "export interface ApiResponse<T> {",
            "  success: boolean;",
            "  data?: T;",
            "  error?: string;",
            "  message?: string;",
            "}",
            "",
            "export interface QueryResult<T> {",
            "  rows: T[];",
            "  total: number;",
            "  page?: number;",
            "  pageSize?: number;",
            "}",
            "",
            "export interface MutationResult {",
            "  success: boolean;",
            "  affectedRows: number;",
            "  id?: string | number;",
            "  message?: string;",
            "}",
            "",
            "export interface ValidationError {",
            "  field: string;",
            "  message: string;",
            "  code?: string;",
            "}",
            "",
            "export interface ApiError {",
            "  message: string;",
            "  code?: string;",
            "  details?: ValidationError[];",
            "}",
        ]
    
    def _json_schema_to_ts_type(self, schema: Dict[str, Any]) -> str:
        """Convert JSON schema type to TypeScript type."""
        if "type" not in schema:
            return "any"
        
        json_type = schema["type"]
        
        # Handle arrays
        if json_type == "array":
            items_type = "any"
            if "items" in schema:
                items_type = self._json_schema_to_ts_type(schema["items"])
            return f"{items_type}[]"
        
        # Handle objects
        if json_type == "object":
            if "properties" in schema:
                # Inline object type
                props = []
                for prop_name, prop_schema in schema["properties"].items():
                    prop_type = self._json_schema_to_ts_type(prop_schema)
                    required = prop_name in schema.get("required", [])
                    optional_mark = "" if required else "?"
                    props.append(f"{prop_name}{optional_mark}: {prop_type}")
                return f"{{ {'; '.join(props)} }}"
            return "Record<string, any>"
        
        # Handle enums
        if "enum" in schema:
            enum_values = [f'"{v}"' if isinstance(v, str) else str(v) for v in schema["enum"]]
            return " | ".join(enum_values)
        
        # Handle formats
        if "format" in schema:
            format_type = schema["format"]
            if format_type in ["date", "date-time"]:
                return "string"  # or Date, depending on preference
            elif format_type == "uuid":
                return "string"
        
        # Basic type mapping
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "null": "null",
        }
        
        return type_map.get(json_type, "any")