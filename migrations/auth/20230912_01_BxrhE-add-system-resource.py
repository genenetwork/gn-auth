"""
Add 'system' resource.
"""

import uuid

import sqlite3
from yoyo import step

__depends__ = {'20230907_04_3LnrG-refactor-create-group-resources-table'}

def add_system_resource(conn):
    """Add a system resource."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT resource_category_id FROM resource_categories "
        "WHERE resource_category_key='system'")
    category_id = cursor.fetchone()["resource_category_id"]
    cursor.execute(
        "INSERT INTO "
        "resources(resource_id, resource_name, resource_category_id, public) "
        "VALUES(?, ?, ?, ?)",
        (str(uuid.uuid4()), "GeneNetwork System", category_id, "1"))

def delete_system_resource(conn):
    """Add a system resource."""
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT resource_category_id FROM resource_categories "
        "WHERE resource_category_key='system'")
    category_id = cursor.fetchone()["resource_category_id"]
    cursor.execute("DELETE FROM resources WHERE resource_category_id = ?",
                   (category_id,))

steps = [
    step(add_system_resource, delete_system_resource)
]
