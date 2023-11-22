"""Major function for handling admin users."""
from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.authentication.users import User

def make_sys_admin(cursor: db.DbCursor, user: User) -> User:
    """Make a given user into an system admin."""
    cursor.execute(
            "SELECT * FROM roles WHERE role_name='system-administrator'")
    admin_role = cursor.fetchone()
    cursor.execute(
            "SELECT * FROM resources AS r "
            "INNER JOIN resource_categories AS rc "
            "ON r.resource_category_id=rc.resource_category_id "
            "WHERE resource_category_key='system'")
    the_system = cursor.fetchone()
    cursor.execute(
        "INSERT INTO user_roles VALUES (:user_id, :role_id, :resource_id)",
        {
            "user_id": str(user.user_id),
            "role_id": admin_role["role_id"],
            "resource_id": the_system["resource_id"]
        })
    return user
