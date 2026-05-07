"""Repository implementation for job documents."""

from shared.db.mongo_client import get_mongo_db


class JobRepository:
    """Repository for the 'jobs' collection."""

    def __init__(self, db=None):
        self.db = db or get_mongo_db()
        self.collection = self.db.jobs

    def insert_job(self, job_data: dict) -> str:
        """
        Insert a new job record into the database.

        Args:
            job_data: Dictionary containing job details (job_id, status, etc.)

        Returns:
            The inserted document's ID as a string.
        """
        result = self.collection.insert_one(job_data)
        return str(result.inserted_id)

    def update_job_status(self, job_id: str, updates: dict) -> bool:
        """
        Update a job's status and related fields.

        Args:
            job_id: The unique identifier for the job.
            updates: Dictionary of fields to update (e.g., {"status": "RUNNING"}).

        Returns:
            True if a document was updated, False otherwise.
        """
        result = self.collection.update_one({"job_id": job_id}, {"$set": updates})
        return result.modified_count > 0

    def get_job_by_id(self, job_id: str) -> dict | None:
        """
        Retrieve a job record by its job_id.

        Args:
            job_id: The unique identifier for the job.

        Returns:
            The job document if found, otherwise None.
        """
        return self.collection.find_one({"job_id": job_id})

    def list_jobs(self, limit: int = 50) -> list[dict]:
        """
        Retrieve a list of recent job records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of job documents.
        """
        return list(self.collection.find().sort("created_at", -1).limit(limit))
