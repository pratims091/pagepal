"""
LLM models for PagePal application.
Provides access to language models.
"""

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from config import config
from utils.logger import rag_logger as logger


@lru_cache(maxsize=2)  # Cache both streaming and non-streaming models
def get_llm_model(streaming: bool = False) -> ChatGoogleGenerativeAI:
    """
    Get the LLM model.
    Uses LRU cache to avoid creating multiple instances.

    Args:
        streaming: Whether to enable streaming

    Returns:
        ChatGoogleGenerativeAI: The LLM model
    """
    try:
        # Create LLM model
        llm_model = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.7,
            top_p=0.95,
            convert_system_message_to_human=True,
            streaming=streaming,  # Enable/disable streaming
        )

        logger.info(f"Created LLM model: {config.LLM_MODEL} (streaming={streaming})")
        return llm_model
    except Exception as e:
        logger.error(f"Failed to create LLM model: {e}")
        raise
