"""Logging utilities shared across backend services."""

import logging


def setup_logger(app):
    """Configure the application logger and emit a startup message."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    app.logger.info("🚀 App started")
