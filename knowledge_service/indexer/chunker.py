"""
Chunker for the Knowledge Service.
Splits markdown documentation files into smaller overlapping chunks
ready for embedding and storage in ChromaDB.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 500      # max characters per chunk
DEFAULT_CHUNK_OVERLAP = 50    # overlap between consecutive chunks


def load_markdown_file(file_path: str) -> str:
    """Read a markdown file and return its content as a string."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Failed to read file %s: %s", file_path, e)
        return ""


def split_by_sections(content: str) -> list[str]:
    """
    Split markdown content by headers (## or ###).
    Each section becomes a logical unit before further chunking.
    """
    # Split on markdown headers
    sections = re.split(r"\n(?=#{1,3} )", content)
    return [s.strip() for s in sections if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split a text into overlapping chunks of max chunk_size characters.

    Args:
        text: the text to split
        chunk_size: maximum number of characters per chunk
        overlap: number of characters to overlap between chunks

    Returns:
        list of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            break_point = max(last_period, last_newline)

            if break_point > start:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def chunk_document(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict]:
    """
    Load a markdown file and return a list of chunks with metadata.

    Args:
        file_path: absolute path to the .md file
        chunk_size: max characters per chunk
        overlap: overlap between chunks

    Returns:
        list of dicts with keys: text, source, chunk_index
    """
    filename = os.path.basename(file_path)
    content = load_markdown_file(file_path)

    if not content:
        logger.warning("Empty or unreadable file: %s", filename)
        return []

    # First split by markdown sections, then chunk each section
    sections = split_by_sections(content)
    all_chunks = []
    chunk_index = 0

    for section in sections:
        section_chunks = chunk_text(section, chunk_size, overlap)
        for chunk in section_chunks:
            all_chunks.append({
                "text": chunk,
                "source": filename,
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    logger.info(
        "Chunked '%s' into %d chunks (%d sections).",
        filename, len(all_chunks), len(sections)
    )

    return all_chunks


def chunk_all_documents(docs_dir: str) -> list[dict]:
    """
    Load and chunk all .md files in a directory.

    Args:
        docs_dir: path to the docs/ folder

    Returns:
        list of all chunks from all documents
    """
    all_chunks = []

    if not os.path.exists(docs_dir):
        logger.error("Docs directory not found: %s", docs_dir)
        return []

    md_files = [
        os.path.join(docs_dir, f)
        for f in os.listdir(docs_dir)
        if f.endswith(".md")
    ]

    if not md_files:
        logger.warning("No .md files found in %s", docs_dir)
        return []

    for file_path in md_files:
        chunks = chunk_document(file_path)
        all_chunks.extend(chunks)

    logger.info(
        "Total chunks from %d documents: %d",
        len(md_files), len(all_chunks)
    )

    return all_chunks
