"""Shared application configuration values loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for shared services."""

    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb://admin:AnasSuperMotDePasse123@mongodb:27017/jira_migration?authSource=admin",
    )
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
    PARSING_SERVICE_URL = os.getenv(
        "PARSING_SERVICE_URL", "http://parsing_service:5001"
    )
    COMPATIBILITY_SERVICE_URL = os.getenv(
        "COMPATIBILITY_SERVICE_URL", "http://compatibility_service:5002"
    )
    KNOWLEDGE_SERVICE_URL = os.getenv(
        "KNOWLEDGE_SERVICE_URL", "http://knowledge_service:5003"
    )
    REPORT_SERVICE_URL = os.getenv(
        "REPORT_SERVICE_URL", "http://report_service:5004"
    )
    WORKER_URL = os.getenv("WORKER_URL", "http://worker:5005")
    ANONYMIZED_TELEMETRY = os.getenv("ANONYMIZED_TELEMETRY", "false")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "false")
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = os.getenv(
        "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION",
        "python",
    )
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
