"""Permission level inference for AI-DB operations."""

import re
from typing import Optional
from .models.ai_db import PermissionLevel


class PermissionInferrer:
    """Infer permission levels from query text."""
    
    # Patterns for different operation types
    SCHEMA_MODIFY_PATTERNS = [
        r"\b(create|alter|drop|rename)\s+(table|schema|database)\b",
        r"\b(add|drop|modify|rename)\s+(column|constraint|index)\b",
        r"\b(create|drop)\s+type\b",
    ]
    
    DATA_MODIFY_PATTERNS = [
        r"\b(insert|update|delete|merge|upsert)\s+(into|from)?\b",
        r"\b(truncate)\s+table\b",
        r"\bcopy\s+.*\s+(from|to)\b",
    ]
    
    VIEW_MODIFY_PATTERNS = [
        r"\b(create|alter|drop|replace)\s+(view|materialized\s+view)\b",
        r"\brefresh\s+materialized\s+view\b",
    ]
    
    SELECT_PATTERNS = [
        r"\bselect\s+",
        r"\bwith\s+.*\s+as\s*\(",  # CTE queries
        r"\bshow\s+",
        r"\bdescribe\s+",
        r"\bexplain\s+",
    ]
    
    @classmethod
    def infer_permission_level(cls, query: str) -> PermissionLevel:
        """Infer the required permission level from a query."""
        query_lower = query.lower().strip()
        
        # Check patterns in order of destructiveness
        if cls._matches_any_pattern(query_lower, cls.SCHEMA_MODIFY_PATTERNS):
            return PermissionLevel.SCHEMA_MODIFY
        
        if cls._matches_any_pattern(query_lower, cls.VIEW_MODIFY_PATTERNS):
            return PermissionLevel.VIEW_MODIFY
        
        if cls._matches_any_pattern(query_lower, cls.DATA_MODIFY_PATTERNS):
            return PermissionLevel.DATA_MODIFY
        
        if cls._matches_any_pattern(query_lower, cls.SELECT_PATTERNS):
            return PermissionLevel.SELECT
        
        # Default to SELECT for unrecognized patterns
        # (better to under-permission than over-permission)
        return PermissionLevel.SELECT
    
    @staticmethod
    def _matches_any_pattern(text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the patterns."""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    @classmethod
    def validate_permission(
        cls,
        query: str,
        provided_permission: Optional[PermissionLevel] = None,
    ) -> tuple[bool, PermissionLevel, Optional[str]]:
        """
        Validate if the provided permission is sufficient for the query.
        
        Returns:
            - is_valid: Whether the permission is sufficient
            - required_permission: The minimum required permission
            - error_message: Error message if invalid
        """
        required_permission = cls.infer_permission_level(query)
        
        if provided_permission is None:
            return True, required_permission, None
        
        # Permission hierarchy: SELECT < DATA_MODIFY < VIEW_MODIFY < SCHEMA_MODIFY
        permission_hierarchy = {
            PermissionLevel.SELECT: 0,
            PermissionLevel.DATA_MODIFY: 1,
            PermissionLevel.VIEW_MODIFY: 2,
            PermissionLevel.SCHEMA_MODIFY: 3,
        }
        
        provided_level = permission_hierarchy.get(provided_permission, 0)
        required_level = permission_hierarchy.get(required_permission, 0)
        
        if provided_level < required_level:
            return (
                False,
                required_permission,
                f"Insufficient permission: {provided_permission.value} provided, "
                f"but {required_permission.value} required",
            )
        
        return True, required_permission, None