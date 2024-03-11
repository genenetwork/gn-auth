"""Views relating to `System` resource(s)."""
from dataclasses import asdict
from flask import jsonify, Blueprint

from gn_auth.auth.db.sqlite3 import with_db_connection

from gn_auth.auth.authentication.oauth2.resource_server import require_oauth

from .models import user_roles_on_system

system = Blueprint("system", __name__)

@system.route("/roles")
def system_roles():
    """Get the roles that a user has that act on the system."""
    with require_oauth.acquire("profile group") as the_token:
        roles = with_db_connection(
            lambda conn: user_roles_on_system(conn, the_token.user))
        return jsonify(tuple(asdict(role) for role in roles))
