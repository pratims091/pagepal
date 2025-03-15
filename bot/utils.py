"""
Bot utilities for PagePal application.
Provides utility functions for the Telegram bot.
"""

from typing import Any, Dict, List, Optional

from utils.logger import bot_logger as logger

# Global cache for user conversations
# user_id -> {"chain": chain, "streaming_chain": streaming_chain, "history": [(question, answer)], "website_id": website_id}
_user_conversations: Dict[str, Dict[str, Any]] = {}


def get_user_conversation(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the user's conversation.

    Args:
        user_id: The user ID

    Returns:
        Optional[Dict[str, Any]]: The conversation if found, None otherwise
    """
    return _user_conversations.get(user_id)


def set_user_conversation(
    user_id: str,
    chain: Any,
    streaming_chain: Any,
    website_id: str,
    history: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Set the user's conversation.

    Args:
        user_id: The user ID
        chain: The QA chain
        streaming_chain: The streaming QA chain
        website_id: The website ID
        history: List of dictionaries containing question and answer pairs (optional)
    """
    _user_conversations[user_id] = {
        "chain": chain,
        "streaming_chain": streaming_chain,
        "history": history or [],
        "website_id": website_id,
    }
    logger.info(f"Set conversation for user {user_id} with website {website_id}")


def update_conversation_history(user_id: str, question: str, answer: str) -> None:
    """
    Update the user's conversation history.

    Args:
        user_id: The user ID
        question: The user's question
        answer: The assistant's answer
    """
    conversation = get_user_conversation(user_id)

    if not conversation:
        logger.warning(
            f"Cannot update history for user {user_id}: conversation not found"
        )
        return

    # Add the new exchange to history
    conversation["history"].append({"human": question, "system": answer})

    # Limit history to last 10 exchanges to prevent context overflow
    if len(conversation["history"]) > 10:
        conversation["history"] = conversation["history"][-10:]

    logger.debug(
        f"Updated history for user {user_id}, now has {len(conversation['history'])} exchanges"
    )


def clear_user_conversation(user_id: str) -> None:
    """
    Clear the user's conversation history.

    Args:
        user_id: The user ID
    """
    conversation = get_user_conversation(user_id)

    if not conversation:
        logger.debug(f"Cannot clear history for user {user_id}: conversation not found")
        return

    # Clear history but keep the chain and website_id
    conversation["history"] = []
    logger.info(f"Cleared history for user {user_id}")


def format_sources_text(source_documents: List[Any]) -> str:
    """
    Format source documents as text.

    Args:
        source_documents: List of source documents

    Returns:
        str: Formatted source text
    """
    if not source_documents:
        return ""

    unique_sources = set()
    for doc in source_documents:
        source_url = doc.metadata.get("source", "")
        if source_url and source_url not in unique_sources:
            unique_sources.add(source_url)

    if not unique_sources:
        return ""

    sources_text = "\n\n📚 Sources:\n"
    for i, source in enumerate(list(unique_sources)[:3]):  # Limit to 3 sources
        sources_text += f"• {source}\n"

    if len(unique_sources) > 3:
        sources_text += f"• ...and {len(unique_sources) - 3} more sources\n"

    return sources_text
