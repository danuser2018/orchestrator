from pydantic_settings import BaseSettings, SettingsConfigDict

class IdentitySettings(BaseSettings):
    system_service_base_url: str = "http://system-service:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = IdentitySettings()
