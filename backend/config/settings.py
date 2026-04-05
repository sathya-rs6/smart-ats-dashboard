import os
from typing import Optional, List
from pydantic import Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings
    PYDANTIC_V2 = False


class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    # Vector Store Configuration
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    vector_store_type: str = "chroma"
    chroma_persist_directory: str = "./vector_stores/chroma_db"
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "resume-analyzer"

    # Database Configuration
    database_url: str = "sqlite:///./models/resume_analyzer.db"

    # Application Settings
    default_llm_provider: str = "openai"
    llm_temperature: float = 0.1
    max_tokens: int = 2000
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Scoring Configuration
    hard_match_weight: float = 0.4
    semantic_match_weight: float = 0.6
    similarity_threshold: float = 0.7

    # File Upload Settings
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,docx,txt"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # Web Application
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # SMTP Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

    def get_allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions as list"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]


settings = Settings()
