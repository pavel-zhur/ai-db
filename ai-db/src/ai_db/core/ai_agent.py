"""AI agent for query interpretation and execution using LangChain."""

import json
import logging
from dataclasses import asdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

from ai_db.config import get_config
from ai_db.core.models import (
    AIOperation,
    PermissionLevel,
    QueryContext,
    Schema,
)
from ai_db.exceptions import AIError
from ai_db.exceptions import PermissionError as DBPermissionError

logger = logging.getLogger(__name__)


class OperationPlan(BaseModel):
    """Plan for executing a database operation."""

    operation_type: str = Field(
        description="Type of operation: select, insert, update, delete, create_table, "
        "alter_table, drop_table, create_view, drop_view"
    )
    permission_level: str = Field(
        description="Required permission level: select, data_modify, schema_modify, view_modify"
    )
    affected_tables: list[str] = Field(description="List of tables affected by this operation")
    requires_python_generation: bool = Field(
        description="Whether this operation requires Python code generation"
    )
    data_loss_indicator: str = Field(description="Potential data loss: none, probable, yes")
    confidence: float = Field(description="Confidence in the interpretation (0-1)")
    interpretation: str = Field(description="Natural language interpretation of the query")


class FileUpdate(BaseModel):
    """File update operation."""

    path: str = Field(description="Relative file path")
    content: str = Field(description="Complete new file content")
    operation: str = Field(description="Operation type: create, update, delete")


class ExecutionPlan(BaseModel):
    """Complete execution plan for the operation."""

    file_updates: list[FileUpdate] = Field(description="List of file updates to perform")
    python_code: str | None = Field(description="Python code for SELECT queries or views")
    validation_queries: list[str] = Field(description="Queries to validate after execution")
    error: str | None = Field(description="Error message if operation cannot be executed")


