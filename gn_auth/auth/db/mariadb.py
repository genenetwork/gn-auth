"""Connections to MariaDB"""
import logging
import traceback
import contextlib
from urllib.parse import urlparse
from typing import Any, Tuple, Protocol, Iterator

import MySQLdb as mdb

class DbConnection(Protocol):
    """Type annotation for a generic database connection object."""
    def cursor(self, *args, **kwargs) -> Any:
        """A cursor object"""

    def commit(self, *args, **kwargs) -> Any:
        """Commit the transaction."""

    def rollback(self) -> Any:
        """Rollback the transaction."""

def parse_db_url(sql_uri: str) -> Tuple:
    """Parse SQL_URI env variable note:there is a default value for SQL_URI so a
    tuple result is always expected"""
    parsed_db = urlparse(sql_uri)
    return (
        parsed_db.hostname, parsed_db.username, parsed_db.password,
        parsed_db.path[1:], parsed_db.port)

@contextlib.contextmanager
def database_connection(sql_uri) -> Iterator[DbConnection]:
    """Connect to MySQL database."""
    host, user, passwd, db_name, port = parse_db_url(sql_uri)
    connection = mdb.connect(db=db_name,
                             user=user,
                             passwd=passwd or '',
                             host=host,
                             port=port or 3306)
    try:
        yield connection
    except mdb.Error as _mdb_err:
        logging.debug(traceback.format_exc())
        connection.rollback()
    finally:
        connection.commit()
        connection.close()
