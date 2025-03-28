"""
Content processing for PagePal application.
Processes crawled content into documents.
"""

from typing import Any, Dict, List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language

from utils.logger import crawler_logger as logger


def process_crawl_results(
    results: List[Dict[str, Any]], base_url: str
) -> List[Document]:
    """
    Process crawl results into documents.

    Args:
        results: List of crawl results
        base_url: The base URL of the website

    Returns:
        List[Document]: List of processed documents
    """
    try:
        documents = []

        for result in results:
            if not result.get("success", False):
                logger.warning(
                    f"Skipping failed result for URL: {result.get('url', 'unknown')}"
                )
                continue

            # Get the URL and content
            page_url = result.get("url", "")
            content = result.get("markdown", "") 

            if not content:
                logger.warning(f"Skipping empty content for URL: {page_url}")
                continue

            # Create document with metadata
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": page_url,
                        "base_url": base_url,
                        "title": result.get("title", ""),
                        "last_crawled": result.get("timestamp", ""),
                    },
                )
            )

        logger.info(f"Processed {len(documents)} documents from crawl results")
        return documents
    except Exception as e:
        logger.error(f"Failed to process crawl results: {e}")
        raise


def chunk_documents(documents: List[Document], **kwargs) -> List[Document]:
    """
    Chunk documents into smaller pieces.

    Args:
        documents: List of documents to chunk
        **kwargs: Additional kwargs for the text splitter

    Returns:
        List[Document]: List of chunked documents
    """
    try:
        # Default chunk settings
        chunk_size = kwargs.get("chunk_size", 1500)
        chunk_overlap = kwargs.get("chunk_overlap", 150)
        separators = kwargs.get("separators", ["\n\n", "\n", ". ", " ", ""])

        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )

        # Split documents
        chunked_documents = text_splitter.split_documents(documents)

        logger.info(
            f"Chunked {len(documents)} documents into {len(chunked_documents)} chunks"
        )
        return chunked_documents
    except Exception as e:
        logger.error(f"Failed to chunk documents: {e}")
        raise
