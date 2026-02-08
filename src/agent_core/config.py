from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for paths and environment."""

    task_config_dir: Path = Path("configs/tasks")

    model_config = SettingsConfigDict(env_prefix="P4AGENT_", env_file=".env", extra="ignore")


settings = Settings()
