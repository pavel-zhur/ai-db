"""Configuration management for AI-DB."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIDBConfig:
    """Configuration for AI-DB."""
    
    # AI Model Configuration
    api_base: str = os.getenv("AI_DB_API_BASE", "https://api.openai.com/v1")
    api_key: str = os.getenv("AI_DB_API_KEY", "")
    model: str = os.getenv("AI_DB_MODEL", "gpt-4")
    temperature: float = float(os.getenv("AI_DB_TEMPERATURE", "0.0"))
    
    # Execution Configuration
    max_retries: int = int(os.getenv("AI_DB_MAX_RETRIES", "3"))
    timeout_seconds: float = float(os.getenv("AI_DB_TIMEOUT", "30.0"))
    
    # Storage Configuration
    data_directory: str = os.getenv("AI_DB_DATA_DIR", "data")
    
    # Validation Configuration
    strict_validation: bool = os.getenv("AI_DB_STRICT_VALIDATION", "true").lower() == "true"
    sandbox_execution: bool = os.getenv("AI_DB_SANDBOX_EXECUTION", "true").lower() == "true"
    
    # Logging Configuration
    log_level: str = os.getenv("AI_DB_LOG_LEVEL", "INFO")
    log_ai_interactions: bool = os.getenv("AI_DB_LOG_AI", "false").lower() == "true"
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise ValueError("AI_DB_API_KEY environment variable must be set")
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


_config: Optional[AIDBConfig] = None


def get_config() -> AIDBConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AIDBConfig()
        _config.validate()
    return _config


def set_config(config: AIDBConfig) -> None:
    """Set the global configuration instance."""
    global _config
    config.validate()
    _config = config