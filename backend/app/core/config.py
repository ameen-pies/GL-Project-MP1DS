"""Typed settings for the API.

Values come from the repository-root ``.env`` file, then from the real
environment. Every setting has a safe local default so the app and the test
suite can start without a configured machine.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )

    # Database
    database_url: str = "sqlite:///./fleet.db"
    test_database_url: str = "sqlite:///./fleet_test.db"

    # Auth
    secret_key: str = "change-me-in-real-life"
    access_token_expire_minutes: int = 60

    # Browser access
    cors_origins: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8000"

    # Mail (SCRUM-30)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "alerts@fleet-control.local"

    # Seed accounts (SCRUM-20)
    seed_admin_password: str = "Admin123!"
    seed_operator_password: str = "Operator123!"

    # Incident prediction model (SCRUM-37)
    model_path: str = "ml/models/incident_model.joblib"

    @property
    def model_file(self) -> Path:
        path = Path(self.model_path)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def metrics_file(self) -> Path:
        return self.model_file.parent / "metrics.json"

    @property
    def cors_origin_list(self) -> list[str]:
        """Split the comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
