"""Configuration management for the console."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AIDBConfig(BaseModel):
    """AI-DB configuration."""

    api_base: str = Field(default="https://api.openai.com/v1")
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.0)
    max_retries: int = Field(default=3)
    timeout_seconds: float = Field(default=30.0)


class AIFrontendConfig(BaseModel):
    """AI-Frontend configuration."""

    claude_code_path: str = Field(default="claude")
    claude_code_docker_image: str = Field(default="anthropics/claude-code:latest")
    max_iterations: int = Field(default=5)
    timeout_seconds: int = Field(default=300)
    retry_attempts: int = Field(default=2)
    api_base_url: str = Field(default="http://localhost:8000")


class GitLayerConfig(BaseModel):
    """Git-Layer configuration."""

    repo_path: str = Field(default="./data")


class ConsoleConfig(BaseModel):
    """Console-specific configuration."""

    log_file: str = Field(default="console.log")
    trace_file: str = Field(default="console_trace.log")
    debug_mode: bool = Field(default=False)
    default_output_format: str = Field(default="table", pattern="^(table|json|yaml)$")
    table_max_width: int = Field(default=120)
    page_size: int = Field(default=50)


class Config(BaseModel):
    """Complete configuration."""

    ai_db: AIDBConfig = Field(default_factory=AIDBConfig)
    ai_frontend: AIFrontendConfig = Field(default_factory=AIFrontendConfig)
    git_layer: GitLayerConfig = Field(default_factory=GitLayerConfig)
    console: ConsoleConfig = Field(default_factory=ConsoleConfig)


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file and environment variables.

    Precedence (highest to lowest):
    1. Command-line arguments (passed to this function)
    2. Environment variables
    3. Config file
    4. Defaults
    """
    config_dict: dict[str, Any] = {}

    # Load from config file if exists
    if config_path and config_path.exists():
        with open(config_path) as f:
            config_dict = yaml.safe_load(f) or {}
    elif Path("console.yaml").exists():
        with open("console.yaml") as f:
            config_dict = yaml.safe_load(f) or {}

    # Override with environment variables
    env_mapping = {
        "AI_DB_API_BASE": ("ai_db", "api_base"),
        "AI_DB_API_KEY": ("ai_db", "api_key"),
        "AI_DB_MODEL": ("ai_db", "model"),
        "AI_DB_TEMPERATURE": ("ai_db", "temperature"),
        "AI_DB_MAX_RETRIES": ("ai_db", "max_retries"),
        "AI_DB_TIMEOUT_SECONDS": ("ai_db", "timeout_seconds"),
        "AI_FRONTEND_CLAUDE_CODE_PATH": ("ai_frontend", "claude_code_path"),
        "AI_FRONTEND_CLAUDE_CODE_DOCKER_IMAGE": ("ai_frontend", "claude_code_docker_image"),
        "AI_FRONTEND_API_BASE_URL": ("ai_frontend", "api_base_url"),
        "GIT_LAYER_REPO_PATH": ("git_layer", "repo_path"),
        "CONSOLE_DEBUG": ("console", "debug_mode"),
        "CONSOLE_LOG_FILE": ("console", "log_file"),
        "CONSOLE_TRACE_FILE": ("console", "trace_file"),
    }

    for env_var, (section, key) in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            if section not in config_dict:
                config_dict[section] = {}
            # Convert to appropriate type
            if key in ["max_retries", "max_iterations", "table_max_width", "page_size"]:
                config_dict[section][key] = int(value)
            elif key in ["timeout_seconds", "temperature"]:
                config_dict[section][key] = float(value)
            elif key == "debug_mode":
                config_dict[section][key] = value.lower() in ("true", "1", "yes")
            else:
                config_dict[section][key] = value

    return Config(**config_dict)
