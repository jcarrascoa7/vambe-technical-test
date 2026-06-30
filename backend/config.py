from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/vambe"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "vambe"
    LLM_API_KEY: str = ""
    LLM_API_URL: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    LLM_MODEL: str = "mimo-v2.5-pro"
    MAX_RECORDS_TO_CATEGORIZE: int = 100

    class Config:
        env_file = ".env"


settings = Settings()
