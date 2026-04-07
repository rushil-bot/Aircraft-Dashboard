"""
Data ingestion script for the Phase 4 NL Query Agent.
Downloads public domain FAA documents, processes them into semantic chunks,
and stores their embeddings in the Chroma vector database.
"""

# pylint: disable=import-error

import os
import argparse
import tempfile
import logging
import requests

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import chromadb

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s"
)
logger = logging.getLogger(__name__)

# A reliable, public domain FAA document (Advisory Circular for Aviation Weather)
# You can override this via command line arguments.
DEFAULT_URL = "https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_00-6B.pdf"

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))


def ingest_pdf(url: str):
    """
    Downloads and ingests an FAA document PDF into ChromaDB.
    """
    logger.info(
        "Initializing vector DB connection to %s:%d...", CHROMA_HOST, CHROMA_PORT
    )
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vectorstore = Chroma(
        client=chroma_client,
        collection_name="aviation_knowledge",
        embedding_function=embeddings,
    )

    logger.info("Downloading FAA Document from: %s", url)
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Failed to download the document: %s", e)
        return

    # Use a temporary file to save the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        for chunk in response.iter_content(chunk_size=8192):
            temp_pdf.write(chunk)
        temp_pdf_path = temp_pdf.name

    logger.info("Parsing PDF...")
    try:
        loader = PyPDFLoader(temp_pdf_path)
        documents = loader.load()
        logger.info("Successfully extracted %d pages.", len(documents))

        logger.info("Splitting text into semantically meaningful chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500, chunk_overlap=300, separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        logger.info("Created %d chunks.", len(chunks))

        logger.info("Embedding and inserting chunks into ChromaDB...")
        vectorstore.add_documents(chunks)

        logger.info("[SUCCESS] Database populated with %d vectors.", len(chunks))

    finally:
        # Cleanup temporary file
        os.remove(temp_pdf_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest FAA PDF into ChromaDB.")
    parser.add_argument(
        "--url", type=str, default=DEFAULT_URL, help="URL of the PDF to ingest."
    )
    args = parser.parse_args()

    ingest_pdf(args.url)
