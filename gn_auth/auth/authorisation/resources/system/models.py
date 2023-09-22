"""Base functions and utilities for system resources."""
from uuid import UUID
from functools import reduce
from typing import Sequence

from gn_auth.auth.db import sqlite3 as db

from gn_auth.auth.authentication.users import User

from gn_auth.auth.authorisation.roles import Role
from gn_auth.auth.authorisation.privileges import Privilege

def __organise_privileges__(acc, row):
    role_id = UUID(row["role_id"])
    role = acc.get(role_id, Role(
        role_id, row["role_name"], bool(int(row["user_editable"])), tuple()))
    return {
        **acc,
        role_id: Role(
            role.role_id,
            role.role_name,
            role.user_editable,
            (role.privileges +
             (Privilege(row["privilege_id"], row["privilege_description"]),)))
    }

def user_roles_on_system(conn: db.DbConnection, user: User) -> Sequence[Role]:
    """
    Retrieve all roles assigned to the `user` that act on `system` resources.
    """
    with db.cursor(conn) as cursor:
        role_ids_query = (
            "SELECT ur.role_id FROM user_roles AS ur INNER JOIN resources AS r "
            "ON ur.resource_id=r.resource_id "
            "INNER JOIN resource_categories AS rc "
            "ON r.resource_category_id=rc.resource_category_id "
            "WHERE user_id=? AND rc.resource_category_key='system'")
        cursor.execute(
            "SELECT r.*, p.* FROM roles AS r "
            "INNER JOIN role_privileges AS rp ON r.role_id=rp.role_id "
            "INNER JOIN privileges AS p ON rp.privilege_id=p.privilege_id "
            f"WHERE r.role_id IN ({role_ids_query})",
            (str(user.user_id),))

        return tuple(reduce(
            __organise_privileges__, cursor.fetchall(), {}).values())
    return tuple()
