"""Handle authorisation checks for resources"""
from uuid import UUID
from functools import reduce
from typing import Sequence

from ...db import sqlite3 as db
from ...authentication.users import User

def __organise_privileges_by_resource_id__(rows):
    def __organise__(privs, row):
        resource_id = UUID(row["resource_id"])
        return {
            **privs,
            resource_id: (row["privilege_id"],) + privs.get(
                resource_id, tuple())
        }
    return reduce(__organise__, rows, {})

def authorised_for(conn: db.DbConnection, user: User, privileges: tuple[str],
                   resource_ids: Sequence[UUID]) -> dict[UUID, bool]:
    """
    Check whether `user` is authorised to access `resources` according to given
    `privileges`.
    """
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT ur.*, rp.privilege_id FROM "
             "user_roles AS ur "
             "INNER JOIN roles AS r ON ur.role_id=r.role_id "
             "INNER JOIN role_privileges AS rp ON r.role_id=rp.role_id "
             "WHERE ur.user_id=? "
             f"AND ur.resource_id IN ({', '.join(['?']*len(resource_ids))})"
             f"AND rp.privilege_id IN ({', '.join(['?']*len(privileges))})"),
            ((str(user.user_id),) + tuple(
                str(r_id) for r_id in resource_ids) + tuple(privileges)))
        resource_privileges = __organise_privileges_by_resource_id__(
            cursor.fetchall())
        authorised = tuple(resource_id for resource_id, res_privileges
                           in resource_privileges.items()
                           if all(priv in res_privileges
                                  for priv in privileges))
        return {
            resource_id: resource_id in authorised
            for resource_id in resource_ids
        }
