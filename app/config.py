"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    database_url: str = "postgresql://user:password@localhost:5432/clara"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    claude_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
