"""Main console interface implementation."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from dependency_injector import containers, providers
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from ai_db import AIDB, PermissionLevel
from ai_frontend import AiFrontend
from git_layer import GitTransaction

from .command_parser import CommandParser
from .config import Config
from .logging import TraceLogger, setup_logging
from .models import CommandType, OutputFormat, SessionState
from .output_formatter import OutputFormatter


logger = logging.getLogger(__name__)


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    
    config = providers.Singleton(Config)
    
    console = providers.Singleton(Console)
    
    trace_logger = providers.Singleton(
        TraceLogger,
        trace_file=config.provided.console.trace_file
    )
    
    command_parser = providers.Singleton(CommandParser)
    
    output_formatter = providers.Singleton(
        OutputFormatter,
        console=console,
        max_width=config.provided.console.table_max_width
    )
    
    session_state = providers.Singleton(
        SessionState,
        conversation_history=[],
        current_output_format=OutputFormat.TABLE
    )


class ConsoleInterface:
    """Main interactive console interface."""
    
    def __init__(
        self,
        config: Config,
        console: Console,
        trace_logger: TraceLogger,
        command_parser: CommandParser,
        output_formatter: OutputFormatter,
        session_state: SessionState
    ):
        self._config = config
        self._console = console
        self._trace_logger = trace_logger
        self._command_parser = command_parser
        self._output_formatter = output_formatter
        self._session_state = session_state
        self._git_transaction: Optional[GitTransaction] = None
        self._ai_db: Optional[AIDB] = None
        self._ai_frontend: Optional[AiFrontend] = None
        
    async def run(self) -> None:
        """Run the interactive console."""
        self._show_welcome()
        
        try:
            while True:
                try:
                    # Show transaction status in prompt
                    if self._session_state.transaction_active:
                        prompt = "[yellow]🔄 TX[/yellow] > "
                    else:
                        prompt = "> "
                        
                    # Get user input
                    user_input = Prompt.ask(prompt, console=self._console)
                    if not user_input.strip():
                        continue
                        
                    # Log input
                    self._trace_logger.log_input(user_input)
                    
                    # Parse command
                    cmd_type, params = self._command_parser.parse(user_input)
                    
                    # Handle command
                    await self._handle_command(cmd_type, params, user_input)
                    
                except KeyboardInterrupt:
                    self._console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    self._output_formatter.format_error(error_msg)
                    self._trace_logger.log_error(error_msg)
                    logger.exception("Unexpected error in console loop")
                    
        except KeyboardInterrupt:
            pass
        finally:
            await self._cleanup()
            
    async def _handle_command(
        self,
        cmd_type: CommandType,
        params: Optional[str],
        user_input: str
    ) -> None:
        """Handle parsed command."""
        try:
            if cmd_type == CommandType.EXIT:
                if self._session_state.transaction_active:
                    if Confirm.ask(
                        "[yellow]Transaction is active. Rollback and exit?[/yellow]",
                        console=self._console
                    ):
                        await self._rollback_transaction()
                    else:
                        return
                raise KeyboardInterrupt
                
            elif cmd_type == CommandType.HELP:
                self._show_help()
                
            elif cmd_type == CommandType.OUTPUT_FORMAT:
                self._set_output_format(params)
                
            elif cmd_type == CommandType.TRANSACTION_BEGIN:
                await self._begin_transaction()
                
            elif cmd_type == CommandType.TRANSACTION_COMMIT:
                await self._commit_transaction()
                
            elif cmd_type == CommandType.TRANSACTION_ROLLBACK:
                await self._rollback_transaction()
                
            elif cmd_type == CommandType.FRONTEND_GENERATE:
                await self._generate_frontend(user_input)
                
            elif cmd_type in [
                CommandType.QUERY,
                CommandType.SCHEMA_MODIFY,
                CommandType.DATA_MODIFY,
                CommandType.VIEW_MODIFY
            ]:
                # Check for destructive operations
                if cmd_type != CommandType.QUERY:
                    if self._command_parser.detect_destructive_operation(user_input):
                        if not Confirm.ask(
                            "[red]This appears to be a destructive operation. Continue?[/red]",
                            console=self._console
                        ):
                            self._output_formatter.format_info("Operation cancelled")
                            return
                            
                await self._execute_db_query(cmd_type, user_input)
                
            elif cmd_type == CommandType.EXPORT:
                await self._export_data(params)
                
            else:
                self._output_formatter.format_error(f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            error_msg = str(e)
            self._output_formatter.format_error(error_msg)
            self._trace_logger.log_error(error_msg)
            self._session_state.add_entry(
                user_input=user_input,
                error=error_msg,
                command_type=cmd_type
            )
            
    async def _begin_transaction(self) -> None:
        """Begin a new transaction."""
        if self._session_state.transaction_active:
            self._output_formatter.format_warning("Transaction already active")
            return
            
        try:
            self._git_transaction = GitTransaction(
                repo_path=self._config.git_layer.repo_path,
                message="Console transaction"
            )
            await self._git_transaction.__aenter__()
            self._session_state.transaction_active = True
            self._session_state.transaction_id = "current"
            
            # Initialize AI-DB with transaction
            self._ai_db = AIDB()
            
            # Initialize AI-Frontend
            from ai_frontend.config import AiFrontendConfig
            ai_frontend_config = AiFrontendConfig(
                claude_code_path=self._config.ai_frontend.claude_code_path,
                max_iterations=self._config.ai_frontend.max_iterations,
                timeout_seconds=self._config.ai_frontend.timeout_seconds
            )
            self._ai_frontend = AiFrontend(ai_frontend_config)
            
            self._output_formatter.format_success("Transaction started")
            self._trace_logger.log_output("Transaction started")
            
        except Exception as e:
            self._session_state.transaction_active = False
            self._session_state.transaction_id = None
            raise
            
    async def _commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self._session_state.transaction_active:
            self._output_formatter.format_warning("No active transaction")
            return
            
        try:
            await self._git_transaction.__aexit__(None, None, None)
            self._session_state.transaction_active = False
            self._session_state.transaction_id = None
            self._git_transaction = None
            self._ai_db = None
            self._ai_frontend = None
            
            self._output_formatter.format_success("Transaction committed")
            self._trace_logger.log_output("Transaction committed")
            
        except Exception as e:
            self._output_formatter.format_error(f"Failed to commit: {str(e)}")
            raise
            
    async def _rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self._session_state.transaction_active:
            self._output_formatter.format_warning("No active transaction")
            return
            
        try:
            # Force rollback by raising exception in context manager
            await self._git_transaction.__aexit__(
                Exception,
                Exception("Manual rollback"),
                None
            )
            self._session_state.transaction_active = False
            self._session_state.transaction_id = None
            self._git_transaction = None
            self._ai_db = None
            self._ai_frontend = None
            
            self._output_formatter.format_success("Transaction rolled back")
            self._trace_logger.log_output("Transaction rolled back")
            
        except Exception as e:
            self._output_formatter.format_error(f"Failed to rollback: {str(e)}")
            raise
            
    async def _execute_db_query(
        self,
        cmd_type: CommandType,
        query: str
    ) -> None:
        """Execute database query."""
        if not self._session_state.transaction_active:
            await self._begin_transaction()
            
        # Map command type to permission level
        permission_map = {
            CommandType.QUERY: PermissionLevel.SELECT,
            CommandType.SCHEMA_MODIFY: PermissionLevel.SCHEMA_MODIFY,
            CommandType.DATA_MODIFY: PermissionLevel.DATA_MODIFY,
            CommandType.VIEW_MODIFY: PermissionLevel.VIEW_MODIFY,
        }
        permissions = permission_map[cmd_type]
        
        # Show progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console
        ) as progress:
            task = progress.add_task("Executing query...", total=None)
            
            try:
                result = await self._ai_db.execute(
                    query=query,
                    permissions=permissions,
                    transaction=self._git_transaction
                )
                
                progress.update(task, completed=True)
                
                # Format and display result
                formatted = self._output_formatter.format_result(
                    data=result.data,
                    format_type=self._session_state.current_output_format,
                    title=None,
                    ai_comment=result.ai_comment
                )
                
                # Log success
                self._trace_logger.log_output(f"Query executed: {formatted[:200]}...")
                self._session_state.add_entry(
                    user_input=query,
                    response=formatted,
                    command_type=cmd_type
                )
                
                # Save compiled plan if available
                if result.compiled_plan:
                    self._output_formatter.format_info(
                        "Query compiled. Use compiled plan for better performance."
                    )
                    
            except Exception as e:
                progress.update(task, completed=True)
                raise
                
    async def _generate_frontend(self, request: str) -> None:
        """Generate frontend using AI-Frontend."""
        if not self._session_state.transaction_active:
            await self._begin_transaction()
            
        # Get current schema
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console
        ) as progress:
            task = progress.add_task("Generating frontend...", total=None)
            
            try:
                # Get schema from AI-DB
                schema_result = await self._ai_db.execute(
                    query="Show me the complete database schema",
                    permissions=PermissionLevel.SELECT,
                    transaction=self._git_transaction
                )
                
                # Generate frontend
                result = await self._ai_frontend.generate_frontend(
                    request=request,
                    schema=schema_result.data,
                    transaction_context=self._git_transaction
                )
                
                progress.update(task, completed=True)
                
                if result.success:
                    self._output_formatter.format_success(
                        f"Frontend generated at: {result.output_path}"
                    )
                    self._trace_logger.log_output(f"Frontend generated: {result.output_path}")
                else:
                    raise Exception(result.error)
                    
            except Exception as e:
                progress.update(task, completed=True)
                raise
                
    async def _export_data(self, params: Optional[str]) -> None:
        """Export data to file."""
        if not params or "|" not in params:
            self._output_formatter.format_error("Invalid export syntax")
            return
            
        query, filename = params.split("|", 1)
        query = query.strip()
        filename = filename.strip()
        
        # Execute query
        await self._execute_db_query(CommandType.QUERY, query)
        
        # Get last result
        if self._session_state.conversation_history:
            last_entry = self._session_state.conversation_history[-1]
            if last_entry.response:
                try:
                    with open(filename, "w") as f:
                        f.write(last_entry.response)
                    self._output_formatter.format_success(f"Exported to {filename}")
                except Exception as e:
                    self._output_formatter.format_error(f"Export failed: {str(e)}")
                    
    def _set_output_format(self, format_str: Optional[str]) -> None:
        """Set output format."""
        if not format_str:
            return
            
        try:
            output_format = OutputFormat(format_str)
            self._session_state.current_output_format = output_format
            self._output_formatter.format_success(f"Output format set to: {format_str}")
            self._trace_logger.log_output(f"Output format changed to: {format_str}")
        except ValueError:
            self._output_formatter.format_error(f"Invalid format: {format_str}")
            
    def _show_welcome(self) -> None:
        """Show welcome message."""
        welcome = Panel(
            Markdown("""# AI-DB Console

