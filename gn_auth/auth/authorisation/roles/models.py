"""Handle management of roles"""
from uuid import UUID, uuid4
from functools import reduce
from dataclasses import dataclass

from typing import Sequence, Iterable

from pymonad.either import Left, Right, Either

from ...db import sqlite3 as db
from ...authentication.users import User

from ..checks import authorised_p
from ..privileges import Privilege
from ..errors import NotFoundError, AuthorisationError


@dataclass(frozen=True)
class Role:
    """Class representing a role: creates immutable objects."""
    role_id: UUID
    role_name: str
    user_editable: bool
    privileges: tuple[Privilege, ...]


def check_user_editable(role: Role):
    """Raise an exception if `role` is not user editable."""
    if not role.user_editable:
        raise AuthorisationError(
            f"The role `{role.role_name}` is not user editable.")

@authorised_p(
    privileges = ("group:role:create-role",),
    error_description="Could not create role")
def create_role(
        cursor: db.DbCursor, role_name: str,
        privileges: Iterable[Privilege]) -> Role:
    """
    Create a new generic role.

    PARAMS:
    * cursor: A database cursor object - This function could be used as part of
              a transaction, hence the use of a cursor rather than a connection
              object.
    * role_name: The name of the role
    * privileges: A 'list' of privileges to assign the new role

    RETURNS: An immutable `gn3.auth.authorisation.roles.Role` object
    """
    role = Role(uuid4(), role_name, True, tuple(privileges))

    cursor.execute(
        "INSERT INTO roles(role_id, role_name, user_editable) VALUES (?, ?, ?)",
        (str(role.role_id), role.role_name, (1 if role.user_editable else 0)))
    cursor.executemany(
        "INSERT INTO role_privileges(role_id, privilege_id) VALUES (?, ?)",
        tuple((str(role.role_id), str(priv.privilege_id))
              for priv in privileges))

    return role

def __organise_privileges__(resources, row) -> dict:
    resource_id = UUID(row["resource_id"])
    role_id = UUID(row["role_id"])
    roles = resources.get(resource_id, {}).get("roles", {})
    role = roles.get(role_id, Role(
        role_id,
        row["role_name"],
        bool(int(row["user_editable"])),
        tuple()))
    return {
        **resources,
        resource_id: {
            "resource_id": resource_id,
            "user_id": UUID(row["user_id"]),
            "roles": {
                **roles,
                role_id: Role(
                    role.role_id,
                    role.role_name,
                    role.user_editable,
                    role.privileges + (Privilege(
                        row["privilege_id"],
                        row["privilege_description"]),)
                )
            }
        }
    }

def user_roles(conn: db.DbConnection, user: User) -> Sequence[dict]:
    """Retrieve all roles (organised by resource) assigned to the user."""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM user_roles")
        cursor.execute(
            "SELECT ur.resource_id, ur.user_id, r.*, p.* "
            "FROM user_roles AS ur "
            "INNER JOIN roles AS r ON ur.role_id=r.role_id "
            "INNER JOIN role_privileges AS rp ON r.role_id=rp.role_id "
            "INNER JOIN privileges AS p ON rp.privilege_id=p.privilege_id "
            "WHERE ur.user_id=?",
            (str(user.user_id),))

        return tuple({# type: ignore[var-annotated]
            **row, "roles": tuple(row["roles"].values())
        } for row in reduce(
            __organise_privileges__, cursor.fetchall(), {}).values())
    return tuple()

def user_role(conn: db.DbConnection, user: User, role_id: UUID) -> Either:
    """Retrieve a specific non-resource role assigned to the user."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT res.resource_id, ur.user_id, r.*, p.* "
            "FROM resources AS res INNER JOIN user_roles AS ur "
            "ON res.resource_id=ur.resource_id INNER JOIN roles AS r "
            "ON ur.role_id=r.role_id INNER JOIN role_privileges AS rp "
            "ON r.role_id=rp.role_id INNER JOIN privileges AS p "
            "ON rp.privilege_id=p.privilege_id "
            "WHERE ur.user_id=? AND ur.role_id=?",
            (str(user.user_id), str(role_id)))

        results = cursor.fetchall()
        if results:
            res_role_obj = tuple(# type: ignore[var-annotated]
                reduce(__organise_privileges__, results, {}).values())[0]
            resource_id = res_role_obj["resource_id"]
            role = tuple(res_role_obj["roles"].values())[0]
            return Right((role, resource_id))
        return Left(NotFoundError(
            f"Could not find role with id '{role_id}'",))

def __assign_group_creator_role__(cursor: db.DbCursor, user: User):
    cursor.execute(
        'SELECT role_id FROM roles WHERE role_name IN '
        '("group-creator")')
    role_id = cursor.fetchone()["role_id"]
    cursor.execute(
        "SELECT resource_id FROM resources AS r "
        "INNER JOIN resource_categories AS rc "
        "ON r.resource_category_id=rc.resource_category_id "
        "WHERE rc.resource_category_key='system'")
    resource_id = cursor.fetchone()["resource_id"]
    cursor.execute(
        ("INSERT INTO user_roles VALUES (:user_id, :role_id, :resource_id)"),
        {"user_id": str(user.user_id), "role_id": role_id,
         "resource_id": resource_id})

def __assign_public_view_role__(cursor: db.DbCursor, user: User):
    cursor.execute("SELECT resource_id FROM resources WHERE public=1")
    public_resources = tuple(row["resource_id"] for row in cursor.fetchall())
    cursor.execute("SELECT role_id FROM roles WHERE role_name='public-view'")
    role_id = cursor.fetchone()["role_id"]
    cursor.executemany(
        "INSERT INTO user_roles(user_id, role_id, resource_id) "
        "VALUES(:user_id, :role_id, :resource_id)",
        tuple({
            "user_id": str(user.user_id),
            "role_id": role_id,
            "resource_id": resource_id
        } for resource_id in public_resources))

def assign_default_roles(cursor: db.DbCursor, user: User):
    """Assign `user` some default roles."""
    __assign_group_creator_role__(cursor, user)
    __assign_public_view_role__(cursor, user)

def revoke_user_role_by_name(cursor: db.DbCursor, user: User, role_name: str):
    """Revoke a role from `user` by the role's name"""
    # TODO: Pass in the resource_id - this works somewhat correctly, but it's
    #       only because it is used in for revoking the "group-creator" role so
    #       far
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name=:role_name",
        {"role_name": role_name})
    role = cursor.fetchone()
    if role:
        cursor.execute(
            ("DELETE FROM user_roles "
             "WHERE user_id=:user_id AND role_id=:role_id"),
            {"user_id": str(user.user_id), "role_id": role["role_id"]})

def assign_user_role_by_name(
        cursor: db.DbCursor, user: User, resource_id: UUID, role_name: str):
    """Revoke a role from `user` by the role's name"""
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name=:role_name",
        {"role_name": role_name})
    role = cursor.fetchone()

    if role:
        cursor.execute(
            ("INSERT INTO user_roles VALUES(:user_id, :role_id, :resource_id) "
             "ON CONFLICT DO NOTHING"),
            {
                "user_id": str(user.user_id),
                "role_id": role["role_id"],
                "resource_id": str(resource_id)
            })
