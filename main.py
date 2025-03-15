"""
Main entry point for PagePal application.
Starts the Telegram bot and initializes components.
"""

import sys

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.commands import help_command, reset_command, start_command, status_command
from bot.handlers import handle_message
from config import config
from utils.logger import app_logger as logger


def validate_config() -> bool:
    """
    Validate application configuration.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    error = config.validate()
    if error:
        logger.error(f"Configuration error: {error}")
        return False

    logger.info("Configuration validated successfully")
    return True


def setup_application() -> Application:
    """
    Set up the Telegram bot application.

    Returns:
        Application: The configured application
    """
    logger.info("Setting up application")

    # Create application
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("reset", reset_command))

    # Add message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Application set up successfully")
    return application


def main() -> None:
    """Run the bot."""
    logger.info("Starting PagePal application")

    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Exiting.")
        sys.exit(1)

    try:
        # Setup application
        application = setup_application()

        # Start the Bot
        logger.info("Starting bot polling")
        application.run_polling()
    except Exception as e:
        logger.error(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
