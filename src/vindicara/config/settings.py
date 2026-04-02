"""Environment-based configuration using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings


class VindicaraSettings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = {"env_prefix": "VINDICARA_"}

    api_key: str = Field(default="", description="Vindicara API key")
    api_base_url: str = Field(
        default="https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com",
        description="Base URL for Vindicara API",
    )
    offline_mode: bool = Field(
        default=False,
        description="Run in offline mode (local evaluation only)",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    stage: str = Field(default="dev", description="Deployment stage")
    request_timeout_seconds: float = Field(
        default=10.0,
        description="HTTP request timeout in seconds",
    )
