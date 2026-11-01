from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Veritas API"
    debug: bool = False

    # CORS
    frontend_url: str = "http://localhost:5173"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_secret_key: str = ""
    supabase_publishable_key: str = ""
    supabase_jwks_url: str = ""

    # LLM
    google_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # Search & APIs
    tavily_api_key: str = ""
    mediacloud_api_key: str = ""
    google_factcheck_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
