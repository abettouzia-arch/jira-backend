"""
Embedder for the Knowledge Service.
Converts text chunks into vector embeddings using sentence-transformers.
Embeddings are used by ChromaDB for semantic similarity search.
"""

import logging

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model used for embeddings — lightweight and fast
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Singleton model instance
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the sentence-transformers model.
    Downloaded once on first call, reused afterwards.
    """
    global _model  # pylint: disable=global-statement
    if _model is None:
        logger.info("Loading embedding model '%s'...", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into embedding vectors.

    Args:
        texts: list of text strings to embed

    Returns:
        list of embedding vectors (each vector is a list of floats)
    """
    if not texts:
        return []

    model = get_embedding_model()

    logger.info("Embedding %d texts...", len(texts))
    embeddings = model.encode(texts, show_progress_bar=False)
    logger.info("Embedding complete.")

    return embeddings.tolist()


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add embedding vectors to a list of chunk dicts.

    Args:
        chunks: list of dicts with at least a 'text' key

    Returns:
        same list with 'embedding' key added to each chunk
    """
    if not chunks:
        return []

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(texts)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks
