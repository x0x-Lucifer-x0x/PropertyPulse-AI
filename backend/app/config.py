import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    database_url: str = os.getenv("DATABASE_URL", "")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    use_sqlite_fallback: bool = os.getenv("USE_SQLITE_FALLBACK", "false").lower() == "true"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def resolved_database_url(self) -> str:
        if self.database_url and "[YOUR-" not in self.database_url:
            return self.database_url
        if self.use_sqlite_fallback:
            return "sqlite:///./property_pulse.db"
        raise RuntimeError(
            "DATABASE_URL is not set. Either configure Supabase Postgres in "
            "DATABASE_URL, or set USE_SQLITE_FALLBACK=true for local dev."
        )

    class Config:
        env_file = ".env"


settings = Settings()
