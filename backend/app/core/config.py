from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = 'echo'
    POSTGRES_PASSWORD: str = 'echo_password'
    POSTGRES_DB: str = 'echo_db'
    POSTGRES_HOST: str = 'postgres'
    POSTGRES_PORT: int = 5432
    REDIS_URL: str = 'redis://redis:6379/0'
    API_V1_PREFIX: str = '/api'

    @property
    def DATABASE_URL(self) -> str:
        return (
            f'postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
