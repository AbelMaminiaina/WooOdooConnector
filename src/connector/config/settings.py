from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # WooCommerce
    woo_url: str
    woo_consumer_key: str
    woo_consumer_secret: str

    # Odoo
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_password: str

    # Database
    database_url: str = "sqlite:///./woo_odoo.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str

    # Sync
    sync_enabled: bool = True
    sync_interval_minutes: int = 15

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
