"""Safe code execution for constraints and validations."""

import logging
from collections.abc import Callable
from typing import Any

from RestrictedPython import compile_restricted_eval, compile_restricted_exec, safe_globals

from ai_db.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SafeExecutor:
    """Executes Python code in a restricted environment."""

    def __init__(self) -> None:
        self._safe_globals = self._create_safe_globals()

    async def execute_function(
        self,
        code: str,
        function_name: str,
    ) -> Callable[..., Any] | None:
        """Compile and return a function from code."""
        try:
            # Compile with restrictions using new API
            result = compile_restricted_exec(code, filename=f"<{function_name}>")

            if result.errors:
                logger.error(f"Compilation errors: {'; '.join(result.errors)}")
                return None

            byte_code = result.code

            # Execute in safe environment
            exec_globals = self._safe_globals.copy()
            exec_locals: dict[str, Any] = {}

            exec(byte_code, exec_globals, exec_locals)

            # Return the function
            return exec_locals.get(function_name)

        except Exception as e:
            logger.error(f"Failed to execute function {function_name}: {e}")
            return None

    async def evaluate_expression(
        self,
        expression: str,
        context: dict[str, Any],
    ) -> Any:
        """Evaluate a Python expression safely."""
        try:
            # Compile expression using new API
            result = compile_restricted_eval(expression, filename="<expression>")

            if result.errors:
                raise ValidationError(f"Expression compilation failed: {'; '.join(result.errors)}")

            byte_code = result.code

            # Create evaluation environment
            eval_globals = self._safe_globals.copy()
            eval_globals.update(context)

            # Evaluate
            return eval(byte_code, eval_globals)

        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            raise ValidationError(f"Expression evaluation failed: {e!s}") from e

    def _create_safe_globals(self) -> dict[str, Any]:
        """Create safe global environment."""
        globals_dict = safe_globals.copy()

        # Safe built-ins for constraints
        safe_builtins = {
            # Comparison and logic
            'True': True,
            'False': False,
            'None': None,

            # Type checking
            'bool': bool,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'isinstance': isinstance,
            'type': type,

            # Math operations
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
            'sum': sum,

            # String operations
            'len': len,

            # Safe functions
            'all': all,
            'any': any,
            'zip': zip,
            'range': range,

            # Required for RestrictedPython
            '_getattr_': getattr,
            '_getitem_': lambda obj, index: obj[index],
            '_getiter_': iter,
            '_iter_unpack_sequence_': lambda it, spec: list(it),
        }

        globals_dict['__builtins__'] = safe_builtins

        return globals_dict
