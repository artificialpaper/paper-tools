"""Paper Tools Configuration Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class PaperToolsSettings(BaseSettings):
    """Configuration settings for paper-tools service."""

    service_name: str = "paper-tools"
    environment: str = "local"
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50053

    default_timeout_ms: int = 30000
    sandbox_workspace_dir: str = "/tmp/paper_sandbox"
    max_memory_mb: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> PaperToolsSettings:
    """Return singleton instance of PaperToolsSettings."""
    return PaperToolsSettings()
