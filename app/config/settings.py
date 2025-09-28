from pydantic_settings import BaseSettings
from typing import Optional, List
import json

class Settings(BaseSettings):
    # Database
    database_url: str
    testing: bool = False
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Application
    environment: str = "development"
    debug: bool = True
    api_v1_str: str = "/api/v1"
    project_name: str = "BookIt API"
    version: str = "1.0.0"
    
    # CORS
    backend_cors_origins: str = '["http://localhost:3000"]'
    
    # Admin User
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    admin_name: str = "System Administrator"
    
    # Logging
    log_level: str = "INFO"
    
    # Security (for production)
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        try:
            return json.loads(self.backend_cors_origins)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    class Config:
        env_file = ".env"

settings = Settings()