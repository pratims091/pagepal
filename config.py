"""
Configuration module for PagePal application.
Loads environment variables and provides configuration settings.
"""

import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for PagePal application."""

    # Bot settings
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    STREAMING_ENABLED: bool = os.getenv("STREAMING_ENABLED", "True").lower() in [
        "true",
        "1",
        "yes",
    ]

    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    CRAWL4AI_API_TOKEN: str = os.getenv("CRAWL4AI_API_TOKEN", "")

    # Crawler settings
    CRAWL4AI_HOST: str = os.getenv("CRAWL4AI_HOST", "http://crawl4ai:11235")
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT", "300"))  # 5 minutes

    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Vector store
    PERSIST_DIRECTORY: str = os.getenv("VECTOR_STORE_DIR", "data/chroma_db")

    # LLM settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/embedding-001")

    # Cache settings
    CACHE_EXPIRY_DAYS: int = int(os.getenv("CACHE_EXPIRY_DAYS", "30"))

    # Streaming settings
    STREAM_CHUNK_SIZE: int = int(
        os.getenv("STREAM_CHUNK_SIZE", "25")
    )  # Characters per chunk

    # Logging settings
    LOG_LEVEL_STR: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_LEVEL: int = getattr(logging, LOG_LEVEL_STR, logging.INFO)
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

    URL_CRAWL_LIMIT: Optional[int] = os.getenv("URL_CRAWL_LIMIT", 100)

    @classmethod
    def validate(cls) -> Optional[str]:
        """
        Validate that all required configuration is present.

        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """
        required_vars = [
            "TELEGRAM_TOKEN",
            "GOOGLE_API_KEY",
            "CRAWL4AI_API_TOKEN",
            "SUPABASE_URL",
            "SUPABASE_KEY",
        ]

        missing = [var for var in required_vars if not getattr(cls, var)]

        if missing:
            return f"Missing required environment variables: {', '.join(missing)}"

        return None

    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("__") and not callable(value)
        }


# Create a config instance for easy importing
config = Config()
