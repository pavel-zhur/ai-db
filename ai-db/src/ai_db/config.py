"""Configuration management for AI-DB."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AIDBConfig(BaseSettings):
    """Configuration for AI-DB using Pydantic BaseSettings."""
    
    # AI Model Configuration
    api_base: str = Field(default="https://api.openai.com/v1")
    api_key: str = Field(default="")
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.0)
    
    # Execution Configuration
    max_retries: int = Field(default=3)
    timeout_seconds: float = Field(default=30.0)
    
    # Storage Configuration
    data_directory: str = Field(default="data")
    
    # Validation Configuration
    strict_validation: bool = Field(default=True)
    sandbox_execution: bool = Field(default=True)
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_ai_interactions: bool = Field(default=False)
    
    @field_validator('api_key')
    @classmethod
    def api_key_must_be_set(cls, v):
        # For POC, allow empty API key but warn
        if not v:
            import logging
            logging.warning("AI_DB_API_KEY not set - using stub AI agent")
        return v or "stub-key"
    
    @field_validator('max_retries')
    @classmethod
    def max_retries_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        return v
    
    @field_validator('timeout_seconds')
    @classmethod
    def timeout_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("timeout_seconds must be positive")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "AI_DB_"
    }


_config: Optional[AIDBConfig] = None


def get_config() -> AIDBConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AIDBConfig()
    return _config


def set_config(config: AIDBConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config