"""Main entry point for the console application."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from dependency_injector import providers
from rich.console import Console

from .config import load_config
from .console_interface import ConsoleInterface, Container
from .logging import setup_logging


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable debug mode",
)
@click.option(
    "--repo-path",
    "-r",
    type=click.Path(path_type=Path),
    help="Git repository path for data storage",
)
def main(
    config: Optional[Path] = None,
    debug: bool = False,
    repo_path: Optional[Path] = None,
) -> None:
    """AI-DB Console - Interactive natural language database interface."""
    try:
        # Load configuration
        app_config = load_config(config)
        
        # Override with command line options
        if debug:
            app_config.console.debug_mode = True
        if repo_path:
            app_config.git_layer.repo_path = str(repo_path)
            
        # Setup console
        console = Console()
        
        # Setup logging
        trace_logger = setup_logging(
            log_file=Path(app_config.console.log_file),
            trace_file=Path(app_config.console.trace_file),
            debug_mode=app_config.console.debug_mode,
            console=console
        )
        
        # Setup dependency injection
        container = Container()
        container.config.override(providers.Singleton(lambda: app_config))
        container.console.override(providers.Singleton(lambda: console))
        container.trace_logger.override(providers.Singleton(lambda: trace_logger))
        
        # Create console interface
        console_interface = ConsoleInterface(
            config=app_config,
            console=console,
            trace_logger=trace_logger,
            command_parser=container.command_parser(),
            output_formatter=container.output_formatter(),
            session_state=container.session_state()
        )
        
        # Run the console
        asyncio.run(console_interface.run())
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        if debug:
            raise
        else:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)


if __name__ == "__main__":
    main()