"""Configuration Management for Stock Analysis System"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings - Load from .env file and environment variables"""

    # Application
    environment: str = "development"
    debug: bool = True
    api_version: str = "v1"
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Database
    database_url: str = "mysql+pymysql://root:password@localhost:3306/stock_analysis_db"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    baidu_api_key: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Data Configuration
    data_retention_days: int = 30
    cache_ttl_hours: int = 24
    analysis_timeout_seconds: int = 60

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Task Scheduler
    scheduler_enabled: bool = True
    task_execution_timeout: int = 300

    # Trading Hours (Chinese market)
    market_open_time: str = "09:30"
    market_close_time: str = "15:00"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Create a global settings instance
settings = get_settings()
