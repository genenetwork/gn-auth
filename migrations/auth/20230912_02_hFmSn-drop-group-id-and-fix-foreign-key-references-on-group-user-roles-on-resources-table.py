"""
Drop 'group_id' and fix foreign key references on 'group_user_roles_on_resources' table
"""

import sqlite3
from yoyo import step

__depends__ = {'20230912_01_BxrhE-add-system-resource'}

def drop_group_id(conn):
    """Drop `group_id` from `group_user_roles_on_resources` table."""
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.execute(
        """
        ALTER TABLE group_user_roles_on_resources
        RENAME TO group_user_roles_on_resources_bkp
        """)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS group_user_roles_on_resources (
          user_id TEXT NOT NULL,
          role_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          PRIMARY KEY (user_id, role_id, resource_id),
          FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (role_id)
            REFERENCES roles(role_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO group_user_roles_on_resources "
        "SELECT user_id, role_id, resource_id "
        "FROM group_user_roles_on_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS group_user_roles_on_resources_bkp")

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

def restore_group_id(conn):
    """Restore `group_id` to `group_user_roles_on_resources` table."""
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.execute(
        """
        ALTER TABLE group_user_roles_on_resources
        RENAME TO group_user_roles_on_resources_bkp
        """)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS group_user_roles_on_resources (
          group_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          role_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          PRIMARY KEY (group_id, user_id, role_id, resource_id),
          FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (group_id, role_id)
            REFERENCES group_roles(group_id, role_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO group_user_roles_on_resources
          SELECT
            ro.group_id, gurorb.user_id, gurorb.role_id, gurorb.resource_id
          FROM resource_ownership AS ro
          INNER JOIN group_user_roles_on_resources_bkp AS gurorb
          ON ro.resource_id=gurorb.resource_id
        """)

    conn.execute("DROP TABLE IF EXISTS group_user_roles_on_resources_bkp")

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

def link_sys_admin_user_roles(conn):
    """Link system-admins to the system resource."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ur.* FROM user_roles AS ur "
        "INNER JOIN roles AS r ON ur.role_id=r.role_id "
        "WHERE r.role_name='system-administrator'")
    admins = cursor.fetchall()
    cursor.execute(
        "SELECT r.resource_id FROM resources AS r "
        "INNER JOIN resource_categories AS rc "
        "ON r.resource_category_id=rc.resource_category_id "
        "WHERE rc.resource_category_key='system'")
    system_resource_id = cursor.fetchone()["resource_id"]
    cursor.executemany(
        "INSERT INTO "
        "group_user_roles_on_resources(user_id, role_id, resource_id) "
        "VALUES (:user_id, :role_id, :resource_id)",
        tuple({**admin, "resource_id": system_resource_id} for admin in admins))

def restore_sys_admin_user_roles(conn):
    """Restore fields into older `user_roles` table."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT guror.user_id, guror.role_id "
        "FROM group_user_roles_on_resources AS guror "
        "INNER JOIN resources AS r "
        "ON guror.resource_id=r.resource_id "
        "INNER JOIN resource_categories AS rc "
        "ON r.resource_category_id=rc.resource_category_id "
        "WHERE rc.resource_category_key='system'")
    user_roles = tuple(cursor.fetchall())
    cursor.executemany(
        "INSERT INTO user_roles(user_id, role_id) "
        "VALUES (:user_id, :role_id)",
        user_roles)

def link_group_leader_user_roles(conn):
    """Link group leaders to their resources."""
    conn.execute(
        """
        INSERT INTO group_user_roles_on_resources(user_id, role_id, resource_id)
         SELECT gu.user_id, r.role_id, gr.resource_id
         FROM group_resources AS gr INNER JOIN group_users AS gu
         ON gr.group_id=gu.group_id INNER JOIN user_roles AS ur
         ON gu.user_id=ur.user_id INNER JOIN roles AS r
         ON ur.role_id=r.role_id
         WHERE r.role_name='group-leader'
        """)

def restore_group_leader_user_roles(conn):
    """Restore group admins to older `user_roles` table."""
    conn.execute(
        """
        INSERT INTO user_roles(user_id, role_id)
         SELECT guror.user_id, guror.role_id
         FROM group_user_roles_on_resources AS guror
         INNER JOIN resources AS r ON guror.resource_id=r.resource_id
         INNER JOIN resource_categories AS rc
         ON r.resource_category_id=rc.resource_category_id
         WHERE rc.resource_category_key='group'
        """)

def link_group_creator_user_roles(conn):
    """Link group-creators to system."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ur.* FROM user_roles AS ur "
        "INNER JOIN roles AS r ON ur.role_id=r.role_id "
        "WHERE r.role_name='group_creator'")
    creators = cursor.fetchall()
    cursor.execute(
        "SELECT r.resource_id FROM resources AS r "
        "INNER JOIN resource_categories AS rc "
        "ON r.resource_category_id=rc.resource_category_id "
        "WHERE rc.resource_category_key='system'")
    sys_res_id = cursor.fetchone()["resource_id"]
    cursor.executemany(
        "INSERT INTO "
        "group_user_roles_on_resources(user_id, role_id, resource_id) "
        "VALUES (:user_id, :role_id, :resource_id)",
        tuple({**creator, "resource_id": sys_res_id} for creator in creators))

def restore_group_creator_user_roles(conn):
    "Restore group-creator user roles."
    conn.execute(
        """
        INSERT INTO user_roles
         SELECT guror.user_id, guror.role_id
         FROM group_user_roles_on_resources AS guror
         INNER JOIN roles AS r ON guror.role_id=r.role_id
         WHERE r.role_name='group-creator'""")

def rename_table(conn):
    "rename `group_user_roles_on_resources`, drop `user_roles`."
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.execute("DROP TABLE IF EXISTS user_roles")
    conn.execute(
        "ALTER TABLE group_user_roles_on_resources RENAME TO user_roles")

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

def restore_tables(conn):
    "rename to `group_user_roles_on_resources`, recreate original `user_roles`."
    conn.execute("PRAGMA foreign_keys = OFF")

    conn.execute(
        "ALTER TABLE user_roles RENAME TO group_user_roles_on_resources")
    conn.execute(
        """
        CREATE TABLE user_roles(
            user_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            PRIMARY KEY(user_id, role_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(role_id) REFERENCES roles(role_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

steps = [
    step(drop_group_id, restore_group_id),
    step(link_sys_admin_user_roles, restore_sys_admin_user_roles),
    step(link_group_leader_user_roles, restore_group_leader_user_roles),
    step(link_group_creator_user_roles, restore_group_creator_user_roles),
    step(rename_table, restore_tables)
]

