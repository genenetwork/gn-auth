"""
Add new "public-view" role
"""

import sqlite3

from yoyo import step

__depends__ = {'20230912_02_hFmSn-drop-group-id-and-fix-foreign-key-references-on-group-user-roles-on-resources-table'}

def grant_to_all_users_public_view_role(conn):
    """Grant the `public-view` role to all existing users."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    user_ids = tuple(row["user_id"] for row in cursor.fetchall())

    cursor.execute("SELECT resource_id FROM resources WHERE public=1")
    resource_ids = tuple(row["resource_id"] for row in cursor.fetchall())

    params = tuple({
        "user_id": user_id,
        "resource_id": resource_id,
        "role_id": "fd88bfed-d869-4969-87f2-67c4e8446ecb"
    } for user_id in user_ids for resource_id in resource_ids)
    cursor.executemany(
        "INSERT INTO user_roles(user_id, role_id, resource_id) "
        "VALUES (:user_id, :role_id, :resource_id) ",
        params)

def revoke_from_all_users_public_view_role(conn):
    """Revoke the `public-view` role from all existing users."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "DELETE FROM user_roles "
        "WHERE role_id='fd88bfed-d869-4969-87f2-67c4e8446ecb'")

steps = [
    step(
        """
        INSERT INTO roles(role_id, role_name, user_editable)
        VALUES('fd88bfed-d869-4969-87f2-67c4e8446ecb', 'public-view', 0)
        """,
        """
        DELETE FROM roles WHERE role_id='fd88bfed-d869-4969-87f2-67c4e8446ecb'
        """),
    step(
        """
        INSERT INTO role_privileges(role_id, privilege_id)
        VALUES(
          'fd88bfed-d869-4969-87f2-67c4e8446ecb',
          'group:resource:view-resource')
        """,
        """
        DELETE FROM role_privileges
        WHERE role_id='fd88bfed-d869-4969-87f2-67c4e8446ecb'
        """),
    step(grant_to_all_users_public_view_role,
         revoke_from_all_users_public_view_role)
]
