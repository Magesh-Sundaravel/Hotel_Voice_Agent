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


settings = Settings()
