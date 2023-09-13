"""
Utilities for handling data on resources.

These are mostly meant for internal use.
"""
from uuid import UUID
from typing import Sequence
from functools import reduce

import sqlite3

from .base import Resource

def __attach_data__(
        data_rows: Sequence[sqlite3.Row],
        resources: Sequence[Resource]) -> Sequence[Resource]:
    def __organise__(acc, row):
        resource_id = UUID(row["resource_id"])
        return {
            **acc,
            resource_id: acc.get(resource_id, tuple()) + (dict(row),)
        }
    organised: dict[UUID, tuple[dict, ...]] = reduce(__organise__, data_rows, {})
    return tuple(
        Resource(
            resource.group, resource.resource_id, resource.resource_name,
            resource.resource_category, resource.public,
            organised.get(resource.resource_id, tuple()))
        for resource in resources)
