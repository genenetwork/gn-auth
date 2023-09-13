"""Base types for resources."""
from uuid import UUID
from typing import Any, Sequence, NamedTuple

from gn_auth.auth.dictify import dictify

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

class Resource(NamedTuple):
    """Class representing a resource."""
    resource_id: UUID
    resource_name: str
    resource_category: ResourceCategory
    public: bool
    resource_data: Sequence[dict[str, Any]] = tuple()

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `Resource` objects."""
        return {
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_category": dictify(self.resource_category),
            "public": self.public,
            "resource_data": self.resource_data
        }
