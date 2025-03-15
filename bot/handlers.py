"""
Message handlers for PagePal application.
Handles URL and question messages.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.utils import (
    format_sources_text,
    get_user_conversation,
    set_user_conversation,
    update_conversation_history,
)
from config import config
from crawler.crawler import crawl_url
from crawler.processor import chunk_documents, process_crawl_results
from db.supabase import db_client
from db.vector_store import vector_store_manager
from rag.chains import (
    create_qa_chain,
    create_streaming_qa_chain,
    run_qa_chain,
    stream_qa_chain,
)
from utils.logger import bot_logger as logger

# URL pattern for basic validation
URL_PATTERN = re.compile(r"^https?://[\w\-]+(\.[\w\-]+)+[/#?]?.*$")


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle URL messages.
    Crawl the website and set up the conversation.

    Args:
        update: The update event
        context: The context
    """
    url = update.message.text
    user_id = str(update.effective_user.id)

    # Validate URL format
    if not URL_PATTERN.match(url):
        await update.message.reply_text(
            "⚠️ Please send a valid URL starting with http:// or https://"
        )
        return

    logger.info(f"User {user_id} sent URL: {url}")

    # Check if URL was crawled recently
    website = db_client.get_website_by_url(url)

    if website:
        # Check if website data is still valid
        last_crawled = datetime.fromisoformat(
            website["last_crawled"].replace("Z", "+00:00")
        )
        if datetime.now().astimezone() - last_crawled < timedelta(
            days=config.CACHE_EXPIRY_DAYS
        ):
            await update.message.reply_text(
                f"📂 This website was crawled recently on {last_crawled.strftime('%Y-%m-%d')}. "
                f"I'll use the existing data for our conversation."
            )

            # Set up conversation with existing data
            await setup_conversation(user_id, website["id"], update)
            return

    # Send a message that crawling is starting
    status_message = await update.message.reply_text(
        "🔍 Starting to crawl the website. This may take a few minutes..."
    )

    try:
        # Crawl the website
        results = await crawl_url(url)

        if not results:
            await status_message.edit_text(
                "❌ No content could be extracted from the website. "
                "Please try a different URL."
            )
            return

        await status_message.edit_text(
            "🔍 Website crawled! Now processing the content..."
        )

        # Process the crawl results
        await process_crawl_data(user_id, url, results, status_message, update)

    except TimeoutError:
        await status_message.edit_text(
            "⏱️ Crawling is taking longer than expected. Please try again later or "
            "try a smaller website."
        )
    except Exception as e:
        logger.error(f"Error during URL handling: {str(e)}")
        await status_message.edit_text(f"❌ Error crawling the website: {str(e)}")


async def process_crawl_data(
    user_id: str,
    url: str,
    results: List[Dict[str, Any]],
    status_message: Any,
    update: Update,
) -> None:
    """
    Process crawled website data.

    Args:
        user_id: The user ID
        url: The website URL
        results: The crawl results
        status_message: The status message to update
        update: The update event
    """
    try:
        # Extract documents from crawl results
        documents = process_crawl_results(results, url)

        if not documents:
            await status_message.edit_text(
                "❌ No content could be extracted from the website. "
                "Please try a different URL."
            )
            return

        # Chunk documents
        chunked_documents = chunk_documents(documents)

        # Generate vector store ID
        vector_store_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create vector store
        vector_store_manager.create_vector_store(chunked_documents, vector_store_id)

        # Save to database
        website_id = db_client.save_crawled_website(url, vector_store_id)

        # Set up conversation
        await setup_conversation(user_id, website_id, update, status_message)

    except Exception as e:
        logger.error(f"Error processing crawl data: {str(e)}")
        await status_message.edit_text(f"❌ Error processing website content: {str(e)}")


