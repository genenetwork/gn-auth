"""Base types for resources."""
from uuid import UUID
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class ResourceCategory:
    """Class representing a resource category."""
    resource_category_id: UUID
    resource_category_key: str
    resource_category_description: str


@dataclass(frozen=True)
class Resource:
    """Class representing a resource."""
    resource_id: UUID
    resource_name: str
    resource_category: ResourceCategory
    public: bool
    resource_data: Sequence[dict[str, Any]] = tuple()
