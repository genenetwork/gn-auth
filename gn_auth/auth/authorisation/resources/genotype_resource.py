"""Genotype data resources functions and utilities."""
import uuid
from typing import Optional, Sequence

import sqlite3

import gn_auth.auth.db.sqlite3 as db

from .base import Resource
from .data import __attach_data__


def resource_data(
        cursor: db.DbCursor,
        resource_id: uuid.UUID,
        offset: int = 0,
        limit: Optional[int] = None) -> Sequence[sqlite3.Row]:
    """Fetch data linked to a Genotype resource"""
    cursor.execute(
        (("SELECT * FROM genotype_resources AS gr "
          "INNER JOIN linked_genotype_data AS lgd "
          "ON gr.data_link_id=lgd.data_link_id "
          "WHERE gr.resource_id=?") + (
              f" LIMIT {limit} OFFSET {offset}" if bool(limit) else "")),
        (str(resource_id),))
    return cursor.fetchall()

def link_data_to_resource(
        conn: db.DbConnection,
        resource: Resource,
        data_link_id: uuid.UUID) -> dict:
    """Link Genotype data with a resource."""
    with db.cursor(conn) as cursor:
        params = {
            "resource_id": str(resource.resource_id),
            "data_link_id": str(data_link_id)
        }
        cursor.execute(
            "INSERT INTO genotype_resources VALUES"
            "(:resource_id, :data_link_id)",
            params)
        return params

def unlink_data_from_resource(
        conn: db.DbConnection,
        resource: Resource,
        data_link_id: uuid.UUID) -> dict:
    """Unlink data from Genotype resources"""
    with db.cursor(conn) as cursor:
        cursor.execute("DELETE FROM genotype_resources "
                       "WHERE resource_id=? AND data_link_id=?",
                       (str(resource.resource_id), str(data_link_id)))
        return {
            "resource_id": str(resource.resource_id),
            "dataset_type": resource.resource_category.resource_category_key,
            "data_link_id": data_link_id
        }

def attach_resources_data(
        cursor, resources: Sequence[Resource]) -> Sequence[Resource]:
    """Attach linked data to Genotype resources"""
    placeholders = ", ".join(["?"] * len(resources))
    cursor.execute(
        "SELECT * FROM genotype_resources AS gr "
        "INNER JOIN linked_genotype_data AS lgd "
        "ON gr.data_link_id=lgd.data_link_id "
        f"WHERE gr.resource_id IN ({placeholders})",
        tuple(str(resource.resource_id) for resource in resources))
    return __attach_data__(cursor.fetchall(), resources)
