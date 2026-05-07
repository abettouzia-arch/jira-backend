"""Shared Flask error handlers for API services."""

from flask import jsonify


def register_error_handlers(app):
    """Register common HTTP error handlers on the Flask app."""

    @app.errorhandler(404)
    def not_found(_error):
        """Handle 404 errors."""
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        return jsonify({"error": str(error)}), 500