class AIAgent:
    """AI agent for database operations."""

    def __init__(self) -> None:
        config = get_config()
        self._llm = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            api_key=SecretStr(config.api_key),
            base_url=config.api_base,
            timeout=config.timeout_seconds,
        )
        self._max_retries = config.max_retries

        # Initialize output parsers
        self._operation_parser = JsonOutputParser(pydantic_object=OperationPlan)
        self._execution_parser = JsonOutputParser(pydantic_object=ExecutionPlan)

    async def analyze_query(
        self,
        query: str,
        permissions: PermissionLevel,
        context: QueryContext,
    ) -> AIOperation:
        """Analyze a query and determine the operation type and requirements."""

        # Build system prompt with schema context
        system_prompt = self._build_analysis_prompt(context.schema)

        # Add error context if retrying
        error_context = ""
        if context.recent_errors:
            error_context = "\n\nPrevious errors:\n" + "\n".join(context.recent_errors[-3:])

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Query: {query}\nGranted permissions: {permissions.value}{error_context}"
            ),
        ]

        # Log the messages being sent to AI
        logger.info(f"Sending query analysis request to AI")
        logger.info(f"System prompt: {system_prompt}")
        logger.info(f"Human message: Query: {query}\nGranted permissions: {permissions.value}{error_context}")

        try:
            # Get operation plan from AI
            response = await self._llm.ainvoke(messages)
            # Ensure we have a string content
            content = (
                response.content if isinstance(response.content, str) else str(response.content)
            )
            logger.info(f"AI response for query analysis: {content}")
            plan_dict = self._operation_parser.parse(content)
            plan = OperationPlan(**plan_dict)

            # Check permissions
            required_perm = PermissionLevel(plan.permission_level)
            if not self._check_permission(permissions, required_perm):
                raise DBPermissionError(required_perm.value, permissions.value)

            # Create AI operation
            operation = AIOperation(
                operation_type=plan.operation_type,
                permission_level=required_perm,
                affected_tables=plan.affected_tables,
                requires_python_generation=plan.requires_python_generation,
                validation_required=True,
            )

            # Log the interpretation
            logger.info(f"AI interpretation: {plan.interpretation} (confidence: {plan.confidence})")

            return operation

        except DBPermissionError:
            raise
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            raise AIError(f"Failed to analyze query: {e!s}", context.retry_count) from e

    async def generate_execution_plan(
        self,
        query: str,
        operation: AIOperation,
        context: QueryContext,
    ) -> ExecutionPlan:
        """Generate the execution plan for an operation."""

        # Build execution prompt
        system_prompt = self._build_execution_prompt(operation, context.schema)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}\nOperation type: {operation.operation_type}"),
        ]

        # Log the messages being sent to AI
        logger.info(f"Sending execution plan request to AI")
        logger.info(f"System prompt: {system_prompt}")
        logger.info(f"Human message: Query: {query}\nOperation type: {operation.operation_type}")

        try:
            response = await self._llm.ainvoke(messages)
            # Ensure we have a string content
            content = (
                response.content if isinstance(response.content, str) else str(response.content)
            )
            logger.info(f"AI response for execution plan: {content}")
            plan_dict = self._execution_parser.parse(content)
            plan = ExecutionPlan(**plan_dict)

            # Store Python code if generated
            if plan.python_code:
                operation.python_code = plan.python_code

            # Convert file updates
            operation.file_updates = {update.path: update.content for update in plan.file_updates}

            return plan  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to generate execution plan: {e}")
            raise AIError(f"Failed to generate execution plan: {e!s}", context.retry_count) from e

    async def handle_validation_error(
        self,
        error_message: str,
        operation: AIOperation,
        context: QueryContext,
    ) -> ExecutionPlan | None:
        """Handle validation errors and attempt to fix them."""

        if context.retry_count >= self._max_retries:
            return None

        system_prompt = (
            "You are an AI database engine. A validation error occurred during execution.\n"
            "Analyze the error and generate a fixed execution plan if possible.\n\n"
            "Current schema and documentation:\n"
            "{schema_context}\n\n"
            "Previous operation:\n"
            "{operation_details}\n\n"
            "Respond with a new ExecutionPlan that fixes the validation error, "
            "or set error field if unfixable."
        )

        messages = [
            SystemMessage(
                content=system_prompt.format(
                    schema_context=self._format_schema_context(context.schema),
                    operation_details=json.dumps(asdict(operation), indent=2),
                )
            ),
            HumanMessage(content=f"Validation error: {error_message}"),
        ]

        # Log the messages being sent to AI
        logger.info(f"Sending validation error recovery request to AI")
        logger.info(f"System prompt: {system_prompt.format(schema_context='[schema details]', operation_details='[operation details]')}")
        logger.info(f"Human message: Validation error: {error_message}")

        try:
            response = await self._llm.ainvoke(messages)
            # Ensure we have a string content
            content = (
                response.content if isinstance(response.content, str) else str(response.content)
            )
            logger.info(f"AI response for validation error recovery: {content}")
            plan_dict = self._execution_parser.parse(content)
            plan = ExecutionPlan(**plan_dict)

            if plan.error:
                return None

            # Update operation with new plan
            if plan.python_code:
                operation.python_code = plan.python_code

            operation.file_updates = {update.path: update.content for update in plan.file_updates}

            return plan  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to handle validation error: {e}")
            return None

    def _build_analysis_prompt(self, schema: Schema | None) -> str:
        """Build the system prompt for query analysis."""
        schema_context = self._format_schema_context(schema) if schema else "No schema loaded yet."

        return (
            f"You are an AI database engine. Analyze the given query and determine:\n"
            f"1. The type of operation (select, insert, update, delete, create_table, "
            f"alter_table, drop_table, create_view, drop_view)\n"
            f"2. Required permission level\n"
            f"3. Affected tables\n"
            f"4. Whether Python code generation is needed (for SELECT queries and views)\n"
            f"5. Potential data loss\n\n"
            f"Current database schema and documentation:\n"
            f"{schema_context}\n\n"
            f"Respond in JSON format matching the OperationPlan schema."
        )

    def _build_execution_prompt(self, operation: AIOperation, schema: Schema | None) -> str:
        """Build the system prompt for execution planning."""
        schema_context = self._format_schema_context(schema) if schema else "No schema loaded yet."

        if operation.operation_type == "select" or operation.operation_type == "create_view":
            return f"""You are an AI database engine. Generate pure Python code for the query.

Current schema:
{schema_context}

Requirements:
- Generate a pure Python function that processes the data
- Function should accept table data as dictionaries and return results
- Use only standard library (no pandas, numpy, etc.)
- Handle joins, aggregations, and filtering as needed
- For views, create a reusable function

Respond in JSON format with ExecutionPlan including python_code field."""

        else:
            return f"""You are an AI database engine. Generate file updates for the operation.

Current schema and data format:
{schema_context}

Data is stored in YAML files:
- Tables: tables/<table_name>.yaml (list of dictionaries)
- Schemas: schemas/<table_name>.schema.yaml
- Views: views/<view_name>.py and views/<view_name>.meta.yaml

Generate complete file contents for all affected files.
Ensure data integrity and constraint compliance.

Respond in JSON format with ExecutionPlan including file_updates list."""

    def _format_schema_context(self, schema: Schema | None) -> str:
        """Format schema information for AI context."""
        if not schema:
            return "No schema defined yet."

        lines = ["Tables:"]
        for table_name, table in schema.tables.items():
            lines.append(f"\n{table_name}:")
            if table.description:
                lines.append(f"  Description: {table.description}")

            lines.append("  Columns:")
            for col in table.columns:
                col_def = f"    - {col.name}: {col.type}"
                if not col.nullable:
                    col_def += " NOT NULL"
                if col.default is not None:
                    col_def += f" DEFAULT {col.default}"
                if col.description:
                    col_def += f" -- {col.description}"
                lines.append(col_def)

            if table.constraints:
                lines.append("  Constraints:")
                for const in table.constraints:
                    const_def = (
                        f"    - {const.name}: {const.type.value} on "
                        f"({', '.join(const.columns)})"
                    )
                    if const.definition:
                        const_def += f" CHECK {const.definition}"
                    if const.referenced_table:
                        const_def += (
                            f" REFERENCES {const.referenced_table}"
                            f"({', '.join(const.referenced_columns or [])})"
                        )
                    lines.append(const_def)

        if schema.views:
            lines.append("\nViews:")
            for view_name in schema.views:
                lines.append(f"  - {view_name}")

        if schema.semantic_documentation:
            lines.append("\nSemantic Documentation:")
            for key, doc in schema.semantic_documentation.items():
                lines.append(f"  {key}: {doc}")

        return "\n".join(lines)

    def _check_permission(self, granted: PermissionLevel, required: PermissionLevel) -> bool:
        """Check if granted permission level is sufficient."""
        permission_hierarchy = {
            PermissionLevel.SELECT: 0,
            PermissionLevel.DATA_MODIFY: 1,
            PermissionLevel.VIEW_MODIFY: 2,
            PermissionLevel.SCHEMA_MODIFY: 3,
        }

        return permission_hierarchy.get(granted, -1) >= permission_hierarchy.get(required, 999)
