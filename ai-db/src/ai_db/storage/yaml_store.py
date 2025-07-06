"""YAML storage operations for AI-DB."""

from pathlib import Path
from typing import Dict, List, Any
import logging
import yaml
import aiofiles

from ai_db.exceptions import StorageError
from ai_shared.protocols import TransactionProtocol

logger = logging.getLogger(__name__)


class YAMLStore:
    """Handles YAML file operations for data storage."""
    
    def __init__(self, transaction_context: TransactionProtocol) -> None:
        self._transaction_context = transaction_context
        self._base_path = Path(transaction_context.path)
    
    async def read_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Read table data from YAML file."""
        file_path = self._get_table_path(table_name)
        
        if not file_path.exists():
            logger.info(f"Table {table_name} does not exist, returning empty list")
            return []
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = yaml.safe_load(content)
                
                if data is None:
                    return []
                
                if not isinstance(data, list):
                    raise StorageError(f"Invalid table format for {table_name}: expected list, got {type(data)}")
                
                return data
        except yaml.YAMLError as e:
            raise StorageError(f"Failed to parse YAML for table {table_name}: {e}")
        except Exception as e:
            raise StorageError(f"Failed to read table {table_name}: {e}")
    
    async def write_table(self, table_name: str, data: List[Dict[str, Any]]) -> None:
        """Write table data to YAML file."""
        # Ensure write escalation
        await self._transaction_context.write_escalation_required()
        
        file_path = self._get_table_path(table_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            yaml_content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(yaml_content)
            logger.info(f"Successfully wrote {len(data)} records to table {table_name}")
            await self._transaction_context.operation_complete(f"Wrote {len(data)} records to table {table_name}")
        except Exception as e:
            await self._transaction_context.operation_failed(f"Failed to write table {table_name}: {e}")
            raise StorageError(f"Failed to write table {table_name}: {e}")
    
    async def delete_table(self, table_name: str) -> None:
        """Delete a table's YAML file."""
        # Ensure write escalation
        await self._transaction_context.write_escalation_required()
        
        file_path = self._get_table_path(table_name)
        
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted table {table_name}")
                await self._transaction_context.operation_complete(f"Deleted table {table_name}")
            except Exception as e:
                await self._transaction_context.operation_failed(f"Failed to delete table {table_name}: {e}")
                raise StorageError(f"Failed to delete table {table_name}: {e}")
    
    async def list_tables(self) -> List[str]:
        """List all table names."""
        tables_dir = self._base_path / "tables"
        
        if not tables_dir.exists():
            return []
        
        tables = []
        for file_path in tables_dir.glob("*.yaml"):
            tables.append(file_path.stem)
        
        return sorted(tables)
    
    async def read_file(self, relative_path: str) -> str:
        """Read any file content."""
        file_path = self._base_path / relative_path
        
        if not file_path.exists():
            raise StorageError(f"File {relative_path} does not exist")
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                return await f.read()
        except Exception as e:
            raise StorageError(f"Failed to read file {relative_path}: {e}")
    
    async def write_file(self, relative_path: str, content: str) -> None:
        """Write any file content."""
        # Ensure write escalation
        await self._transaction_context.write_escalation_required()
        
        file_path = self._base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(content)
            logger.info(f"Successfully wrote file {relative_path}")
            await self._transaction_context.operation_complete(f"Wrote file {relative_path}")
        except Exception as e:
            await self._transaction_context.operation_failed(f"Failed to write file {relative_path}: {e}")
            raise StorageError(f"Failed to write file {relative_path}: {e}")
    
    def _get_table_path(self, table_name: str) -> Path:
        """Get the file path for a table."""
        return self._base_path / "tables" / f"{table_name}.yaml"