from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Read from env vars or api/.env. Secrets never leave the backend."""

    # hide_input_in_errors: a failed startup must never print the keys into logs.
    model_config = SettingsConfigDict(
        env_file=(".env", "api/.env"), extra="ignore", hide_input_in_errors=True
    )

    offscript_env: Literal["development", "production"] = "development"
    offscript_mode: Literal["live", "mock"] = "live"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    tinker_api_key: str = ""
    tinker_model_path: str = ""
    serpapi_api_key: str = ""
    hf_token: str = ""  # optional: avoids Hugging Face rate limits on tokenizer download

    @model_validator(mode="after")
    def _no_mock_in_production(self) -> "Settings":
        if self.offscript_env == "production" and self.offscript_mode == "mock":
            raise ValueError("OFFSCRIPT_MODE=mock is not allowed when OFFSCRIPT_ENV=production")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def model_configured(self) -> bool:
        return bool(self.tinker_api_key and self.tinker_model_path)

    @property
    def serpapi_configured(self) -> bool:
        return bool(self.serpapi_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
