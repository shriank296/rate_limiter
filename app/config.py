from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_PORT: int = 6379
    REDIS_HOST: str = "localhost"


settings = Settings()
