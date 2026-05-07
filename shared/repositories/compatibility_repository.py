"""Repository implementation for compatibility matrix documents."""

from shared.db.mongo_client import get_mongo_db


class CompatibilityRepository:
    """Repository for the 'compatibility_matrices' collection."""

    def __init__(self, db=None):
        self.db = db or get_mongo_db()
        self.collection = self.db.compatibility_matrices

    def insert_matrix(self, matrix_data: dict) -> str:
        """
        Insert a compatibility matrix document into the database.

        Args:
            matrix_data: Dictionary representing the matrix.

        Returns:
            The inserted document ID as a string.
        """
        result = self.collection.insert_one(matrix_data)
        return str(result.inserted_id)

    def get_matrix_by_id(self, matrix_id: str) -> dict | None:
        """
        Retrieve a compatibility matrix by its matrix_id.

        Args:
            matrix_id: The unique identifier for the matrix.

        Returns:
            The matrix document if found, otherwise None.
        """
        return self.collection.find_one({"matrix_id": matrix_id})

    def list_matrices(self, limit: int = 50) -> list[dict]:
        """
        List recent compatibility matrices.

        Args:
            limit: Maximum number of documents to return.

        Returns:
            List of compatibility matrix documents.
        """
        projection = {
            "_id": 0,
            "matrix_id": 1,
            "analysis_id": 1,
            "analyzed_at": 1,
            "summary": 1,
        }
        return list(
            self.collection.find({}, projection).sort("analyzed_at", -1).limit(limit)
        )

    def get_latest_matrix_by_analysis_id(self, analysis_id: str) -> dict | None:
        """
        Retrieve the latest compatibility matrix for a given analysis_id.

        Args:
            analysis_id: The analysis identifier to query.

        Returns:
            The latest matrix document if found, otherwise None.
        """
        return self.collection.find_one(
            {"analysis_id": analysis_id},
            sort=[("analyzed_at", -1)],
        )
