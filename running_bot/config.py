"""Project configuration."""
from pathlib import Path

import google.auth
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunSetting(BaseSettings):
    """Configuration object affecting all parts of decisioning pipeline.

    All config value can be altered via environment variables or .env file. The values must be prefixed
    with "LINEBOT_" prefix. Here is the example of default configuration as .env file
    (the environment variables will have the same names):

    LINEBOT_LINE_CHANNEL_SECRET_KEY=""
    LINEBOT_LINE_ACCESS_TOKEN=""

    LINEBOT_REDIS_HOST=""
    LINEBOT_REDIS_PASSWORD=""
    LINEBOT_REDIS_PORT=50000

    LINEBOT_PROJECT_ID=""
    """

    model_config = SettingsConfigDict(
        env_prefix="linebot_",
        env_file=Path(__file__) / ".env",
        env_nested_delimiter="__",
    )

    @field_validator("project_id", mode="before")
    @staticmethod
    def get_current_project_id(value: str | None) -> str | None:
        """Get default project_id if project_id is not speficied."""
        if value is None:
            try:
                _, project_id = google.auth.default()
            except Exception as _:
                return None
            return project_id
        return None

    line_channel_secret_key: SecretStr = SecretStr("")
    line_access_token: SecretStr = SecretStr("")

    firestore_database: str = "intania92-runner-leaderboard"
    firestore_leaderboard_collection: str = "leaderboard"

    redis_host: str = ""
    redis_password: SecretStr = SecretStr("")
    redis_port: int = 6379

    project_id: str | None = None


cfg = RunSetting()
