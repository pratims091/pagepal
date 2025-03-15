"""
Vector store operations for PagePal application.
Manages document embeddings and vector search.
"""

from pathlib import Path
from typing import Any, List, Optional

from langchain.schema import Document
from langchain.vectorstores.base import VectorStore
from langchain_chroma import Chroma

from config import config
from rag.embeddings import get_embedding_model
from utils.logger import db_logger as logger


class VectorStoreManager:
    """Manager for vector store operations."""

    def __init__(self):
        """Initialize the vector store manager."""
        self.persist_directory = Path(config.PERSIST_DIRECTORY)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.embedding_model = get_embedding_model()

    def create_vector_store(
        self, documents: List[Document], vector_store_id: str
    ) -> VectorStore:
        """
        Create a new vector store for documents.

        Args:
            documents: List of documents to add to the vector store
            vector_store_id: ID for the vector store

        Returns:
            VectorStore: The created vector store
        """
        try:
            persist_directory = self.persist_directory / vector_store_id

            # Create vector store
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_model,
                persist_directory=str(persist_directory),
            )

            logger.info(
                f"Created vector store: {vector_store_id} with {len(documents)} documents"
            )
            return vectorstore
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    def load_vector_store(self, vector_store_id: str) -> Optional[VectorStore]:
        """
        Load an existing vector store.

        Args:
            vector_store_id: ID of the vector store to load

        Returns:
            Optional[VectorStore]: The loaded vector store, or None if not found
        """
        try:
            persist_directory = self.persist_directory / vector_store_id

            if not persist_directory.exists():
                logger.warning(f"Vector store directory not found: {persist_directory}")
                return None

            # Load vector store
            vectorstore = Chroma(
                persist_directory=str(persist_directory),
                embedding_function=self.embedding_model,
            )

            logger.info(f"Loaded vector store: {vector_store_id}")
            return vectorstore
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            raise

    def get_retriever(self, vector_store_id: str, **kwargs) -> Any:
        """
        Get a retriever for the vector store.

        Args:
            vector_store_id: ID of the vector store
            **kwargs: Additional kwargs for the retriever

        Returns:
            Any: The retriever
        """
        try:
            vectorstore = self.load_vector_store(vector_store_id)

            if not vectorstore:
                raise ValueError(f"Vector store not found: {vector_store_id}")

            # Default search parameters
            search_kwargs = kwargs.get("search_kwargs", {"k": 5})

            # Create retriever
            retriever = vectorstore.as_retriever(
                search_type="similarity", search_kwargs=search_kwargs
            )

            logger.info(f"Created retriever for vector store: {vector_store_id}")
            return retriever
        except Exception as e:
            logger.error(f"Failed to get retriever: {e}")
            raise

    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete a vector store.

        Args:
            vector_store_id: ID of the vector store to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            persist_directory = self.persist_directory / vector_store_id

            if not persist_directory.exists():
                logger.warning(f"Vector store directory not found: {persist_directory}")
                return False

            # Delete vector store directory
            for file in persist_directory.glob("*"):
                file.unlink()
            persist_directory.rmdir()

            logger.info(f"Deleted vector store: {vector_store_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector store: {e}")
            return False


# Create a singleton instance for easy importing
vector_store_manager = VectorStoreManager()
