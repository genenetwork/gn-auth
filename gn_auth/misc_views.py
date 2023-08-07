"""
Miscellaneous top-level views that have nothing to do with the application's
functionality.
"""
from pathlib import Path

from flask import Blueprint

misc = Blueprint("misc", __name__)

@misc.route("/version")
def version():
    """Get the application's version information."""
    version_file = Path("VERSION.txt")
    if version_file.exists():
        with open(version_file, encoding="utf-8") as verfl:
            return verfl.read().strip()
    return "0.0.0"
