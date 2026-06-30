from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/vambe"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "vambe"
    GEMMA_API_KEY: str = ""
    GEMMA_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/gemma-4:generateContent"
    MAX_RECORDS_TO_CATEGORIZE: int = 1000

    class Config:
        env_file = ".env"


settings = Settings()
