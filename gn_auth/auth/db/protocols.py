"""Common Database connection protocols."""
from typing import Any, Protocol

class DbCursor(Protocol):
    """Type annotation for a generic database cursor object."""
    def execute(self, *args, **kwargs) -> Any:
        """Execute a single query"""
        raise NotImplementedError

    def executemany(self, *args, **kwargs) -> Any:
        """
        Execute parameterized SQL statement sql against all parameter sequences
        or mappings found in the sequence parameters.
        """
        raise NotImplementedError

    def fetchone(self, *args, **kwargs):
        """Fetch single result if present, or `None`."""
        raise NotImplementedError

    def fetchmany(self, *args, **kwargs):
        """Fetch many results if present or `None`."""
        raise NotImplementedError

    def fetchall(self, *args, **kwargs):
        """Fetch all results if present or `None`."""
        raise NotImplementedError
