"""
Export dataset from MongoDB for AI feature detection training.
Extracts (source_code → features_detected) pairs.
"""

import json
from pymongo import MongoClient


client = MongoClient("mongodb://docker.itspectrum.fr:27017")
db = client["jira_migration"]

dataset = []

for analysis in db.analyses.find():
    for component in analysis.get("components", []):
        source_code = component.get("source_code", "")
        features = component.get("features_detected", [])

        if source_code and features:
            dataset.append({
                "input": source_code,
                "output": features,
                "component_type": component.get("component_type", ""),
                "plugin": component.get("plugin", ""),
            })

with open("feature_detection_dataset.json", "w", encoding="utf-8") as file:
    json.dump(dataset, file, indent=2, ensure_ascii=False)

print("Export terminé :", len(dataset), "exemples")
