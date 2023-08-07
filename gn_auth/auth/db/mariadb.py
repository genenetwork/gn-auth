"""Connections to MariaDB"""
import traceback
import contextlib
from typing import Iterator

import MySQLdb as mdb

from .protocols import DbConnection

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
    except Exception as _exc: # TODO: Make the Exception class less general
        logging.debug(traceback.format_exc())
        connection.rollback()
    finally:
        connection.commit()
        connection.close()
