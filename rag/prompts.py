"""
Prompt templates for PagePal application.
Provides templates for QA and other interactions.
"""

from functools import lru_cache

from langchain import hub
from langchain_core.prompts import ChatPromptTemplate

from utils.logger import rag_logger as logger


@lru_cache(maxsize=1)
def get_qa_prompt() -> ChatPromptTemplate:
    """
    Get the QA prompt template.
    Tries to use LangChain Hub, with fallback to custom prompt.
    Uses LRU cache to avoid creating multiple instances.

    Returns:
        ChatPromptTemplate: The prompt template
    """
    try:
        # Try to get prompt from LangChain Hub
        try:
            prompt = hub.pull("langchain-ai/retrieval-qa-chat")
            logger.info("Using QA prompt from LangChain Hub")
            return prompt
        except Exception as e:
            logger.warning(f"Failed to pull from hub: {e}. Using custom prompt.")

        # Fallback to custom prompt
        prompt = ChatPromptTemplate.from_template(
            """
        You are PagePal, an AI assistant that helps users understand website content.
        Answer the following question based on the provided context from the crawled website.
        
        <context>
        {context}
        </context>
        
        Chat History:
        {chat_history}
        
        Question: {question}
        
        When answering, be informative and extract specific details from the context. 
        If the answer cannot be found in the context, say "I don't have enough information about that from the website."
        Include relevant URLs from the context when appropriate.
        """
        )

        logger.info("Created custom QA prompt")
        return prompt
    except Exception as e:
        logger.error(f"Failed to create QA prompt: {e}")
        raise
