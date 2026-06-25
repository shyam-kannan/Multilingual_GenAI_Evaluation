from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@db:5432/eval_gateway"
    anthropic_api_key: str = ""
    environment: str = "development"

    quality_threshold: float = 0.7
    hallucination_threshold: float = 0.3
    regression_delta: float = 0.1

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
