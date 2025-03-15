"""
LangChain chains for PagePal application.
Provides conversational RAG chains.
"""

from typing import Any, Callable, Dict, List

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableLambda

from rag.llm import get_llm_model
from rag.prompts import get_qa_prompt
from utils.logger import rag_logger as logger


def format_chat_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Convert history from {human/system} format to {role/content} format.

    Args:
        history: List of message dictionaries with 'human' or 'system' keys

    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    formatted_history = []
    for message in history:
        if "human" in message:
            formatted_history.append({"role": "user", "content": message["human"]})
        elif "system" in message:
            formatted_history.append(
                {"role": "assistant", "content": message["system"]}
            )
    return formatted_history


def create_qa_chain(retriever: BaseRetriever, **kwargs) -> Any:
    """
    Create a QA chain with the retriever.

    Args:
        retriever: The retriever component
        **kwargs: Additional kwargs for the chain

    Returns:
        Any: The QA chain
    """
    try:
        # Get LLM and prompt
        llm = get_llm_model()
        qa_prompt = get_qa_prompt()

        # Create the document chain
        document_chain = create_stuff_documents_chain(llm, qa_prompt)

        # Create the retrieval chain
        qa_chain = create_retrieval_chain(retriever, document_chain)

        # Add a post-processing step to include source documents
        def add_source_documents(inputs):
            # Get retrieved documents from inputs
            source_documents = inputs.get("context", [])
            # Get the result from the chain
            result = inputs.get("answer", "")
            # Return both
            return {"answer": result, "source_documents": source_documents}

        # Chain with source documents included
        qa_chain_with_sources = qa_chain | RunnableLambda(add_source_documents)

        logger.info("Created QA chain")
        return qa_chain_with_sources
    except Exception as e:
        logger.error(f"Failed to create QA chain: {e}")
        raise


def create_streaming_qa_chain(retriever: BaseRetriever, **kwargs) -> Any:
    """
    Create a streaming QA chain with the retriever.

    Args:
        retriever: The retriever component
        **kwargs: Additional kwargs for the chain

    Returns:
        Any: The streaming QA chain
    """
    try:
        # Get LLM and prompt (with streaming enabled)
        llm = get_llm_model(streaming=True)
        qa_prompt = get_qa_prompt()

        # Create the document chain
        document_chain = create_stuff_documents_chain(
            llm,
            qa_prompt,
            document_variable_name="context",
        )

        # Create the retrieval chain
        qa_chain = create_retrieval_chain(retriever, document_chain)

        # Add a post-processing step to include source documents
        def add_source_documents(inputs):
            # Get retrieved documents from inputs
            source_documents = inputs.get("context", [])
            # Get the result from the chain
            result = inputs.get("answer", "")
            # Return both
            return {"answer": result, "source_documents": source_documents}

        # Chain with source documents included
        qa_chain_with_sources = qa_chain | RunnableLambda(add_source_documents)

        logger.info("Created streaming QA chain")
        return qa_chain_with_sources
    except Exception as e:
        logger.error(f"Failed to create streaming QA chain: {e}")
        raise


async def run_qa_chain(
    chain: Any, question: str, history: List[Dict[str, str]], **kwargs
) -> Dict[str, Any]:
    """
    Run the QA chain with the question and history.

    Args:
        chain: The QA chain
        question: The user question
        history: List of (question, answer) tuples
        **kwargs: Additional kwargs for the chain

    Returns:
        Dict[str, Any]: The chain result
    """
    try:
        # Prepare the input for the chain
        formatted_history = format_chat_history(history)

        chain_input = {
            "input": question,
            "chat_history": formatted_history,
        }

        # Run the chain
        result = chain.invoke(chain_input)

        logger.info(f"Ran QA chain for question: {question}")
        return result
    except Exception as e:
        logger.error(f"Failed to run QA chain: {e}")
        raise


async def stream_qa_chain(
    chain: Any,
    question: str,
    history: List[Dict[str, Any]],
    token_callback: Callable[[str], None],
    **kwargs,
) -> Dict[str, Any]:
    """
    Stream the QA chain with the question and history.

    Args:
        chain: The streaming QA chain
        question: The user question
        history: List of (question, answer) tuples
        token_callback: Callback function for streamed tokens
        **kwargs: Additional kwargs for the chain

    Returns:
        Dict[str, Any]: The chain result
    """
    try:
        # Prepare the input for the chain
        formatted_history = format_chat_history(history)

        chain_input = {
            "input": question,
            "chat_history": formatted_history,
        }

        # Full response accumulator
        full_response = ""
        source_documents = []

        # Process streaming response
        async for chunk in chain.astream(chain_input):
            if "answer" in chunk:
                token = chunk["answer"]
                full_response += token
                await token_callback(token)

            # For streaming, source documents usually come at the end
            if "source_documents" in chunk and chunk["source_documents"]:
                source_documents = chunk["source_documents"]

        # Return the full result
        result = {"answer": full_response, "source_documents": source_documents}

        logger.info(f"Streamed QA chain for question: {question}")
        return result
    except Exception as e:
        logger.error(f"Failed to stream QA chain: {e}")
        raise
