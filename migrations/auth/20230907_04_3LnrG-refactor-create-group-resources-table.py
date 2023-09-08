"""
refactor: create 'group_resources' table.
"""

import uuid
import random
import string

import sqlite3
from yoyo import step

__depends__ = {'20230907_03_BwAmf-refactor-drop-group-id-from-resources-table'}

def randstr(length: int = 5):
    """Generate random string."""
    return "".join(random.choices(
        string.ascii_letters + string.digits, k=length))

def create_and_link_resources_for_existing_groups(conn):
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, group_name FROM groups")
    resources = tuple({
        "group_id": row["group_id"],
        "resource_id": str(uuid.uuid4()),
        "resource_name": f"{randstr(10)}: {row['group_name']}",
        "resource_category_id": "1e0f70ee-add5-4358-8c6c-43de77fa4cce"
    } for row in cursor.fetchall())
    cursor.executemany(
        "INSERT INTO "
        "resources(resource_id, resource_name, resource_category_id) "
        "VALUES (:resource_id, :resource_name, :resource_category_id)",
        resources)
    cursor.executemany(
        "INSERT INTO group_resources(resource_id, group_id) "
        "VALUES (:resource_id, :group_id)",
        resources)

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS group_resources(
        -- Links groups to the resources of type 'group' that control access to
        -- each group
        resource_id TEXT NOT NULL,
        group_id TEXT NOT NULL,
        PRIMARY KEY(resource_id, group_id),
        FOREIGN KEY (resource_id)
          REFERENCES resources(resource_id)
          ON UPDATE CASCADE ON DELETE RESTRICT,
        FOREIGN KEY (group_id)
          REFERENCES groups(group_id)
          ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS group_resources"),
    step(create_and_link_resources_for_existing_groups)
]
