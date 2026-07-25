"""Configuration management for the AI Translation & Quality Scoring Pipeline.

Loads settings from environment variables or .env file cleanly and robustly.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def is_api_key_configured(self) -> bool:
        """Check if an Anthropic API key is provided."""
        return bool(self.anthropic_api_key and self.anthropic_api_key.strip())


# Global singleton configuration instance
config = Config()
