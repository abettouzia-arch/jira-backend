"""
Document Loader for the Knowledge Service.
Orchestrates the full indexing pipeline:
  docs/*.md → chunker → embedder → ChromaDB
"""

import logging
import os
import sys
from functools import lru_cache

import chromadb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from knowledge_service.indexer.chunker import chunk_all_documents
from knowledge_service.indexer.embedder import embed_chunks

logger = logging.getLogger(__name__)

COLLECTION_NAME = "jira_migration_docs"

DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
)

CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chroma_db",
)


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """Create and cache the ChromaDB persistent client."""
    logger.info("Initializing ChromaDB at %s", CHROMA_PATH)
    return chromadb.PersistentClient(path=CHROMA_PATH)


@lru_cache(maxsize=1)
def get_chroma_collection():
    """
    Initialize and return the ChromaDB collection.
    Creates it if it doesn't exist.
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info(
        "ChromaDB collection '%s' ready (%d documents).",
        COLLECTION_NAME,
        collection.count(),
    )

    return collection


def index_documents(force_reindex: bool = False) -> int:
    """
    Index all documents from docs/ into ChromaDB.

    Args:
        force_reindex: if True, clears existing collection before indexing

    Returns:
        number of chunks indexed
    """
    collection = get_chroma_collection()

    if collection.count() > 0 and not force_reindex:
        logger.info(
            "Collection already contains %d chunks. Skipping indexing.",
            collection.count(),
        )
        return collection.count()

    if force_reindex and collection.count() > 0:
        logger.info("Force reindex — clearing existing collection.")
        client = get_chroma_client()
        client.delete_collection(COLLECTION_NAME)
        get_chroma_collection.cache_clear()
        collection = get_chroma_collection()

    logger.info("Loading and chunking documents from %s", DOCS_DIR)
    chunks = chunk_all_documents(DOCS_DIR)

    if not chunks:
        logger.warning("No chunks to index.")
        return 0

    logger.info("Embedding %d chunks...", len(chunks))
    chunks = embed_chunks(chunks)

    ids = [f"{chunk['source']}__chunk_{chunk['chunk_index']}" for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    metadatas = [
        {"source": chunk["source"], "chunk_index": chunk["chunk_index"]}
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info("Indexed %d chunks into ChromaDB.", len(chunks))
    return len(chunks)


def get_collection_stats() -> dict:
    """Return basic stats about the ChromaDB collection."""
    collection = get_chroma_collection()
    return {
        "collection_name": COLLECTION_NAME,
        "total_chunks": collection.count(),
        "docs_dir": DOCS_DIR,
        "chroma_path": CHROMA_PATH,
    }