async def setup_conversation(
    user_id: str, website_id: str, update: Update, status_message: Optional[Any] = None
) -> None:
    """
    Set up conversation with the website.

    Args:
        user_id: The user ID
        website_id: The website ID
        update: The update event
        status_message: The status message to update (optional)
    """
    try:
        # Get website info
        website = db_client.get_website(website_id)
        vector_store_id = website["vector_store_id"]

        # Get retriever
        retriever = vector_store_manager.get_retriever(vector_store_id)

        # Create QA chains - both streaming and non-streaming versions
        qa_chain = create_qa_chain(retriever)
        streaming_qa_chain = create_streaming_qa_chain(retriever)

        # Set up conversation context
        set_user_conversation(user_id, qa_chain, streaming_qa_chain, website_id)

        # Update user session in database
        db_client.update_user_session(user_id, website_id)

        # Provide feedback to user
        completion_message = (
            f"✅ Successfully processed {website['url']}!\n\n"
            f"You can now ask me questions about this website."
        )

        if status_message:
            await status_message.edit_text(completion_message)
        else:
            await update.message.reply_text(completion_message)

    except Exception as e:
        logger.error(f"Error setting up conversation: {str(e)}")
        error_message = f"❌ Error setting up conversation: {str(e)}"

        if status_message:
            await status_message.edit_text(error_message)
        else:
            await update.message.reply_text(error_message)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages (questions).

    Args:
        update: The update event
        context: The context
    """
    user_id = str(update.effective_user.id)
    message = update.message.text

    # Check if the message is a URL
    if URL_PATTERN.match(message):
        return await handle_url(update, context)

    logger.info(f"User {user_id} sent question: {message}")

    # Check if user has an active conversation
    conversation = get_user_conversation(user_id)

    if not conversation:
        # Check if user has a previous session in the database
        session = db_client.get_user_session(user_id)

        if not session:
            await update.message.reply_text(
                "Please send a website URL first so I can crawl it and answer your questions."
            )
            return

        # Restore the session
        website_id = session["website_id"]
        await update.message.reply_text(
            "I'm restoring your previous session. Let me process your question..."
        )

        # Set up conversation context
        await setup_conversation(user_id, website_id, update)

        # Get the conversation again
        conversation = get_user_conversation(user_id)

        if not conversation:
            await update.message.reply_text(
                "❌ Error restoring your previous session. "
                "Please send a website URL to start a new session."
            )
            return

    # Use the conversation chain to get an answer
    try:
        # Send typing action
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )

        # Check if streaming is enabled in config
        if config.STREAMING_ENABLED:
            # Send initial message that will be updated with streaming tokens
            response_message = await update.message.reply_text(
                "Thinking...", parse_mode=ParseMode.MARKDOWN
            )

            # Create a token accumulator for streaming
            accumulated_text = ""

            # Create a token handler function
            async def handle_token(token: str):
                nonlocal accumulated_text
                accumulated_text += token

                # Only update the message periodically to avoid Telegram API rate limits
                # Update roughly every N characters (from config) or if response is very short
                if (
                    len(accumulated_text) % config.STREAM_CHUNK_SIZE == 0
                    or len(accumulated_text) < 50
                ):
                    try:
                        await response_message.edit_text(
                            accumulated_text, parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception:
                        # If markdown parsing fails, try without parse mode
                        try:
                            await response_message.edit_text(accumulated_text)
                        except Exception as e:
                            logger.warning(f"Failed to update message: {e}")

            # Use streaming chain
            result = await stream_qa_chain(
                chain=conversation["streaming_chain"],
                question=message,
                history=conversation["history"],
                token_callback=handle_token,
            )

            # Get the answer and source documents
            answer = result.get("answer", "")
            if not answer and "result" in result:
                answer = result["result"]

            source_documents = result.get("source_documents", [])

            # Add sources to the answer
            sources_text = format_sources_text(source_documents)
            if sources_text:
                answer += sources_text

                # Update the message one last time with sources
                try:
                    await response_message.edit_text(
                        answer, parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    # If markdown parsing fails, try without parse mode
                    try:
                        await response_message.edit_text(answer)
                    except Exception as e:
                        logger.warning(f"Failed to update final message: {e}")
        else:
            # Non-streaming approach
            result = await run_qa_chain(
                chain=conversation["chain"],
                question=message,
                history=conversation["history"],
            )

            print(result)
            # Extract the answer and source documents
            answer = result.get("answer", "")
            if not answer and "result" in result:
                answer = result["result"]

            source_documents = result.get("source_documents", [])

            # Add sources to the answer
            sources_text = format_sources_text(source_documents)
            if sources_text:
                answer += sources_text

            await update.message.reply_text(answer)

        # Update conversation history
        update_conversation_history(user_id=user_id, question=message, answer=answer)

        # Update session last activity
        db_client.update_user_session(user_id, conversation["website_id"])

    except Exception as e:
        print(e)
        logger.error(f"Error answering question: {str(e)}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error while processing your question. Please try again."
        )
