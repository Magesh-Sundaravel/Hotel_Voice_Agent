from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""
    SUPABASE_DB_URL: str = ""

    # Hotel defaults (Sina Bernini Bristol, Roma)
    DEFAULT_HOTEL_NAME: str = "Sina Bernini Bristol"
    DEFAULT_HOTEL_PHONE: str = "+39 06 4883051"
    DEFAULT_HOTEL_ADDRESS: str = "Piazza Barberini 23, Roma"
    DEFAULT_RESTAURANT_NAME: str = "Sina Bernini Bristol"
    DEFAULT_RESTAURANT_PHONE: str = "+39 06 4883051"
    DEFAULT_TIMEZONE: str = "Europe/Rome"
    DEFAULT_SLOT_DURATION_MINUTES: int = 90

    # Server settings
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    PUBLIC_URL: str = ""
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Twilio settings
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = Field(
        default="",
        validation_alias=AliasChoices("TWILIO_PHONE_NUMBER", "TWILIO_FROM_NUMBER"),
    )

    # ElevenLabs settings
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = (
        "Xb7hH8MSUJpSbSDYk0k2"  # Alice (default free & paid supported premade voice)
    )
    ELEVENLABS_MODEL_ID: str = "eleven_turbo_v2_5"

    # STT Provider ("groq" or "elevenlabs")
    STT_PROVIDER: str = "groq"

    # Email / SMTP settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "prenotazioni@sinahotels.com"

    # Owner notification settings
    OWNER_EMAIL: str = ""
    OWNER_PHONE: str = ""

    # API Authentication & Webhook Security
    API_KEY: str = ""
    TWILIO_VALIDATE_SIGNATURE: bool = False


settings = Settings()
