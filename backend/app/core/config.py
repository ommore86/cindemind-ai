"""
CineMind AI — Core Application Configuration
Loads configuration from environment variables with fallback defaults.
"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "CineMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = Field(default=8000)
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # CORS & Deployed Frontend URL
    FRONTEND_URL: str = ""
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    def get_cors_origins(self) -> List[str]:
        origins = list(self.BACKEND_CORS_ORIGINS) if isinstance(self.BACKEND_CORS_ORIGINS, list) else [self.BACKEND_CORS_ORIGINS]
        if self.FRONTEND_URL and self.FRONTEND_URL.strip():
            clean_fe = self.FRONTEND_URL.strip().rstrip("/")
            if clean_fe not in origins:
                origins.append(clean_fe)
        return origins
    
    # Database
    DATABASE_URL: str = "sqlite:///./cinemind.db"
    
    # Data Paths
    DATA_RAW_DIR: str = "data/raw"
    DATA_PROCESSED_DIR: str = "data/processed"
    EVALUATION_REPORT_PATH: str = "data/processed/evaluation_report.json"
    DATA_QUALITY_REPORT_PATH: str = "data/processed/data_quality_report.json"
    
    # Hybrid Weights (Default baseline: 45% Content, 40% Collaborative, 15% Sentiment)
    CONTENT_WEIGHT: float = 0.45
    COLLABORATIVE_WEIGHT: float = 0.40
    SENTIMENT_WEIGHT: float = 0.15
    
    # Sentiment Model
    SENTIMENT_MODEL_NAME: str = "distilbert-base-uncased-finetuned-sst-2-english"
    USE_GPU: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
