"""
MCMV Dashboard v5 - Configuration Management
Smart configuration loading with environment overrides
"""

import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

class DatabaseSettings(BaseSettings):
    """Database configuration with smart defaults"""
    host: str = Field(default="pac-mcmv-mvp-db-1", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="pac_mcmv", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="postgres123", env="DB_PASSWORD")
    pool_size: int = Field(default=15, env="DB_POOL_SIZE")
    pool_overflow: int = Field(default=25, env="DB_POOL_OVERFLOW")
    query_timeout: int = Field(default=30, env="DB_QUERY_TIMEOUT")
    
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class RedisSettings(BaseSettings):
    """Redis configuration for caching"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    database: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"redis://{self.host}:{self.port}/{self.database}"

class APISettings(BaseSettings):
    """API configuration"""
    title: str = "MCMV Dashboard API v5"
    description: str = "High-performance MCMV dashboard with materialized views"
    version: str = "5.0.0"
    base_path: str = "/api/v5"
    cors_origins: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:8503",
        "http://localhost:8504",
        "http://localhost:8505"
    ])
    rate_limit_per_minute: int = Field(default=300, env="API_RATE_LIMIT")
    debug: bool = Field(default=False, env="API_DEBUG")

class BusinessRulesConfig:
    """Configuration-driven business rules loader"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "business_rules.yaml"
        
        self.config_path = config_path
        self._config = None
        self.load_config()
    
    def load_config(self):
        """Load business rules from YAML configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info("Business rules configuration loaded", config_path=str(self.config_path))
        except Exception as e:
            logger.error("Failed to load business rules configuration", error=str(e))
            raise
    
    @property
    def programs(self) -> Dict:
        return self._config.get('programs', {})
    
    @property
    def status_definitions(self) -> Dict:
        return self._config.get('status_definitions', {})
    
    @property
    def kpis(self) -> Dict:
        return self._config.get('kpis', {})
    
    @property
    def regions(self) -> Dict:
        return self._config.get('regions', {})
    
    @property
    def charts(self) -> Dict:
        return self._config.get('charts', {})
    
    @property
    def performance(self) -> Dict:
        return self._config.get('performance', {})
    
    @property
    def data_quality(self) -> Dict:
        return self._config.get('data_quality', {})
    
    def get_program_config(self, program_name: str) -> Optional[Dict]:
        """Get configuration for specific program"""
        return self.programs.get(program_name)
    
    def get_status_color(self, status: str) -> str:
        """Get color for status"""
        return self.status_definitions.get(status, {}).get('color', '#9E9E9E')
    
    def get_cache_ttl(self, data_type: str) -> int:
        """Get cache TTL for data type"""
        cache_config = self.performance.get('cache_ttl', {})
        return cache_config.get(data_type, 600)  # Default 10 minutes

class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    
    # Redis
    redis: RedisSettings = Field(default_factory=RedisSettings)
    
    # API
    api: APISettings = Field(default_factory=APISettings)
    
    # Security
    secret_key: str = Field(default="mcmv-dashboard-v5-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Monitoring
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Business Rules
    business_rules: BusinessRulesConfig = Field(default_factory=BusinessRulesConfig)
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of {allowed}')
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

# Global settings instance
settings = Settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)