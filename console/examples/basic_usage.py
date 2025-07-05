"""Basic usage example for the console.

This example demonstrates how to use the console programmatically
instead of interactively.
"""

import asyncio
from pathlib import Path

from console.config import Config
from console.console_interface import ConsoleInterface, Container
from console.logging import setup_logging
from console.models import CommandType
from rich.console import Console


async def example_session():
    """Run an example console session."""
    # Create configuration
    config = Config(
        git_layer={"repo_path": "./example_data"},
        console={
            "log_file": "example.log",
            "trace_file": "example_trace.log",
            "debug_mode": True
        }
    )
    
    # Setup console and logging
    console = Console()
    trace_logger = setup_logging(
        log_file=Path(config.console.log_file),
        trace_file=Path(config.console.trace_file),
        debug_mode=config.console.debug_mode,
        console=console
    )
    
    # Create dependency container
    container = Container()
    container.config.override(lambda: config)
    container.console.override(lambda: console)
    container.trace_logger.override(lambda: trace_logger)
    
    # Create console interface
    interface = ConsoleInterface(
        config=config,
        console=console,
        trace_logger=trace_logger,
        command_parser=container.command_parser(),
        output_formatter=container.output_formatter(),
        session_state=container.session_state()
    )
    
    # Example: Execute some commands programmatically
    print("Starting example session...")
    
    # Begin transaction
    await interface._begin_transaction()
    print("Transaction started")
    
    # Create a table
    await interface._execute_db_query(
        CommandType.SCHEMA_MODIFY,
        "Create a products table with id, name, price, and category"
    )
    print("Table created")
    
    # Insert some data
    await interface._execute_db_query(
        CommandType.DATA_MODIFY,
        "Add product 'Laptop' with price 999.99 in category 'Electronics'"
    )
    print("Data inserted")
    
    # Query the data
    await interface._execute_db_query(
        CommandType.QUERY,
        "Show all products"
    )
    print("Query executed")
    
    # Commit the transaction
    await interface._commit_transaction()
    print("Transaction committed")
    
    print("\nExample session completed!")


if __name__ == "__main__":
    # Note: This is just an example. The console is designed to be
    # used interactively via the main entry point.
    asyncio.run(example_session())