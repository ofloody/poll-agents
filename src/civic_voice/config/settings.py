"""Configuration settings using Pydantic."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SMTPSettings(BaseSettings):
    """SMTP email configuration."""
    model_config = SettingsConfigDict(env_prefix="SMTP_")

    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    sender_email: str = ""
    use_tls: bool = True


class ServerSettings(BaseSettings):
    """WebSocket server configuration."""
    model_config = SettingsConfigDict(env_prefix="SERVER_")

    host: str = "localhost"
    port: int = 8765


class StorageSettings(BaseSettings):
    """Storage backend configuration."""
    model_config = SettingsConfigDict(env_prefix="STORAGE_")

    backend: str = "local"  # local, postgres, mongodb (future)
    data_path: str = "./data"


class VerificationSettings(BaseSettings):
    """Verification code configuration."""
    model_config = SettingsConfigDict(env_prefix="VERIFICATION_")

    code_length: int = 6
    code_expiry_seconds: int = 300


class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    smtp: SMTPSettings = Field(default_factory=SMTPSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    verification: VerificationSettings = Field(default_factory=VerificationSettings)
