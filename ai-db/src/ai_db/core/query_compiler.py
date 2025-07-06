"""Query compilation and execution for AI-DB."""

import ast
import base64
import logging
import marshal
import pickle
from collections.abc import Callable
from typing import Any

from RestrictedPython import compile_restricted_exec, safe_globals

from ai_db.exceptions import CompilationError

logger = logging.getLogger(__name__)


class QueryCompiler:
    """Compiles and executes Python query code."""

    def __init__(self) -> None:
        self._safe_globals = self._create_safe_globals()

    def compile_query(self, python_code: str) -> str:
        """Compile Python code to a serialized query plan."""
        try:
            # Validate the Python code
            self._validate_code(python_code)

            # Compile with restrictions using new API
            result = compile_restricted_exec(python_code, filename="<query>")

            if result.errors:
                raise CompilationError(f"Compilation errors: {'; '.join(result.errors)}")

            byte_code = result.code

            if result.warnings:
                logger.warning(f"Compilation warnings: {'; '.join(result.warnings)}")

            # Serialize the compiled code and source
            query_plan = {
                "source": python_code,
                "byte_code": base64.b64encode(marshal.dumps(byte_code)).decode('utf-8'),
            }

            # Return as base64-encoded pickle
            return base64.b64encode(pickle.dumps(query_plan)).decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to compile query: {e}")
            raise CompilationError(f"Failed to compile query: {e!s}")

    def execute_compiled(
        self,
        compiled_plan: str,
        table_data: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Execute a compiled query plan."""
        try:
            # Deserialize the query plan
            query_plan = pickle.loads(base64.b64decode(compiled_plan))

            # Create execution environment
            exec_globals = self._safe_globals.copy()
            exec_globals['__tables__'] = table_data
            exec_locals: dict[str, Any] = {}

            # Deserialize and execute the byte code
            byte_code = marshal.loads(base64.b64decode(query_plan['byte_code']))
            exec(byte_code, exec_globals, exec_locals)

            # Find and call the query function
            query_func = None
            for name, obj in exec_locals.items():
                if callable(obj) and name.startswith('query_'):
                    query_func = obj
                    break

            if not query_func:
                raise CompilationError("No query function found in compiled code")

            # Execute the query
            result = query_func(table_data)

            # Ensure result is a list of dictionaries
            if not isinstance(result, list):
                raise CompilationError("Query must return a list")

            return result

        except Exception as e:
            logger.error(f"Failed to execute compiled query: {e}")
            raise CompilationError(f"Failed to execute query: {e!s}")


    def _validate_code(self, python_code: str) -> None:
        """Validate Python code for safety."""
        try:
            # Parse the code to check syntax
            tree = ast.parse(python_code)

            # Check for forbidden constructs
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    raise CompilationError("Import statements are not allowed")
                elif isinstance(node, ast.ImportFrom):
                    raise CompilationError("Import statements are not allowed")
                elif isinstance(node, (ast.Exec, ast.Eval)) if hasattr(ast, 'Exec') else False:
                    raise CompilationError("Exec/eval statements are not allowed")
                elif isinstance(node, ast.Global):
                    raise CompilationError("Global statements are not allowed")
                elif isinstance(node, ast.Nonlocal):
                    raise CompilationError("Nonlocal statements are not allowed")

            # Ensure there's at least one function definition
            has_function = any(isinstance(node, ast.FunctionDef) for node in tree.body)
            if not has_function:
                raise CompilationError("Query code must define at least one function")

        except SyntaxError as e:
            raise CompilationError(f"Syntax error: {e}")

    def _create_safe_globals(self) -> dict[str, Any]:
        """Create safe global environment for query execution."""
        # Start with RestrictedPython's safe globals
        globals_dict = safe_globals.copy()

        # Add safe built-ins
        safe_builtins = {
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'reversed': reversed,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'all': all,
            'any': any,
            'bool': bool,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'isinstance': isinstance,
            'type': type,
        }

        globals_dict['__builtins__'] = safe_builtins

        # Add utility functions for queries
        globals_dict.update({
            'group_by': self._group_by,
            'aggregate': self._aggregate,
            'join_tables': self._join_tables,
        })

        # Add required RestrictedPython functions
        safe_builtins = globals_dict.get('__builtins__', {})
        safe_builtins.update({
            '_getattr_': getattr,
            '_getitem_': lambda obj, index: obj[index],
            '_getiter_': iter,
            '_iter_unpack_sequence_': lambda it, spec: list(it),
        })
        globals_dict['__builtins__'] = safe_builtins

        return globals_dict

    @staticmethod
    def _group_by(data: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
        """Group data by a key."""
        groups: dict[Any, list[dict[str, Any]]] = {}
        for row in data:
            group_key = row.get(key)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(row)
        return groups

    @staticmethod
    def _aggregate(
        data: list[dict[str, Any]],
        agg_func: Callable[[list[Any]], Any],
        field: str,
    ) -> Any:
        """Apply an aggregation function to a field."""
        values = [row.get(field) for row in data if field in row]
        return agg_func(values) if values else None

    @staticmethod
    def _join_tables(
        left: list[dict[str, Any]],
        right: list[dict[str, Any]],
        left_key: str,
        right_key: str,
        join_type: str = "inner",
    ) -> list[dict[str, Any]]:
        """Join two tables."""
        result = []

        if join_type == "inner":
            for left_row in left:
                left_val = left_row.get(left_key)
                for right_row in right:
                    if right_row.get(right_key) == left_val:
                        joined = left_row.copy()
                        joined.update(right_row)
                        result.append(joined)

        elif join_type == "left":
            for left_row in left:
                left_val = left_row.get(left_key)
                matched = False
                for right_row in right:
                    if right_row.get(right_key) == left_val:
                        joined = left_row.copy()
                        joined.update(right_row)
                        result.append(joined)
                        matched = True
                if not matched:
                    result.append(left_row.copy())

        return result
