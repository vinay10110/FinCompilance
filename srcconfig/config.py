from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    TOGETHER_API_KEY: str
    MODEL_NAME: str = "togethercomputer/llama-2-7b-chat"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # RBI Website Configuration
    RBI_BASE_URL: str = "https://www.rbi.org.in"
    RBI_UPDATES_URL: str = "https://www.rbi.org.in/Scripts/NotificationUser.aspx"
    
    # Vector Store Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "RBI Compliance Automation System"
    
    class Config:
        env_file = ".env"

settings = Settings()