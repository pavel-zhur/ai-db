"""Utility functions for ai-frontend."""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import yaml

logger = logging.getLogger(__name__)


async def read_file(path: Path) -> str:
    """Read file content asynchronously."""
    async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
        return await f.read()


async def write_file(path: Path, content: str) -> None:
    """Write content to file asynchronously."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
        await f.write(content)


async def read_json(path: Path) -> Dict[str, Any]:
    """Read JSON file asynchronously."""
    content = await read_file(path)
    return json.loads(content)


async def write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON file asynchronously."""
    content = json.dumps(data, indent=2)
    await write_file(path, content)


async def read_yaml(path: Path) -> Dict[str, Any]:
    """Read YAML file asynchronously."""
    content = await read_file(path)
    return yaml.safe_load(content)


async def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Write YAML file asynchronously."""
    content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    await write_file(path, content)


def sanitize_component_name(name: str) -> str:
    """Convert a string to a valid React component name."""
    # Remove special characters and convert to PascalCase
    words = re.findall(r"\w+", name)
    return "".join(word.capitalize() for word in words)


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase."""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


async def run_command(
    cmd: list[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> tuple[int, str, str]:
    """Run a command asynchronously and return exit code, stdout, and stderr."""
    logger.debug(f"Running command: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=env,
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise TimeoutError(f"Command timed out after {timeout} seconds")
    
    return (
        process.returncode or 0,
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )


def extract_code_blocks(text: str, language: Optional[str] = None) -> list[str]:
    """Extract code blocks from markdown text."""
    pattern = r"```(?:" + (language or r"\w*") + r")?\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def format_error_message(error: Exception, context: str) -> str:
    """Format an error message with context."""
    return f"{context}: {type(error).__name__}: {str(error)}"