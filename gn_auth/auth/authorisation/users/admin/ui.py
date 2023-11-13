"""UI utilities for the auth system."""
from functools import wraps
from flask import flash, url_for, redirect

from gn_auth.session import logged_in, session_user, clear_session_info
from gn_auth.auth.authorisation.resources.system.models import (
    user_roles_on_system)

from ....authentication.users import User
from ....db.sqlite3 import with_db_connection

def is_admin(func):
    """Verify user is a system admin."""
    @wraps(func)
    @logged_in
    def __admin__(*args, **kwargs):
        admin_roles = [
            role for role in with_db_connection(
                lambda conn: user_roles_on_system(
                    conn, User(**session_user())))
            if role.role_name == "system-administrator"]
        if len(admin_roles) > 0:
            return func(*args, **kwargs)
        flash("Expected a system administrator.", "alert-danger")
        flash("You have been logged out of the system.", "alert-info")
        clear_session_info()
        return redirect(url_for("oauth2.admin.login"))
    return __admin__
