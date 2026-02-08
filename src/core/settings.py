from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for paths and environment."""

    task_config_dir: Path = Path("configs/tasks")
    llm_enabled: bool = False
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 30
    llm_fallback_to_rules: bool = True
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    azure_openai_api_key: str | None = Field(default=None, validation_alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str | None = Field(
        default=None, validation_alias="AZURE_OPENAI_ENDPOINT"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        validation_alias="AZURE_OPENAI_API_VERSION",
    )
    azure_openai_deployment: str | None = Field(
        default=None, validation_alias="AZURE_OPENAI_DEPLOYMENT"
    )

    model_config = SettingsConfigDict(env_prefix="P4AGENT_", env_file=".env", extra="ignore")


settings = Settings()
