"""
ZIP handler for Jira Migration parsing service.
Extracts and routes files from uploaded ZIP archives
to the appropriate parser based on file type.
"""

import logging
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger(__name__)

# Supported file extensions and their target parser
SUPPORTED_EXTENSIONS = {
    ".xml":    "xml",
    ".groovy": "groovy",
    ".sql":    "dump",
    ".json":   "dump",
}

# Files and folders to always ignore
IGNORED_PATTERNS = {
    "__MACOSX",
    ".DS_Store",
    "Thumbs.db",
    ".gitignore",
    ".git",
}


def is_ignored(path: str) -> bool:
    """Check if a file or folder should be ignored."""
    parts = Path(path).parts
    return any(ignored in parts for ignored in IGNORED_PATTERNS)


def detect_file_type(filename: str) -> str | None:
    """
    Detect the parser type based on file extension.
    Returns 'xml', 'groovy', 'dump', or None if unsupported.
    """
    ext = Path(filename).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, None)


def extract_zip(zip_path: str) -> tuple[str, list[dict]]:
    """
    Extract ZIP archive to a temporary directory.

    Returns:
        extract_dir: path to the temporary extraction folder
        file_list:   list of dicts with file metadata
    """
    extract_dir = tempfile.mkdtemp(prefix="jira_migration_")
    file_list = []

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            members = z.namelist()
            if not members:
                raise ValueError("ZIP archive is empty.")

            z.extractall(extract_dir)

            for member in members:
                if member.endswith("/") or is_ignored(member):
                    continue

                full_path = os.path.join(extract_dir, member)
                file_type = detect_file_type(member)

                file_list.append({
                    "filename":  member,
                    "full_path": full_path,
                    "file_type": file_type,
                    "size_kb":   round(os.path.getsize(full_path) / 1024, 2)
                })

        logger.info("Extracted %d files from ZIP.", len(file_list))
        return extract_dir, file_list

    except zipfile.BadZipFile as exc:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise ValueError("Invalid or corrupted ZIP file.") from exc

    except Exception as exc:
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to extract ZIP: {exc}") from exc


def route_files(file_list: list[dict]) -> dict[str, list[dict]]:
    """
    Group files by their parser type.

    Returns a dict like:
    {
        "xml":     [...],
        "groovy":  [...],
        "dump":    [...],
        "unknown": []
    }
    """
    routed = {
        "xml":     [],
        "groovy":  [],
        "dump":    [],
        "unknown": []
    }

    for file in file_list:
        file_type = file["file_type"]
        if file_type in routed:
            routed[file_type].append(file)
        else:
            routed["unknown"].append(file)
            logger.warning("Unsupported file type: %s", file["filename"])

    return routed


def extract_and_route(zip_path: str) -> tuple[str, dict[str, list[dict]]]:
    """
    Main entry point for the ZIP handler.
    Extracts the ZIP and returns routed files grouped by parser type.

    Args:
        zip_path: absolute path to the uploaded ZIP file

    Returns:
        extract_dir: temp folder path (caller must clean up with cleanup())
        routed:      dict of files grouped by parser type
    """
    extract_dir, file_list = extract_zip(zip_path)
    routed = route_files(file_list)

    logger.info(
        "Routing summary — xml: %d | groovy: %d | dump: %d | unknown: %d",
        len(routed["xml"]),
        len(routed["groovy"]),
        len(routed["dump"]),
        len(routed["unknown"])
    )

    return extract_dir, routed


def cleanup(extract_dir: str) -> None:
    """
    Delete the temporary extraction directory.
    Must be called after parsing is complete.
    """
    if extract_dir and os.path.exists(extract_dir):
        shutil.rmtree(extract_dir, ignore_errors=True)
        logger.info("Cleaned up temp dir: %s", extract_dir)
