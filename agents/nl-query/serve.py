"""
Natural Language Query Agent Service.
Provides a conversational interface powered by Retrieval-Augmented Generation (RAG).
Executes local queries against an Ollama instance, augmented by context from ChromaDB.
"""

# pylint: disable=import-error,duplicate-code
import os
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# Configure logging strictly for professional monitoring
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger("nl-query")

app = FastAPI(
    title="Aircraft Dashboard - NL Query Service",
    description="Microservice providing RAG capabilities for aviation data.",
    version="1.0.0",
)

# Environment configuration
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", 11434))
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Global singletons for persistence across requests
vectorstore = None  # pylint: disable=invalid-name


@app.on_event("startup")
async def startup_event():
    """Initialize remote connections on server startup."""
    global vectorstore  # pylint: disable=global-statement
    logger.info("Connecting to ChromaDB at %s:%d", CHROMA_HOST, CHROMA_PORT)
    try:
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(
            client=chroma_client,
            collection_name="aviation_knowledge",
            embedding_function=embeddings,
        )
        logger.info("[PASS] Connected to ChromaDB successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to initialize ChromaDB connection: %s", e)


class QueryRequest(BaseModel):
    """Data model representing an incoming query."""

    query: str
    model: str = "llama3"


# Template enforcing strict grounding in the provided context
RAG_TEMPLATE = """You are a highly professional aviation data assistant.
Use the following pieces of retrieved context from official FAA and aviation documents to answer the question.
If the information is not present in the context, state that the data is not available. Do not infer answers absent from context.

Context:
{context}

Question:
{question}

Answer:"""

prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template=RAG_TEMPLATE,
)


async def generate_response_stream(
    query: str, target_model: str
) -> AsyncGenerator[str, None]:
    """Generates a streaming text response using RAG."""
    if vectorstore is None:
        yield "Error: Database connection is unavailable.\n"
        return

    # 1. Retrieve context
    docs = vectorstore.similarity_search(query, k=3)
    context_text = "\n\n".join([doc.page_content for doc in docs])

    logger.info("Retrieved %d context chunks for query: '%s'", len(docs), query)

    # 2. Format localized LLM invocation
    llm = OllamaLLM(model=target_model, base_url=OLLAMA_URL)
    chain = prompt_template | llm

    # 3. Stream data from the LLM via LangChain
    try:
        for chunk in chain.stream({"context": context_text, "question": query}):
            yield chunk
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("LLM Generation failure: %s", e)
        yield f"\n[System Error: Failed to execute {target_model} generation]"


@app.post("/ask")
async def ask_question(request: QueryRequest):
    """
    Receives a natural language question, retrieves context, and streams
    the generated answer via Server-Sent responses.
    """
    logger.info("Received query leveraging model: %s", request.model)
    return StreamingResponse(
        generate_response_stream(request.query, request.model),
        media_type="text/event-stream",
    )
