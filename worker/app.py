"""
Worker Service for Jira Migration backend.

Provides endpoints to run and monitor full analysis jobs.
"""

import logging
import os
import sys
import tempfile
import threading
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from worker.tasks.analysis_task import run_full_analysis_job
from worker.tasks.job_manager import create_job, get_job, list_jobs

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("WORKER_UPLOAD_DIR", "/tmp/jira_migration_worker_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "worker"}), 200


@app.route("/worker/jobs/run", methods=["POST"])
def run_job():
    """
    Run full analysis job asynchronously.
    Expects multipart/form-data: file=<zip/xml/json/sql>
    """
    if "file" not in request.files:
        logger.error("Worker received request without file part")
        return jsonify({"error": "File is required."}), 400

    uploaded_file = request.files["file"]
    logger.info(
        "Worker received file upload: file_in_request=%s filename=%s content_type=%s",
        "file" in request.files,
        uploaded_file.filename,
        uploaded_file.content_type,
    )

    if not uploaded_file.filename:
        logger.error("Worker received file without filename")
        return jsonify({"error": "Uploaded file must have a filename."}), 400

    # On crée le job en base de données tout de suite
    job = create_job(
        job_type="FULL_ANALYSIS",
        payload={
            "filename": uploaded_file.filename,
        },
    )

    try:
        # Préparation du fichier temporaire
        suffix = Path(uploaded_file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIR,
        )

        uploaded_file.save(temp_file.name)
        temp_file.close()
        file_size = os.path.getsize(temp_file.name)

        logger.info(
            "Saved uploaded file for job %s to %s (size=%s bytes). Starting background task.",
            job["job_id"],
            temp_file.name,
            file_size,
        )

        # --- CHANGEMENT ICI : LANCEMENT DU THREAD ---
        # On lance run_full_analysis_job dans un fil d'exécution séparé
        analysis_thread = threading.Thread(
            target=run_full_analysis_job,
            args=(job["job_id"], temp_file.name)
        )
        analysis_thread.start()

        # On répond IMMÉDIATEMENT au client (Gateway/Nginx)
        # On utilise le code HTTP 202 (Accepted) pour dire que c'est en cours
        return jsonify({
            "job_id": job["job_id"],
            "status": "STARTED",
            "message": "Analysis job started in background.",
            "check_status_url": f"/api/worker/jobs/{job['job_id']}"
        }), 202

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Worker failed to initiate job %s: %s", job["job_id"], error)
        return jsonify({
            "job_id": job["job_id"],
            "status": "FAILED",
            "error": str(error),
        }), 500


@app.route("/worker/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Retrieve job status."""
    job = get_job(job_id)

    if not job:
        return jsonify({"error": f"Job '{job_id}' not found."}), 404

    return jsonify(job), 200


@app.route("/worker/jobs", methods=["GET"])
def get_jobs():
    """List recent jobs."""
    limit = request.args.get("limit", 50, type=int)
    jobs = list_jobs(limit=limit)

    return jsonify({
        "jobs": jobs,
        "count": len(jobs),
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=True)
