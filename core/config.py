from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Voice Orchestrator"
    port: int = 8000
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    system_service_base_url: str = "http://system-service:8000"
    mail_pending_dir: str = "/shared/mail/pending"
    weather_service_base_url: str = "http://weather-service:8000"

    # Similarity engine parameters
    similarity_threshold: float = 60.0
    tie_breaker_threshold: float = 5.0

    # RapidFuzz similarity weights
    weight_ratio: float = 0.20
    weight_partial_ratio: float = 0.30
    weight_token_sort_ratio: float = 0.20
    weight_token_set_ratio: float = 0.30

    @model_validator(mode="after")
    def validate_weights(self) -> 'Settings':
        total = (
            self.weight_ratio + 
            self.weight_partial_ratio + 
            self.weight_token_sort_ratio + 
            self.weight_token_set_ratio
        )
        if not abs(total - 1.0) < 1e-6:
            raise ValueError(f"The sum of similarity weights must be exactly 1.0, got {total}")
        return self

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

