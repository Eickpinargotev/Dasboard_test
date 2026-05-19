from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    X_BEARER_TOKEN: str = ""
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/social_db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
