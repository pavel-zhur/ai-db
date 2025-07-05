"""API client generation for AI-DB integration."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from ai_frontend.type_generator import TypeScriptGenerator
from ai_frontend.utils import sanitize_component_name, to_camel_case, write_file

logger = logging.getLogger(__name__)


class ApiGenerator:
    """Generate API client code for AI-DB integration."""
    
    def __init__(self):
        self._type_generator = TypeScriptGenerator()
    
    async def generate_api_layer(
        self,
        project_dir: Path,
        schema: Dict[str, Any],
        api_base_url: str = "http://localhost:8000",
    ) -> None:
        """Generate complete API layer including types and service functions.
        
        Args:
            project_dir: Root directory of the React project
            schema: AI-DB schema dictionary
            api_base_url: Base URL for API calls
        """
        logger.info("Generating API layer from schema")
        
        # Generate TypeScript types
        types_content = self._type_generator.generate_from_schema(schema)
        await write_file(project_dir / "src/types/api.ts", types_content)
        
        # Generate service functions for each table
        if "tables" in schema:
            for table_name, table_schema in schema["tables"].items():
                service_content = self._generate_table_service(
                    table_name, table_schema
                )
                service_file = (
                    project_dir / f"src/api/services/{to_camel_case(table_name)}.ts"
                )
                await write_file(service_file, service_content)
        
        # Generate service index
        index_content = self._generate_services_index(schema.get("tables", {}))
        await write_file(project_dir / "src/api/services/index.ts", index_content)
        
        # Generate hooks for each table
        if "tables" in schema:
            for table_name in schema["tables"]:
                hook_content = self._generate_table_hooks(table_name)
                hook_file = (
                    project_dir / f"src/hooks/use{sanitize_component_name(table_name)}.ts"
                )
                await write_file(hook_file, hook_content)
        
        logger.info("API layer generated successfully")
    
    def _generate_table_service(
        self, table_name: str, table_schema: Dict[str, Any]
    ) -> str:
        """Generate service functions for a single table."""
        type_name = sanitize_component_name(table_name)
        service_name = to_camel_case(table_name)
        
        # Determine primary key field
        pk_field = "id"  # default
        if "columns" in table_schema:
            for col_name, col_schema in table_schema["columns"].items():
                if col_schema.get("primary_key"):
                    pk_field = col_name
                    break
        
        return f"""import {{ apiClient }} from '@/api/client'
import {{ {type_name}, Create{type_name}DTO, Update{type_name}DTO, QueryResult }} from '@/types/api'

export const {service_name}Service = {{
  async getAll(page = 1, pageSize = 20): Promise<QueryResult<{type_name}>> {{
    const offset = (page - 1) * pageSize
    return apiClient.query<{type_name}>(
      `SELECT * FROM {table_name} LIMIT ${{pageSize}} OFFSET ${{offset}}`
    )
  }},

  async getById(id: string | number): Promise<{type_name} | null> {{
    const result = await apiClient.query<{type_name}>(
      `SELECT * FROM {table_name} WHERE {pk_field} = '${{id}}' LIMIT 1`
    )
    return result.rows[0] || null
  }},

  async create(data: Create{type_name}DTO): Promise<{type_name}> {{
    const columns = Object.keys(data).join(', ')
    const values = Object.values(data).map(v => 
      typeof v === 'string' ? `'${{v}}'` : v
    ).join(', ')
    
    await apiClient.execute(
      `INSERT INTO {table_name} (${{columns}}) VALUES (${{values}})`,
      'data_modify'
    )
    
    // Fetch the created record (assuming auto-increment ID)
    const result = await apiClient.query<{type_name}>(
      `SELECT * FROM {table_name} ORDER BY {pk_field} DESC LIMIT 1`
    )
    return result.rows[0]
  }},

  async update(id: string | number, data: Update{type_name}DTO): Promise<{type_name}> {{
    const updates = Object.entries(data)
      .map(([key, value]) => {{
        const val = typeof value === 'string' ? `'${{value}}'` : value
        return `${{key}} = ${{val}}`
      }})
      .join(', ')
    
    await apiClient.execute(
      `UPDATE {table_name} SET ${{updates}} WHERE {pk_field} = '${{id}}'`,
      'data_modify'
    )
    
    return this.getById(id) as Promise<{type_name}>
  }},

  async delete(id: string | number): Promise<void> {{
    await apiClient.execute(
      `DELETE FROM {table_name} WHERE {pk_field} = '${{id}}'`,
      'data_modify'
    )
  }},

  async search(query: string): Promise<QueryResult<{type_name}>> {{
    // This is a simple search - Claude Code can enhance based on actual fields
    return apiClient.query<{type_name}>(
      `SELECT * FROM {table_name} WHERE {pk_field} LIKE '%${{query}}%'`
    )
  }},
}}"""
    
    def _generate_services_index(self, tables: Dict[str, Any]) -> str:
        """Generate index file for all services."""
        imports = []
        exports = []
        
        for table_name in tables:
            service_name = to_camel_case(table_name)
            imports.append(f"export {{ {service_name}Service }} from './{service_name}'")
        
        return "\n".join(imports)
    
    def _generate_table_hooks(self, table_name: str) -> str:
        """Generate React hooks for a table."""
        type_name = sanitize_component_name(table_name)
        service_name = to_camel_case(table_name)
        hook_name = f"use{type_name}"
        
        return f"""import {{ useState, useCallback }} from 'react'
import {{ {service_name}Service }} from '@/api/services/{service_name}'
import {{ {type_name}, Create{type_name}DTO, Update{type_name}DTO }} from '@/types/api'
import {{ useApi }} from '@/hooks/useApi'

export function {hook_name}List(page = 1, pageSize = 20) {{
  const query = `SELECT * FROM {table_name} LIMIT ${{pageSize}} OFFSET ${{(page - 1) * pageSize}}`
  return useApi<{type_name}>(query, [page, pageSize])
}}

export function {hook_name}(id: string | number | null) {{
  const query = id ? `SELECT * FROM {table_name} WHERE id = '${{id}}' LIMIT 1` : null
  const {{ data, ...rest }} = useApi<{type_name}>(query, [id])
  return {{ data: data?.[0] || null, ...rest }}
}}

export function {hook_name}Mutations() {{
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const create = useCallback(async (data: Create{type_name}DTO) => {{
    setLoading(true)
    setError(null)
    try {{
      const result = await {service_name}Service.create(data)
      return result
    }} catch (err) {{
      setError(err as Error)
      throw err
    }} finally {{
      setLoading(false)
    }}
  }}, [])

  const update = useCallback(async (id: string | number, data: Update{type_name}DTO) => {{
    setLoading(true)
    setError(null)
    try {{
      const result = await {service_name}Service.update(id, data)
      return result
    }} catch (err) {{
      setError(err as Error)
      throw err
    }} finally {{
      setLoading(false)
    }}
  }}, [])

  const remove = useCallback(async (id: string | number) => {{
    setLoading(true)
    setError(null)
    try {{
      await {service_name}Service.delete(id)
    }} catch (err) {{
      setError(err as Error)
      throw err
    }} finally {{
      setLoading(false)
    }}
  }}, [])

  return {{ create, update, remove, loading, error }}
}}"""