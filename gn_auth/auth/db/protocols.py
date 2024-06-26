"""Common Database connection protocols."""
from typing import Any, Protocol

class DbCursor(Protocol):
    """Type annotation for a generic database cursor object."""
    def execute(self, *args, **kwargs) -> Any:
        """Execute a single query"""

    def executemany(self, *args, **kwargs) -> Any:
        """
        Execute parameterized SQL statement sql against all parameter sequences
        or mappings found in the sequence parameters.
        """

    def fetchone(self, *args, **kwargs):
        """Fetch single result if present, or `None`."""

    def fetchmany(self, *args, **kwargs):
        """Fetch many results if present or `None`."""

    def fetchall(self, *args, **kwargs):
        """Fetch all results if present or `None`."""
