"""
Analysis task orchestration for Worker service.

Runs the full Jira migration pipeline:
1. Parsing Service
2. Compatibility Service
3. Report Service
"""

import logging
import mimetypes
import os
from pathlib import Path

import requests

from worker.tasks.job_manager import mark_completed, mark_failed, mark_running

logger = logging.getLogger(__name__)

PARSING_SERVICE_URL = os.getenv("PARSING_SERVICE_URL", "http://parsing_service:5001")
COMPATIBILITY_SERVICE_URL = os.getenv(
    "COMPATIBILITY_SERVICE_URL",
    "http://compatibility_service:5002",
)
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report_service:5004")

DEFAULT_TIMEOUT = 300


def run_full_analysis_job(job_id: str, file_path: str) -> dict:
    """
    Run the full migration analysis pipeline for a given uploaded file.

    Args:
        job_id: job identifier stored in MongoDB
        file_path: local path to the uploaded ZIP/XML/dump file

    Returns:
        final result dict containing analysis_id, matrix_id and report_id
    """
    mark_running(job_id)

    try:
        logger.info("Starting full analysis job %s", job_id)

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        parse_result = _call_parsing_service(file_path)
        analysis_id = parse_result.get("analysis_id")

        if not analysis_id:
            raise ValueError("Parsing Service did not return analysis_id.")

        compatibility_result = _call_compatibility_service(analysis_id)
        matrix_id = compatibility_result.get("matrix_id")

        if not matrix_id:
            raise ValueError("Compatibility Service did not return matrix_id.")

        report_result = _call_report_service(matrix_id)
        report_id = report_result.get("report_id")

        if not report_id:
            raise ValueError("Report Service did not return report_id.")

        result = {
            "analysis_id": analysis_id,
            "matrix_id": matrix_id,
            "report_id": report_id,
            "summary": compatibility_result.get("summary", {}),
            "report": {
                "ai_used": report_result.get("ai_used", False),
                "ai_model": report_result.get("ai_model", ""),
                "title": report_result.get("title", ""),
                "summary": report_result.get("summary", ""),
            },
        }

        mark_completed(job_id, result)
        logger.info("Full analysis job %s completed successfully.", job_id)

        return result

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Full analysis job %s failed: %s", job_id, error)
        mark_failed(job_id, str(error))
        return {
            "job_id": job_id,
            "status": "FAILED",
            "error": str(error),
        }


def _call_parsing_service(file_path: str) -> dict:
    """Call Parsing Service /parse endpoint."""
    url = f"{PARSING_SERVICE_URL.rstrip('/')}/parse"
    logger.info("Calling Parsing Service: %s", url)

    # Déterminer le type MIME
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    with open(file_path, "rb") as file:
        files = {
            "file": (os.path.basename(file_path), file, mime_type)
        }
        response = requests.post(url, files=files, timeout=(10, DEFAULT_TIMEOUT))

    if response.status_code != 200:
        logger.error("Parsing failed (%s): %s", response.status_code, response.text)

    response.raise_for_status()
    return response.json()


def _call_compatibility_service(analysis_id: str) -> dict:
    """Call Compatibility Service /compatibility/analyze endpoint."""
    url = f"{COMPATIBILITY_SERVICE_URL.rstrip('/')}/compatibility/analyze"

    logger.info("Calling Compatibility Service for analysis_id=%s", analysis_id)

    response = requests.post(
        url,
        json={"analysis_id": analysis_id},
        timeout=(10, DEFAULT_TIMEOUT),
    )

    response.raise_for_status()
    return response.json()


def _call_report_service(matrix_id: str) -> dict:
    """Call Report Service /reports/generate endpoint."""
    url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports/generate"

    logger.info("Calling Report Service for matrix_id=%s", matrix_id)

    response = requests.post(
        url,
        json={"matrix_id": matrix_id},
        timeout=(10, DEFAULT_TIMEOUT),
    )

    response.raise_for_status()
    return response.json()
