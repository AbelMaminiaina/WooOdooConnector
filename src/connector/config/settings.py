from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # WooCommerce
    woo_url: str = "http://localhost:8080"
    woo_consumer_key: str = "test_key"
    woo_consumer_secret: str = "test_secret"

    # Odoo
    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "test_db"
    odoo_username: str = "admin"
    odoo_password: str = "admin"

    # API
    api_host: str = (
        "0.0.0.0"  # nosec B104 - Binding to all interfaces is required for Docker
    )
    api_port: int = 8000
    api_secret_key: str = "dev-secret-key-change-in-production"

    # Sync
    sync_enabled: bool = True
    sync_interval_minutes: int = 15

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Singleton instance
settings = Settings()
