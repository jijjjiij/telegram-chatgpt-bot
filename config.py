"""
Configuration module for Telegram ChatGPT Bot.
Loads settings from environment variables for secure credential management.
"""

import os
from typing import Optional


class Config:
    """Bot configuration class using environment variables."""

    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

    # OpenAI/ChatGPT Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))

    # Bot Behavior Settings
    BOT_NAME: str = os.getenv("BOT_NAME", "ChatGPT Bot")
    BOT_DESCRIPTION: str = os.getenv("BOT_DESCRIPTION", "A Telegram bot powered by ChatGPT")
    BOT_COMMAND_PREFIX: str = os.getenv("BOT_COMMAND_PREFIX", "/")

    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

    # Database Settings (Optional)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", "30"))

    # Webhook Settings (Optional)
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))
    POLLING_MODE: bool = os.getenv("POLLING_MODE", "True").lower() == "true"

    # Application Settings
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    @classmethod
    def validate(cls) -> bool:
        """
        Validate critical configuration settings.

        Returns:
            bool: True if all required settings are present, False otherwise.
        """
        required_fields = ["TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"]
        missing_fields = [field for field in required_fields if not getattr(cls, field)]

        if missing_fields:
            print(f"Error: Missing required environment variables: {', '.join(missing_fields)}")
            return False

        return True

    @classmethod
    def get_config_summary(cls) -> dict:
        """
        Get a summary of the current configuration (excluding sensitive data).

        Returns:
            dict: Configuration summary without sensitive credentials.
        """
        return {
            "bot_name": cls.BOT_NAME,
            "openai_model": cls.OPENAI_MODEL,
            "log_level": cls.LOG_LEVEL,
            "debug_mode": cls.DEBUG_MODE,
            "environment": cls.ENVIRONMENT,
            "polling_mode": cls.POLLING_MODE,
            "rate_limit_enabled": cls.RATE_LIMIT_ENABLED,
        }


# Example usage
if __name__ == "__main__":
    if Config.validate():
        print("✓ Configuration is valid")
        print("Configuration Summary:")
        for key, value in Config.get_config_summary().items():
            print(f"  {key}: {value}")
    else:
        print("✗ Configuration validation failed")
