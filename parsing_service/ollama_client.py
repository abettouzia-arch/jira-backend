"""Client utilities for communicating with the Ollama service."""

import logging
import os

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"))


class OllamaConnectionError(RuntimeError):
    """Raised when the Ollama service cannot be reached or returns an invalid response."""


def generate_text(prompt: str, model: str = "llama3", format_json: bool = False) -> str:
    """
    Send a prompt to the Ollama API and return the generated response.

    If format_json is True, Ollama is asked to return a JSON-formatted response.
    """
    url = f"{OLLAMA_URL}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    if format_json:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    except requests.exceptions.RequestException as e:
        logger.error("Failed to connect to Ollama at %s. Error: %s", OLLAMA_URL, e)
        raise OllamaConnectionError(f"Ollama connection failed: {e}") from e
