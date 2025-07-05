"""Constraint checking for AI-DB."""

import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from ai_db.core.models import Table, Constraint, ConstraintType
from ai_db.exceptions import ConstraintViolationError
from ai_db.validation.sandbox import SafeExecutor

logger = logging.getLogger(__name__)


class ConstraintChecker:
    """Checks database constraints."""
    
    def __init__(self, safe_executor: SafeExecutor) -> None:
        self._safe_executor = safe_executor
    
    async def check_constraints(
        self,
        table: Table,
        data: List[Dict[str, Any]],
        all_tables_data: Dict[str, List[Dict[str, Any]]],
    ) -> List[str]:
        """Check all constraints for table data."""
        errors = []
        
        for constraint in table.constraints:
            try:
                if constraint.type == ConstraintType.PRIMARY_KEY:
                    self._check_primary_key(constraint, data, errors)
                elif constraint.type == ConstraintType.UNIQUE:
                    self._check_unique(constraint, data, errors)
                elif constraint.type == ConstraintType.NOT_NULL:
                    self._check_not_null(constraint, data, errors)
                elif constraint.type == ConstraintType.FOREIGN_KEY:
                    self._check_foreign_key(constraint, data, all_tables_data, errors)
                elif constraint.type == ConstraintType.CHECK:
                    await self._check_check_constraint(constraint, data, errors)
            except Exception as e:
                errors.append(f"Error checking constraint {constraint.name}: {str(e)}")
        
        return errors
    
    def _check_primary_key(
        self, 
        constraint: Constraint, 
        data: List[Dict[str, Any]], 
        errors: List[str],
    ) -> None:
        """Check primary key constraint."""
        seen_keys: Set[tuple] = set()
        
        for i, row in enumerate(data):
            # Extract key values
            key_values = []
            for col in constraint.columns:
                value = row.get(col)
                if value is None:
                    errors.append(
                        f"Row {i}: Primary key column '{col}' cannot be NULL"
                    )
                    continue
                key_values.append(value)
            
            if not key_values:
                continue
                
            key_tuple = tuple(key_values)
            if key_tuple in seen_keys:
                errors.append(
                    f"Row {i}: Duplicate primary key {dict(zip(constraint.columns, key_values))}"
                )
            else:
                seen_keys.add(key_tuple)
    
    def _check_unique(
        self, 
        constraint: Constraint, 
        data: List[Dict[str, Any]], 
        errors: List[str],
    ) -> None:
        """Check unique constraint."""
        seen_values: Set[tuple] = set()
        
        for i, row in enumerate(data):
            # Extract values
            values = []
            all_null = True
            for col in constraint.columns:
                value = row.get(col)
                values.append(value)
                if value is not None:
                    all_null = False
            
            # Skip if all values are NULL
            if all_null:
                continue
            
            value_tuple = tuple(values)
            if value_tuple in seen_values:
                errors.append(
                    f"Row {i}: Duplicate unique constraint {dict(zip(constraint.columns, values))}"
                )
            else:
                seen_values.add(value_tuple)
    
    def _check_not_null(
        self, 
        constraint: Constraint, 
        data: List[Dict[str, Any]], 
        errors: List[str],
    ) -> None:
        """Check NOT NULL constraint."""
        for i, row in enumerate(data):
            for col in constraint.columns:
                if row.get(col) is None:
                    errors.append(f"Row {i}: Column '{col}' cannot be NULL")
    
    def _check_foreign_key(
        self,
        constraint: Constraint,
        data: List[Dict[str, Any]],
        all_tables_data: Dict[str, List[Dict[str, Any]]],
        errors: List[str],
    ) -> None:
        """Check foreign key constraint."""
        if not constraint.referenced_table or not constraint.referenced_columns:
            errors.append(f"Foreign key {constraint.name} missing reference information")
            return
        
        # Get referenced table data
        ref_data = all_tables_data.get(constraint.referenced_table, [])
        if not ref_data:
            # Empty referenced table - all non-null FKs are violations
            for i, row in enumerate(data):
                fk_values = [row.get(col) for col in constraint.columns]
                if any(v is not None for v in fk_values):
                    errors.append(
                        f"Row {i}: Foreign key references non-existent table {constraint.referenced_table}"
                    )
            return
        
        # Build index of referenced values
        ref_index: Set[tuple] = set()
        for ref_row in ref_data:
            ref_values = []
            for col in constraint.referenced_columns:
                ref_values.append(ref_row.get(col))
            ref_index.add(tuple(ref_values))
        
        # Check each row
        for i, row in enumerate(data):
            fk_values = []
            all_null = True
            for col in constraint.columns:
                value = row.get(col)
                fk_values.append(value)
                if value is not None:
                    all_null = False
            
            # Skip if all FK columns are NULL
            if all_null:
                continue
            
            fk_tuple = tuple(fk_values)
            if fk_tuple not in ref_index:
                errors.append(
                    f"Row {i}: Foreign key violation - {dict(zip(constraint.columns, fk_values))} "
                    f"not found in {constraint.referenced_table}"
                )
    
    async def _check_check_constraint(
        self,
        constraint: Constraint,
        data: List[Dict[str, Any]],
        errors: List[str],
    ) -> None:
        """Check CHECK constraint using Python expression."""
        if not constraint.definition:
            errors.append(f"CHECK constraint {constraint.name} has no definition")
            return
        
        # Generate validation function
        func_code = f"""
def check_{constraint.name}(row):
    # Extract column values
    {self._generate_column_extractors(constraint.columns)}
    
    # Evaluate constraint
    try:
        result = {constraint.definition}
        return bool(result)
    except:
        return False
"""
        
        # Execute safely
        check_func = await self._safe_executor.execute_function(
            func_code, 
            f"check_{constraint.name}"
        )
        
        if not check_func:
            errors.append(f"Failed to compile CHECK constraint {constraint.name}")
            return
        
        # Check each row
        for i, row in enumerate(data):
            try:
                if not check_func(row):
                    errors.append(
                        f"Row {i}: CHECK constraint {constraint.name} failed"
                    )
            except Exception as e:
                errors.append(
                    f"Row {i}: Error evaluating CHECK constraint {constraint.name}: {str(e)}"
                )
    
    def _generate_column_extractors(self, columns: List[str]) -> str:
        """Generate code to extract column values."""
        lines = []
        for col in columns:
            # Create safe variable name
            var_name = col.replace(" ", "_").replace("-", "_")
            lines.append(f"{var_name} = row.get('{col}')")
        return "\n    ".join(lines)