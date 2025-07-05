"""Safe code execution for constraints and validations."""

import logging
from typing import Any, Optional, Callable, Dict
from RestrictedPython import compile_restricted, safe_globals

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
    ) -> Optional[Callable[..., Any]]:
        """Compile and return a function from code."""
        try:
            # Compile with restrictions
            byte_code = compile_restricted(
                code,
                filename=f"<{function_name}>",
                mode="exec"
            )
            
            if byte_code.errors:
                logger.error(f"Compilation errors: {'; '.join(byte_code.errors)}")
                return None
            
            # Execute in safe environment
            exec_globals = self._safe_globals.copy()
            exec_locals: Dict[str, Any] = {}
            
            exec(byte_code.code, exec_globals, exec_locals)
            
            # Return the function
            return exec_locals.get(function_name)
            
        except Exception as e:
            logger.error(f"Failed to execute function {function_name}: {e}")
            return None
    
    async def evaluate_expression(
        self, 
        expression: str, 
        context: Dict[str, Any],
    ) -> Any:
        """Evaluate a Python expression safely."""
        try:
            # Compile expression
            byte_code = compile_restricted(
                expression,
                filename="<expression>",
                mode="eval"
            )
            
            if byte_code.errors:
                raise ValidationError(f"Expression compilation failed: {'; '.join(byte_code.errors)}")
            
            # Create evaluation environment
            eval_globals = self._safe_globals.copy()
            eval_globals.update(context)
            
            # Evaluate
            return eval(byte_code.code, eval_globals)
            
        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            raise ValidationError(f"Expression evaluation failed: {str(e)}")
    
    def _create_safe_globals(self) -> Dict[str, Any]:
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
        }
        
        globals_dict['__builtins__'] = safe_builtins
        
        return globals_dict