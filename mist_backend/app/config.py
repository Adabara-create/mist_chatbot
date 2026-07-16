from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. Reads from environment variables / .env file."""

    groq_api_key: str
    tavily_api_key: str
    mist_model: str = "openai/gpt-oss-120b"
    mist_data_dir: str = "app/data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def data_dir(self) -> Path:
        path = Path(self.mist_data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
