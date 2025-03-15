"""
Bot commands for PagePal application.
Defines command handlers for the Telegram bot.
"""

import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.utils import clear_user_conversation, get_user_conversation
from db.supabase import db_client
from utils.logger import bot_logger as logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    Sends a welcome message to the user.

    Args:
        update: The update event
        context: The context
    """
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")

    await update.message.reply_text(
        f"👋 *Welcome to PagePal, {user.first_name}\\!*\n\n"
        "I help you chat with website content\\. Just send me a URL, and I'll crawl up to *100 pages* for you\\. Once done, you can ask questions about the content\\.\n\n"
        "🔹 *How to use:*\n"
        " 1️⃣ Send a website URL\n"
        " 2️⃣ Wait for me to crawl it\n"
        " 3️⃣ Start asking questions\\!\n\n"
        " 🔗 i’m *open\\-source\\!* Contribute or fork me: [GitHub](https://github.com/pratims091/pagepal)\n\n"
        " 📜 *Privacy Policy & Disclaimer:*  Please respect website terms before using\\. I’m for educational purposes only and may make mistakes [Read here](https://github.com/pratims091/pagepal/tree/dev?tab=readme-ov-file#privacy-policy)\n\n"
        " _Type `/help` to see available commands\\._ 🚀",
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    Sends a help message to the user.

    Args:
        update: The update event
        context: The context
    """
    user = update.effective_user
    logger.info(f"User {user.id} requested help")

    await update.message.reply_text(
        "🔍 PagePal Help:\n\n"
        "1. Send a website URL to crawl it\n"
        "2. Once crawled, ask any questions about the content\n"
        "3. Use /reset to start a new conversation\n"
        "4. Use /status to see your current website\n"
        "5. Use /help to see this message again"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /status command.
    Shows the current status of the user's crawled website.

    Args:
        update: The update event
        context: The context
    """
    user = update.effective_user
    user_id = str(user.id)
    logger.info(f"User {user_id} requested status")

    # Get user session
    session = db_client.get_user_session(user_id)

    if not session:
        await update.message.reply_text(
            "You haven't crawled any websites yet. Send me a URL to get started!"
        )
        return

    # Get website details
    website_id = session["website_id"]
    website = db_client.get_website(website_id)

    # Format expiry time
    expires_at = datetime.fromisoformat(website["expires_at"].replace("Z", "+00:00"))
    expires_in = expires_at - datetime.now().astimezone()
    days = expires_in.days

    # Check if the website has expired
    if days < 0:
        await update.message.reply_text(
            "⏰ Your previously crawled website data has expired.\n\n"
            "Send me a new URL to crawl it again!"
        )
        return

    # Get conversation info
    conversation = get_user_conversation(user_id)
    chat_count = len(conversation["history"]) if conversation else 0

    await update.message.reply_text(
        f"📊 Current Status:\n\n"
        f"Active Website: {website['url']}\n"
        f"Last Crawled: {website['last_crawled']}\n"
        f"Status: {website['status']}\n"
        f"Data Expires In: {days} days\n"
        f"Questions Asked: {chat_count}\n\n"
        "You can ask questions about this website or send a new URL to crawl."
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /reset command.
    Resets the user's conversation history.
    Args:
        update: The update event
        context: The context
    """
    user = update.effective_user
    user_id = str(user.id)
    logger.info(f"User {user_id} reset conversation")

    # Clear conversation history
    clear_user_conversation(user_id)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            await update.message.reply_text(
                "🔄 Conversation reset! You can continue asking about the current website "
                "or send a new URL to crawl."
            )
            break  # If successful, exit
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to send message after multiple retries: {e}")
                raise  # Re-raise the exception if all retries failed
