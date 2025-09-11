from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    Qdrant_url: str = "http://localhost:6333"
    GROQ_API_KEY: str
    FIRECRAWL_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

