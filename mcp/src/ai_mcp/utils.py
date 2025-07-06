"""Utility functions for MCP servers."""

import importlib
from typing import Optional


def try_import(module_name: str, class_name: str) -> Optional[type]:
    """Try to import a class from a module."""
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        return None


def check_dependencies() -> tuple[bool, bool]:
    """Check if AI-DB and AI-Frontend are available."""
    ai_db_available = try_import("ai_db", "AIDB") is not None
    ai_frontend_available = try_import("ai_frontend", "AIFrontend") is not None
    return ai_db_available, ai_frontend_available
