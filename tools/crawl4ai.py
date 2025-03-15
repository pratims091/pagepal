import gzip
import time
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import List
from urllib.parse import urlparse

import requests

from config import config
from utils.logger import crawler_logger as logger

headers = {"Authorization": f"Bearer {config.CRAWL4AI_API_TOKEN}"}


def get_sitemaps(base_url: str) -> List[str]:
    """Discover sitemap URLs from robots.txt or default locations"""
    domain = urlparse(base_url).netloc
    scheme = urlparse(base_url).scheme

    # First try robots.txt for sitemap references
    robots_url = f"{scheme}://{domain}/robots.txt"
    sitemap_urls = []

    try:
        logger.info(f"Checking robots.txt at {robots_url}")
        response = requests.get(robots_url, timeout=10)

        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    sitemap_urls.append(sitemap_url)
                    logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
    except Exception as e:
        logger.warning(f"Error retrieving robots.txt: {e}")

    # If no sitemaps found in robots.txt, try common locations
    if not sitemap_urls:
        common_sitemap_paths = [
            "/sitemap.xml",
            "/sitemap.xml.gz",
            "/sitemap_index.xml",
            "/sitemap_index.xml.gz",
            "/sitemap/sitemap.xml",
            "/sitemap/sitemap.xml.gz",
            "/sitemapindex.xml",
            "/sitemapindex.xml.gz",
        ]

        for path in common_sitemap_paths:
            sitemap_url = f"{scheme}://{domain}{path}"
            try:
                logger.info(f"Trying common sitemap location: {sitemap_url}")
                response = requests.head(sitemap_url, timeout=10)
                if response.status_code == 200:
                    sitemap_urls.append(sitemap_url)
                    logger.info(f"Found sitemap at common location: {sitemap_url}")
                    break
            except Exception as e:
                logger.warning(f"Error checking sitemap at {sitemap_url}: {e}")

    return sitemap_urls


def parse_sitemap(sitemap_url: str) -> List[str]:
    """Parse a sitemap XML file and extract URLs"""
    urls = []
    child_sitemaps = []

    try:
        logger.info(f"Parsing sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=30)

        # Handle gzipped sitemaps
        content = response.content
        if sitemap_url.endswith(".gz"):
            logger.info("Decompressing gzipped sitemap")
            content = gzip.GzipFile(fileobj=BytesIO(content)).read()

        # Parse XML
        root = ET.fromstring(content)

        # Extract namespace if present
        namespace = ""
        if "}" in root.tag:
            namespace = root.tag.split("}")[0] + "}"

        # Check if this is a sitemap index
        is_sitemap_index = False
        for child in root:
            tag = child.tag
            if namespace:
                tag = tag.replace(namespace, "")

            if tag == "sitemap":
                is_sitemap_index = True
                loc_elem = child.find(f"{namespace}loc")
                if loc_elem is not None and loc_elem.text:
                    child_sitemaps.append(loc_elem.text)
                    logger.info(f"Found child sitemap: {loc_elem.text}")

            elif tag == "url":
                loc_elem = child.find(f"{namespace}loc")
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text)

        if is_sitemap_index:
            logger.info(
                f"Sitemap is a sitemap index with {len(child_sitemaps)} child sitemaps"
            )
            # Recursively process child sitemaps
            for child_sitemap in child_sitemaps:
                child_urls = parse_sitemap(child_sitemap)
                urls.extend(child_urls)
        else:
            logger.info(f"Found {len(urls)} URLs in sitemap")

    except Exception as e:
        logger.error(f"Error parsing sitemap {sitemap_url}: {e}")

    return urls


