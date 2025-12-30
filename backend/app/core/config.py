"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "spur_chat"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Upstash Redis Configuration (alternative to redis_url)
    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None
    
    # Google Gemini API
    google_api_key: str  # Google Gemini API key
    google_model: str = "gemini-2.5-flash"  # Gemini model name (e.g., gemini-2.5-flash, gemini-3-flash)
    
    # Application Settings
    max_message_length: int = 2000
    llm_max_tokens: int = 500
    llm_temperature: float = 0.7
    message_history_limit: int = 10
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env (like old Azure OpenAI vars)


settings = Settings()

