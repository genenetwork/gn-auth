"""Application initialisation module."""
import os
import sys
import logging
from typing import Optional

from flask import Flask
from flask_cors import CORS

from gn_auth.misc_views import misc
from gn_auth.auth.views import oauth2

from gn_auth.auth.authentication.oauth2.server import setup_oauth2_server

from . import settings
from .errors import register_error_handlers

class ConfigurationError(Exception):
    """Raised in case of a configuration error."""

def __check_secret_key__(app: Flask) -> None:
    """Verify secret key is not empty."""
    if app.config.get("SECRET_KEY", "") == "":
        raise ConfigurationError("The `SECRET_KEY` settings cannot be empty.")

def check_mandatory_settings(app: Flask) -> None:
    """Verify that mandatory settings are defined in the application"""
    undefined = tuple(
        setting for setting in (
            "SECRET_KEY", "SQL_URI", "AUTH_DB", "AUTH_MIGRATIONS",
            "OAUTH2_SCOPE")
        if setting not in app.config)
    if len(undefined) > 0:
        raise ConfigurationError(
            "You must provide values for the following settings: " +
            "\t* " + "\n\t* ".join(undefined))

    __check_secret_key__(app)

def override_settings_with_envvars(
        app: Flask, ignore: tuple[str, ...]=tuple()) -> None:
    """Override settings in `app` with those in ENVVARS"""
    for setting in (key for key in app.config if key not in ignore):
        app.config[setting] = os.environ.get(setting) or app.config[setting]

def setup_logging_handlers(app: Flask) -> None:
    """Setup the loggging handlers."""
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    app.logger.addHandler(stderr_handler)

    root_logger = logging.getLogger()
    root_logger.addHandler(stderr_handler)
    root_logger.setLevel(app.config["LOGLEVEL"])

def create_app(config: Optional[dict] = None) -> Flask:
    """Create and return a new flask application."""
    app_instance_path = os.environ.get("GN_AUTH_INSTANCE_PATH")
    app = Flask(__name__,
                instance_path=app_instance_path,
                instance_relative_config=True)

    # ====== Setup configuration ======
    app.config.from_object(settings) # Default settings
    # Override defaults with startup settings
    app.config.update(config or {})
    # Override app settings with site-local settings
    if "GN_AUTH_CONF" in os.environ:
        app.config.from_envvar("GN_AUTH_CONF")

    override_settings_with_envvars(app)
    if bool(app_instance_path):## load secrets
        app.config.from_pyfile("secrets.py")
    # ====== END: Setup configuration ======

    check_mandatory_settings(app)

    setup_logging_handlers(app)
    setup_oauth2_server(app)

    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        allow_headers=app.config["CORS_HEADERS"],
        supports_credentials=True, intercept_exceptions=False)

    ## Blueprints
    app.register_blueprint(misc, url_prefix="/")
    app.register_blueprint(oauth2, url_prefix="/auth")

    register_error_handlers(app)

    return app
