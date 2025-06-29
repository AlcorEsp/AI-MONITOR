from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación AI Ops Suite"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    debug: bool = True
    
    # Database Configuration
    database_url: str = "sqlite:///./aiops_db.sqlite"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Scale AI Integration
    scale_api_key: Optional[str] = None
    scale_api_url: str = "https://api.scale.com/v1"
    scale_webhook_secret: Optional[str] = None
    mock_scale_api: bool = True
    
    # Monitoring & Observability
    prometheus_port: int = 9090
    grafana_port: int = 3000
    grafana_admin_password: str = "admin"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Email Notifications
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@aiops-suite.com"
    
    # Slack Integration
    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#ai-ops-alerts"
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None
    
    # Feature Flags
    enable_cost_optimizer: bool = True
    enable_compliance_guardian: bool = True
    enable_real_time_alerts: bool = True
    enable_ml_predictions: bool = True
    
    # Development Settings
    enable_debug_routes: bool = True
    skip_auth_in_dev: bool = False
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 