Natural language database interface with AI-powered operations.

**Commands:**
- Type natural language queries or SQL
- `begin` - Start a transaction
- `commit` - Commit transaction
- `rollback` - Rollback transaction
- `output format [table|json|yaml]` - Change output format
- `export <query> to <filename>` - Export query results
- `help` - Show this help
- `exit` - Exit console

**Examples:**
- "Show all users"
- "Create a products table with id, name, and price"
- "Generate a dashboard for customer management"
"""),
            title="Welcome",
            border_style="blue"
        )
        self._console.print(welcome)
        
    def _show_help(self) -> None:
        """Show help message."""
        help_text = Markdown("""## Console Help

### Basic Commands
- **Natural language queries**: Just type what you want
- **SQL queries**: Standard SQL syntax supported
- **UI generation**: "Generate a dashboard for..."

### Transaction Commands
- `begin` - Start a new transaction
- `commit` - Commit current transaction  
- `rollback` - Rollback current transaction

### Output Commands
- `output format table` - Table format (default)
- `output format json` - JSON format
- `output format yaml` - YAML format
- `export <query> to <file>` - Export results to file

### Other Commands
- `help` or `?` - Show this help
- `exit`, `quit`, or `bye` - Exit console

### Tips
- Transactions are automatic if not explicitly managed
- Destructive operations require confirmation
- Use natural language for complex queries
- The AI understands context from conversation history
""")
        self._console.print(Panel(help_text, title="Help", border_style="green"))
        
    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._session_state.transaction_active and self._git_transaction:
            try:
                await self._rollback_transaction()
            except Exception:
                pass
                
        self._console.print("\n[blue]Goodbye![/blue]")