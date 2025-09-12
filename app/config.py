from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    Qdrant_url: str = "http://localhost:6333"
    GROQ_API_KEY: str
    FIRECRAWL_API_KEY: str
    mongodb_uri: str = ""
    mongodb_db: str = "article_explorer"
    mongodb_collection: str = "chunks"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

