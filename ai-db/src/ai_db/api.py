"""Public API for AI-DB."""

import logging
from typing import Any

from ai_shared.protocols import TransactionProtocol

from ai_db.config import get_config
from ai_db.core.engine import DIContainer, Engine
from ai_db.core.models import (
    PermissionLevel,
    QueryContext,
    QueryResult,
)
from ai_db.exceptions import AIDBError

logger = logging.getLogger(__name__)


class AIDB:
    """Main AI-DB interface."""

    def __init__(self) -> None:
        """Initialize AI-DB."""
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, get_config().log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Initialize DI container
        self._container = DIContainer()
        self._container.config.from_dict(get_config().__dict__)

        # Create engine
        self._engine = Engine(self._container)

        logger.info("AI-DB initialized")

    async def execute(
        self,
        query: str,
        permissions: PermissionLevel,
        transaction: TransactionProtocol,
        context: QueryContext | None = None,
    ) -> QueryResult:
        """
        Execute a database query.

        Args:
            query: Natural language query or SQL
            permissions: Permission level for the operation
            transaction: Transaction context from git-layer
            context: Optional query context with schema and error history

        Returns:
            QueryResult with status, data, and metadata
        """
        if not query:
            return QueryResult(
                status=False,
                error="Query cannot be empty",
                transaction_id=transaction.id,
            )

        try:
            logger.info(f"Executing query with {permissions.value} permissions: {query[:100]}...")

            result = await self._engine.execute(
                query=query,
                permissions=permissions,
                transaction_context=transaction,
                context=context,
            )

            if result.status:
                logger.info("Query executed successfully")
                await transaction.operation_complete(f"Query executed: {query[:50]}...")
            else:
                logger.warning(f"Query failed: {result.error}")
                await transaction.operation_failed(f"Query failed: {result.error}")

            return result

        except AIDBError as e:
            await transaction.operation_failed(f"AIDBError: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await transaction.operation_failed(f"Unexpected error: {e!s}")
            return QueryResult(
                status=False,
                error=f"Unexpected error: {e!s}",
                transaction_id=transaction.id,
            )

    def execute_compiled(
        self,
        compiled_plan: str,
        transaction: TransactionProtocol,
    ) -> QueryResult:
        """
        Execute a pre-compiled query plan.

        Args:
            compiled_plan: Serialized query plan from previous compilation
            transaction: Transaction context from git-layer

        Returns:
            QueryResult with query results
        """
        import asyncio

        try:
            logger.info("Executing compiled query plan")

            # Run async method in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If called from async context
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self._engine.execute_compiled(compiled_plan, transaction)
                    )
                    return future.result()
            else:
                # If called from sync context
                return asyncio.run(self._engine.execute_compiled(compiled_plan, transaction))

        except AIDBError:
            raise
        except Exception as e:
            logger.error(f"Failed to execute compiled query: {e}")
            return QueryResult(
                status=False,
                error=f"Failed to execute compiled query: {e!s}",
                transaction_id=transaction.id,
            )

    async def begin_transaction(self, transaction: TransactionProtocol) -> None:
        """
        Begin a new transaction.

        This is handled by git-layer, but AI-DB can perform any necessary setup.

        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Beginning transaction {transaction.id}")
        # Any AI-DB specific transaction initialization can go here

    async def commit_transaction(self, transaction: TransactionProtocol) -> None:
        """
        Commit a transaction.

        This is handled by git-layer, but AI-DB can perform any necessary cleanup.

        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Committing transaction {transaction.id}")
        # Any AI-DB specific transaction cleanup can go here

    async def rollback_transaction(self, transaction: TransactionProtocol) -> None:
        """
        Rollback a transaction.

        This is handled by git-layer, but AI-DB can perform any necessary cleanup.

        Args:
            transaction: Transaction context from git-layer
        """
        logger.info(f"Rolling back transaction {transaction.id}")
        # Any AI-DB specific transaction cleanup can go here

    async def get_schema(
        self, transaction: TransactionProtocol, include_semantic_docs: bool = False
    ) -> dict[str, Any]:
        """
        Get the current database schema.

        Args:
            transaction: Transaction context from git-layer
            include_semantic_docs: Whether to include semantic documentation

        Returns:
            Schema in JSON format
        """
        # Override container's transaction context
        self._container.transaction_context.override(transaction)

        # Create schema store with transaction context
        schema_store = self._container.schema_store()
        schema = await schema_store.load_schema()

        # Convert to JSON format expected by ai-frontend
        result: dict[str, Any] = {"tables": {}, "views": schema.views, "version": schema.version}

        for table_name, table in schema.tables.items():
            result["tables"][table_name] = {
                "columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "nullable": col.nullable,
                        "default": col.default,
                        "description": col.description,
                    }
                    for col in table.columns
                ],
                "constraints": [
                    {
                        "name": const.name,
                        "type": const.type.value,
                        "columns": const.columns,
                        "definition": const.definition,
                        "referenced_table": const.referenced_table,
                        "referenced_columns": const.referenced_columns,
                    }
                    for const in table.constraints
                ],
                "description": table.description,
            }

        if include_semantic_docs:
            result["semantic_documentation"] = schema.semantic_documentation

        return result

    async def init_from_folder(self, transaction: TransactionProtocol, source_folder: str) -> None:
        """
        Initialize database from an existing folder structure.

        Copies and validates YAML schemas from source folder.
        Used for setting up AI-DB with seed data.

        Args:
            transaction: Transaction context from git-layer
            source_folder: Path to source folder with schemas and data
        """
        import shutil
        from pathlib import Path

        import yaml

        source_path = Path(source_folder)
        target_path = Path(transaction.path)

        try:
            # Ensure write escalation for initialization
            await transaction.write_escalation_required()

            # Copy schema files if they exist
            schemas_source = source_path / "schemas"
            if schemas_source.exists():
                schemas_target = target_path / "schemas"
                schemas_target.mkdir(parents=True, exist_ok=True)

                for schema_file in schemas_source.glob("*.schema.yaml"):
                    # Validate schema format
                    with open(schema_file) as f:
                        schema_data = yaml.safe_load(f)

                    # Basic validation
                    if not isinstance(schema_data, dict) or "name" not in schema_data:
                        raise ValueError(f"Invalid schema format in {schema_file.name}")

                    # Copy to target
                    target_file = schemas_target / schema_file.name
                    shutil.copy2(schema_file, target_file)
                    logger.info(f"Copied schema: {schema_file.name}")

            # Copy table data if it exists
            tables_source = source_path / "tables"
            if tables_source.exists():
                tables_target = target_path / "tables"
                tables_target.mkdir(parents=True, exist_ok=True)

                for table_file in tables_source.glob("*.yaml"):
                    # Validate YAML format
                    with open(table_file) as f:
                        table_data = yaml.safe_load(f)

                    if table_data is not None and not isinstance(table_data, list):
                        raise ValueError(
                            f"Invalid table format in {table_file.name} - must be a list"
                        )

                    # Copy to target
                    target_file = tables_target / table_file.name
                    shutil.copy2(table_file, target_file)
                    logger.info(f"Copied table data: {table_file.name}")

            # Copy views if they exist
            views_source = source_path / "views"
            if views_source.exists():
                views_target = target_path / "views"
                views_target.mkdir(parents=True, exist_ok=True)

                for view_file in views_source.rglob("*"):
                    if view_file.is_file():
                        relative_path = view_file.relative_to(views_source)
                        target_file = views_target / relative_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(view_file, target_file)
                        logger.info(f"Copied view: {relative_path}")

            # Copy documentation if it exists
            docs_source = source_path / "documentation"
            if docs_source.exists():
                docs_target = target_path / "documentation"
                docs_target.mkdir(parents=True, exist_ok=True)

                for doc_file in docs_source.glob("*.yaml"):
                    target_file = docs_target / doc_file.name
                    shutil.copy2(doc_file, target_file)
                    logger.info(f"Copied documentation: {doc_file.name}")

            # Create .gitignore if it doesn't exist
            gitignore_path = target_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_content = """# AI-DB generated files
__pycache__/
*.py[cod]
*$py.class
*.so
.pytest_cache/
.coverage
htmlcov/
.DS_Store
.vscode/
.idea/
"""
                with open(gitignore_path, "w") as f:
                    f.write(gitignore_content)
                logger.info("Created .gitignore")

            await transaction.operation_complete(
                f"Successfully initialized database from {source_folder}"
            )
            logger.info(f"Database initialized from {source_folder}")

        except Exception as e:
            await transaction.operation_failed(f"Failed to initialize from folder: {e!s}")
            logger.error(f"Failed to initialize from folder {source_folder}: {e}")
            raise
