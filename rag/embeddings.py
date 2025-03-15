"""
Embedding models for PagePal application.
Provides access to text embedding models.
"""

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import config
from utils.logger import rag_logger as logger


@lru_cache(maxsize=1)
def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """
    Get the embedding model.
    Uses LRU cache to avoid creating multiple instances.

    Returns:
        GoogleGenerativeAIEmbeddings: The embedding model
    """
    try:
        # Create embedding model
        embedding_model = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL, google_api_key=config.GOOGLE_API_KEY
        )

        logger.info(f"Created embedding model: {config.EMBEDDING_MODEL}")
        return embedding_model
    except Exception as e:
        logger.error(f"Failed to create embedding model: {e}")
        raise
