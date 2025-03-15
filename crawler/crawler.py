"""
Web crawler integration for PagePal application.
Handles web crawling with crawler4ai.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from config import config

# Your crawler4ai package - these are placeholders that should match your actual crawler4ai imports
from tools.crawl4ai import crawl, poll_crawl_result
from utils.logger import crawler_logger as logger


async def crawl_url(url: str, timeout: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Crawl a URL and get the results.

    Args:
        url: The URL to crawl
        timeout: Timeout in seconds (optional)

    Returns:
        List[Dict[str, Any]]: The crawl results
    """
    if timeout is None:
        timeout = config.CRAWL_TIMEOUT

    try:
        logger.info(f"Starting crawl for URL: {url}")

        # Set the API token in environment
        os.environ["CRAWL4AI_API_TOKEN"] = config.CRAWL4AI_API_TOKEN

        # Configure the crawler to use the Docker container endpoint
        # Note: When running within Docker, we use the service name
        # When running locally outside Docker, we use localhost
        crawler_host = config.CRAWL4AI_HOST

        # Initiate crawling
        task_id = crawl(urls=[url], host=crawler_host)
        logger.info(f"Crawling initiated with task ID: {task_id}")

        # Define async timeout
        async def wait_for_results():
            # Poll for results
            return poll_crawl_result(task_id, host=crawler_host, interval=5)

        # Run with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.create_task(wait_for_results()), timeout=timeout
            )

            logger.info(
                f"Crawling completed for URL: {url}, got {len(results)} results"
            )
            return results
        except asyncio.TimeoutError:
            logger.error(f"Crawling timed out after {timeout} seconds")
            raise TimeoutError(f"Crawling timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"Error during crawling: {str(e)}")
        raise
