"""Repository for cached component compatibility analysis results."""

from datetime import datetime

from pymongo import ASCENDING

from shared.db.mongo_client import get_mongo_db


class ComponentAnalysisCacheRepository:
    """Repository for the 'component_analysis_cache' collection."""

    def __init__(self, db=None):
        self.db = db or get_mongo_db()
        self.collection = self.db.component_analysis_cache
        self.collection.create_index([("signature", ASCENDING)], unique=True)
        self.collection.create_index([("updated_at", ASCENDING)])

    def get_by_signature(self, signature: str) -> dict | None:
        """Return a cached analysis result for a component signature."""
        if not signature:
            return None

        return self.collection.find_one({"signature": signature})

    def upsert_result(
        self,
        signature_data: dict,
        result: dict,
        source_component: dict,
    ) -> None:
        """Insert or update a cached component analysis result."""
        signature = signature_data.get("signature")
        if not signature:
            return

        now = datetime.utcnow()
        self.collection.update_one(
            {"signature": signature},
            {
                "$set": {
                    **signature_data,
                    "result": result,
                    "component_name": source_component.get("component_name", ""),
                    "component_type_label": source_component.get("component_type", ""),
                    "plugin_label": source_component.get("plugin", ""),
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                    "usage_count": 0,
                },
            },
            upsert=True,
        )

    def mark_used(self, signature: str) -> None:
        """Record that a cached result was reused."""
        if not signature:
            return

        self.collection.update_one(
            {"signature": signature},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used_at": datetime.utcnow()},
            },
        )

    def list_recent(self, limit: int = 500) -> list[dict]:
        """Return recent cached component analyses for knowledge indexing."""
        projection = {
            "_id": 0,
            "signature": 1,
            "plugin": 1,
            "plugin_label": 1,
            "component_type": 1,
            "component_type_label": 1,
            "component_name": 1,
            "features": 1,
            "result": 1,
            "updated_at": 1,
            "usage_count": 1,
        }
        return list(
            self.collection.find({}, projection)
            .sort("updated_at", -1)
            .limit(limit)
        )

    def stats(self) -> dict:
        """Return lightweight cache statistics."""
        return {
            "collection_name": "component_analysis_cache",
            "entries": self.collection.count_documents({}),
        }
