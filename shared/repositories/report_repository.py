"""Repository implementation for report documents."""

from datetime import datetime

from shared.db.mongo_client import get_mongo_db


class ReportRepository:
    """Repository for the 'reports' collection."""

    def __init__(self, db=None):
        self.db = db or get_mongo_db()
        self.collection = self.db.reports
        self.archived_collection = self.db.reports_archived

    def insert_report(self, report_data: dict) -> str:
        """
        Insert a new report record into the database.

        Args:
            report_data: Dictionary containing report details (report_id, title, etc.)

        Returns:
            The inserted document's ID as a string.
        """
        result = self.collection.insert_one(report_data)
        return str(result.inserted_id)

    def get_report_by_id(self, report_id: str) -> dict | None:
        """
        Retrieve a report record by its report_id.

        Args:
            report_id: The unique identifier for the report.

        Returns:
            The report document if found, otherwise None.
        """
        return self.collection.find_one({
            "report_id": report_id,
            "status": {"$ne": False}
            })

    def list_reports(self, limit: int = 50) -> list[dict]:
        """
        Retrieve a list of recent report records with summary fields only.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of report summary documents.
        """
        projection = {
            "_id": 0,
            "report_id": 1,
            "matrix_id": 1,
            "analysis_id": 1,
            "generated_at": 1,
            "title": 1,
            "summary": 1,
            "status": 1,
        }
        return list(
            self.collection.find({"status": {"$ne": False}}, projection)
            .sort("generated_at", -1)
            .limit(limit)
        )

    def soft_delete_report(self, report_id: str) -> bool:
        """
        Update report status to False instead of removing it from database.
        """
        result = self.collection.update_one(
            {"report_id": report_id},
            {"$set": {"status": False}}
        )
        return result.modified_count > 0

    def archive_report(self, report_id: str) -> bool:
        """
        Move a report from the active 'reports' collection to 'reports_archived'.

        Returns:
            True if the report existed and was archived, False otherwise.
        """
        report = self.collection.find_one({"report_id": report_id})
        if not report:
            return False

        # Remove the source document ID to avoid duplicate _id errors in the target collection
        report.pop("_id", None)
        report["archived_at"] = report.get("archived_at") or datetime.utcnow()

        self.archived_collection.insert_one(report)
        self.collection.delete_one({"report_id": report_id})
        return True

    def list_archived_reports(self, limit: int = 50) -> list[dict]:
        """
        Retrieve a list of archived report records with summary fields only.
        """
        projection = {
            "_id": 0,
            "report_id": 1,
            "matrix_id": 1,
            "analysis_id": 1,
            "generated_at": 1,
            "title": 1,
            "summary": 1,
            "status": 1,
            "archived_at": 1,
        }
        return list(
            self.archived_collection.find({}, projection)
            .sort("archived_at", -1)
            .limit(limit)
        )