def crawl(urls: List[str], host: str) -> str:
    """
    Sends a POST request to the crawling API with the provided URLs and returns the task ID if the response is successful.

    Args:
        urls (List[str]): A list of URLs to be crawled.

    Returns:
        str: The task ID if the response status is 200, otherwise an error message.
    """

    response = requests.post(
        f"{host}/crawl",
        headers=headers,
        json={
            "urls": urls[: config.URL_CRAWL_LIMIT],
            "priority": 1,
            "crawler_params": {
                "simulate_user": True,
                "magic": True,
                "override_navigator": True,
                "user_agent_mode": "random",
                "headers": {"Accept-Language": "en-US,en;q=0.9"},
                "verbose": True,
                "page_timeout": 60000,
                "remove_overlay_elements": True,
                "deep_crawl_strategy": {
                    "type": "best_first",
                    "max_depth": 2,
                    "url_scorer": {
                        "type": "keyword_relevance",
                        "keywords": [
                            "tutorial",
                            "guide",
                            "documentation",
                            "product",
                            "blog",
                            "article",
                        ],
                    },
                },
            },
            # Disable it for now, LLM text extraction takes time and this is out of scope for a free to use bot, I mean who will pay for the LLMs?
            # "extraction_config": {
            #     "type": "llm",
            #     "params": {
            #         "provider": "mistral/mistral-small-latest",
            #         "api_token": os.environ.get("MISTRAL_API_KEY"),
            #         "instruction": """
            #             Your task is to extract specific information from the provided Markdown content. Please identify and extract the following elements if they are present:
            #             1. **Main Page Title:** The primary title of the page.
            #             2. **Main Content:** The core textual content, such as articles, product descriptions, etc.
            #             3. **Author or Creator Name:** The name of the individual or entity that authored or created the content.
            #             4. **Publication or Last Updated Date:** The date when the content was published or last updated.
            #             5. **Main Categories or Tags:** The primary categories or tags associated with the content.
            #             6. **Key Entities Mentioned:** Notable people, organizations, products, etc., referenced in the content.
            #             7. **Meta Description:** A brief summary or description of the page's content.
            #             8. **Main Content Image Links:** URLs of the main images associated with the content.
            #             Please output the extracted information in the following JSON format:
            #             ```json
            #             {
            #               "main_page_title": "Title here",
            #               "main_content": "Content here",
            #               "author_or_creator": "Author name here",
            #               "publication_or_last_updated_date": "Date here",
            #               "main_categories_or_tags": ["Tag1", "Tag2"],
            #               "key_entities_mentioned": ["Entity1", "Entity2"],
            #               "meta_description": "Meta description here",
            #               "main_content_image_links": ["ImageURL1", "ImageURL2"]
            #             }
            #         """,
            #     }
            # },
            "extra": {"bypass_cache": True, "check_robots_txt": True},
        },
    )

    if response.status_code == 200:
        res = response.json()
        return res.get("task_id", "No task_id found in response")
    else:
        logger.error(f"Error: Received status code {response.status_code}")
        response.raise_for_status()


def crawl_website(base_url: str, host: str) -> str:
    sitemap_urls = get_sitemaps(base_url)

    start_urls = []
    if not sitemap_urls:
        logger.warning("No sitemaps found! Will start from the base URL.")
        start_urls = [base_url]
    else:
        # Parse sitemaps to get URLs
        start_urls = []
        for sitemap_url in sitemap_urls:
            urls = parse_sitemap(sitemap_url)
            start_urls.extend(urls)

        if not start_urls:
            logger.warning("No URLs found in sitemaps! Will start from the base URL.")
            start_urls = [base_url]
        else:
            logger.info(f"Found {len(start_urls)} URLs from sitemaps")
    task_id = crawl(urls=start_urls, host=host)

    return task_id


def poll_crawl_result(task_id: str, host: str, interval: int = 5):
    """
    Polls the status of a crawling task at regular intervals until it is completed or failed.

    Args:
        task_id (str): The unique identifier of the crawling task.
        host (str): The host URL where the task status can be queried.
        interval (int, optional): The time interval (in seconds) between each poll. Defaults to 5 seconds.

    Returns:
        dict: The results of the completed task if the task is successful.

    Raises:
        RuntimeError: If the task fails.
    """
    status_url = f"{host}/task/{task_id}"
    while True:
        logger.debug(f"Polling task status at {status_url}")

        response = requests.get(status_url, headers=headers)
        res = response.json()
        status = res.get("status")

        logger.debug(f"Task {task_id} status: {status}")
        if status == "completed":
            logger.info(f"Task {task_id} completed successfully")
            return res.get("results")
        elif status == "failed":
            logger.error(f"Task {task_id} failed")
            raise RuntimeError(f"Task {task_id} failed.")
        time.sleep(interval)
