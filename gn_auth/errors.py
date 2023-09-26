"""Handle application level errors."""
from flask import Flask, jsonify, current_app

from gn_auth.auth.authorisation.errors import AuthorisationError

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify({
        "error": type(exc).__name__,
        "error_description": " :: ".join(exc.args)
    }), exc.error_code

__error_handlers__ = {
    AuthorisationError: handle_authorisation_error
}
def register_error_handlers(app: Flask):
    """Register ALL defined error handlers"""
    for klass, error_handler in __error_handlers__.items():
        app.register_error_handler(klass, error_handler)
