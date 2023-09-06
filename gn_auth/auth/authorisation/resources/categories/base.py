"""Base resource category."""
from uuid import UUID
from typing import Any, Sequence, NamedTuple


from ...errors import NotFoundError

from ....db import sqlite3 as db

class ResourceCategory(NamedTuple):
    """Class representing a resource category."""
    resource_category_id: UUID
    resource_category_key: str
    resource_category_description: str

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `ResourceCategory` objects."""
        return {
            "resource_category_id": self.resource_category_id,
            "resource_category_key": self.resource_category_key,
            "resource_category_description": self.resource_category_description
        }

def resource_category_by_id(
        conn: db.DbConnection, category_id: UUID) -> ResourceCategory:
    """Retrieve a resource category by its ID."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM resource_categories WHERE "
            "resource_category_id=?",
            (str(category_id),))
        results = cursor.fetchone()
        if results:
            return ResourceCategory(
                UUID(results["resource_category_id"]),
                results["resource_category_key"],
                results["resource_category_description"])

    raise NotFoundError(
        f"Could not find a ResourceCategory with ID '{category_id}'")

def resource_categories(conn: db.DbConnection) -> Sequence[ResourceCategory]:
    """Retrieve all available resource categories"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        return tuple(
            ResourceCategory(UUID(row[0]), row[1], row[2])
            for row in cursor.fetchall())
    return tuple()
