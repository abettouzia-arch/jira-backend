"""
Worker Service for Jira Migration backend.

Provides endpoints to run and monitor full analysis jobs.
"""

import logging
import os
import sys
import tempfile
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
    Run full analysis job.

    Expects multipart/form-data:
      file=<zip/xml/json/sql>
    """
    if "file" not in request.files:
        return jsonify({"error": "File is required."}), 400

    uploaded_file = request.files["file"]

    if not uploaded_file.filename:
        return jsonify({"error": "Uploaded file must have a filename."}), 400

    job = create_job(
        job_type="FULL_ANALYSIS",
        payload={
            "filename": uploaded_file.filename,
        },
    )

    try:
        suffix = Path(uploaded_file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=UPLOAD_DIR,
        )

        uploaded_file.save(temp_file.name)
        temp_file.close()

        logger.info(
            "Saved uploaded file for job %s to %s",
            job["job_id"],
            temp_file.name,
        )

        result = run_full_analysis_job(job["job_id"], temp_file.name)

        return jsonify({
            "job_id": job["job_id"],
            "status": "COMPLETED" if "report_id" in result else "FAILED",
            "result": result,
        }), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Worker job execution failed: %s", error)
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
