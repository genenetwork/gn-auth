"""Handle application level errors."""
import traceback

from werkzeug.exceptions import NotFound
from flask import Flask, request, jsonify, current_app, render_template

from gn_auth.auth.authorisation.errors import AuthorisationError

def add_trace(exc: Exception, errobj: dict) -> dict:
    """Add the traceback to the error handling object."""
    return {
        **errobj,
        "error-trace": "".join(traceback.format_exception(exc))
    }

def page_not_found(exc):
    """404 handler."""
    content_type = request.content_type
    if bool(content_type) and content_type.lower() == "application/json":
        return jsonify(add_trace(exc, {
            "error": exc.name,
            "error_description": (f"The page '{request.url}' does not exist on "
                                  "this server.")
        })), 404

    return render_template("404.html", page=request.url)

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify(add_trace(exc, {
        "error": type(exc).__name__,
        "error_description": " :: ".join(exc.args)
    })), exc.error_code

__error_handlers__ = {
    AuthorisationError: handle_authorisation_error,
    NotFound: page_not_found
}
def register_error_handlers(app: Flask):
    """Register ALL defined error handlers"""
    for class_, error_handler in __error_handlers__.items():
        app.register_error_handler(class_, error_handler)
