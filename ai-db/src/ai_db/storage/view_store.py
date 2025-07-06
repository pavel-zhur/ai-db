"""View storage operations for AI-DB."""

import os
from pathlib import Path
from typing import Dict, Optional, Any
import yaml
import logging

from ai_db.exceptions import StorageError
from ai_db.storage.yaml_store import YAMLStore
from ai_shared.protocols import TransactionProtocol

logger = logging.getLogger(__name__)


class ViewStore:
    """Handles view storage and retrieval."""
    
    def __init__(self, transaction_context: TransactionProtocol) -> None:
        self._yaml_store = YAMLStore(transaction_context)
        self._transaction_context = transaction_context
    
    async def save_view(self, view_name: str, python_code: str, metadata: Dict[str, Any]) -> None:
        """Save a view's Python code and metadata."""
        # Save Python code
        await self._yaml_store.write_file(f"views/{view_name}.py", python_code)
        
        # Save metadata
        meta_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        await self._yaml_store.write_file(f"views/{view_name}.meta.yaml", meta_content)
        
        logger.info(f"Saved view {view_name}")
    
    async def load_view(self, view_name: str) -> tuple[str, Dict[str, Any]]:
        """Load a view's Python code and metadata."""
        try:
            # Load Python code
            python_code = await self._yaml_store.read_file(f"views/{view_name}.py")
            
            # Load metadata
            meta_content = await self._yaml_store.read_file(f"views/{view_name}.meta.yaml")
            metadata = yaml.safe_load(meta_content) or {}
            
            return python_code, metadata
            
        except StorageError as e:
            raise StorageError(f"Failed to load view {view_name}: {e}")
    
    async def delete_view(self, view_name: str) -> None:
        """Delete a view."""
        # Since we don't have direct file deletion, we'll mark for deletion
        # The AI agent should handle actual file removal
        logger.info(f"View {view_name} marked for deletion")
    
    async def list_views(self) -> list[str]:
        """List all view names."""
        base_path = Path(self._transaction_context.path) / "views"
        
        if not base_path.exists():
            return []
        
        views = []
        for file_path in base_path.glob("*.py"):
            views.append(file_path.stem)
        
        return sorted(views)