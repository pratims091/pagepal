"""
Supabase client for PagePal application.
Handles database connections and operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from supabase import Client, create_client

from config import config
from utils.logger import db_logger as logger


class SupabaseClient:
    """Supabase client for database operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Optional[Client] = None
        self.initialize()

    def initialize(self) -> None:
        """Initialize the Supabase client with configuration settings."""
        try:
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def save_crawled_website(self, url: str, vector_store_id: str) -> str:
        """
        Save crawled website info to database.

        Args:
            url: The website URL
            vector_store_id: ID of the vector store

        Returns:
            str: The ID of the created website record
        """
        try:
            now = datetime.now().isoformat()
            expires_at = (
                datetime.now() + timedelta(days=config.CACHE_EXPIRY_DAYS)
            ).isoformat()

            result = (
                self.client.table("pagepal_crawled_websites")
                .insert(
                    {
                        "url": url,
                        "last_crawled": now,
                        "vector_store_id": vector_store_id,
                        "status": "completed",
                        "expires_at": expires_at,
                    }
                )
                .execute()
            )

            website_id = result.data[0]["id"]
            logger.info(f"Saved crawled website with ID: {website_id}")
            return website_id
        except Exception as e:
            logger.error(f"Failed to save crawled website: {e}")
            raise

    def get_website(self, website_id: str) -> Dict[str, Any]:
        """
        Get website info by ID.

        Args:
            website_id: The website ID

        Returns:
            Dict[str, Any]: Website information
        """
        try:
            result = (
                self.client.table("pagepal_crawled_websites")
                .select("*")
                .eq("id", website_id)
                .execute()
            )

            if not result.data:
                raise ValueError(f"Website with ID {website_id} not found")

            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get website: {e}")
            raise

    def get_website_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get website info by URL.

        Args:
            url: The website URL

        Returns:
            Optional[Dict[str, Any]]: Website information if found, None otherwise
        """
        try:
            result = (
                self.client.table("pagepal_crawled_websites")
                .select("*")
                .eq("url", url)
                .execute()
            )

            if not result.data:
                return None

            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to get website by URL: {e}")
            raise

    def update_user_session(self, user_id: str, website_id: str) -> str:
        """
        Update or create user session.

        Args:
            user_id: The user ID
            website_id: The website ID

        Returns:
            str: The session ID
        """
        try:
            now = datetime.now().isoformat()

            # Check if session exists
            result = (
                self.client.table("pagepal_user_sessions")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                # Update existing session
                session_id = result.data[0]["id"]
                self.client.table("pagepal_user_sessions").update(
                    {"website_id": website_id, "last_activity": now}
                ).eq("id", session_id).execute()

                logger.info(f"Updated user session: {session_id}")
                return session_id
            else:
                # Create new session
                result = (
                    self.client.table("pagepal_user_sessions")
                    .insert(
                        {
                            "user_id": user_id,
                            "website_id": website_id,
                            "created_at": now,
                            "last_activity": now,
                        }
                    )
                    .execute()
                )

                session_id = result.data[0]["id"]
                logger.info(f"Created user session: {session_id}")
                return session_id
        except Exception as e:
            logger.error(f"Failed to update user session: {e}")
            raise

    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session info.

        Args:
            user_id: The user ID

        Returns:
            Optional[Dict[str, Any]]: Session information if found, None otherwise
        """
        try:
            result = (
                self.client.table("pagepal_user_sessions")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data:
                return None

            # Get the most recent session
            return sorted(result.data, key=lambda x: x["last_activity"], reverse=True)[
                0
            ]
        except Exception as e:
            logger.error(f"Failed to get user session: {e}")
            raise


# Create a singleton instance for easy importing
db_client = SupabaseClient()
