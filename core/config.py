from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Voice Orchestrator"
    port: int = 8000
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    system_service_base_url: str = "http://system-service:8000"
    user_email: str = "user@example.com"
    mail_pending_dir: str = "/shared/mail/pending"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
