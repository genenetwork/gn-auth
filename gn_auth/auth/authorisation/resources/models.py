"""Handle the management of resources."""
import json
from uuid import UUID, uuid4
from functools import reduce, partial
from typing import Dict, Sequence, Optional

from pymonad.maybe import Just, Maybe, Nothing

from ...db import sqlite3 as db
from ...dictify import dictify
from ...authentication.users import User
from ...db.sqlite3 import with_db_connection

from ..checks import authorised_p
from ..errors import NotFoundError, AuthorisationError
from ..groups.models import (
    Group, GroupRole, user_group, group_by_id, is_group_leader)

from .checks import authorised_for
from .base import Resource, ResourceCategory
from .mrna_resource import (
    resource_data as mrna_resource_data,
    attach_resources_data as mrna_attach_resources_data,
    link_data_to_resource as mrna_link_data_to_resource,
    unlink_data_from_resource as mrna_unlink_data_from_resource)
from .genotype_resource import (
    resource_data as genotype_resource_data,
    attach_resources_data as genotype_attach_resources_data,
    link_data_to_resource as genotype_link_data_to_resource,
    unlink_data_from_resource as genotype_unlink_data_from_resource)
from .phenotype_resource import (
    resource_data as phenotype_resource_data,
    attach_resources_data as phenotype_attach_resources_data,
    link_data_to_resource as phenotype_link_data_to_resource,
    unlink_data_from_resource as phenotype_unlink_data_from_resource)

class MissingGroupError(AuthorisationError):
    """Raised for any resource operation without a group."""

def __assign_resource_owner_role__(cursor, resource, user, group):
    """Assign `user` the 'Resource Owner' role for `resource`."""
    cursor.execute(
        "SELECT gr.* FROM group_roles AS gr INNER JOIN roles AS r "
        "ON gr.role_id=r.role_id WHERE r.role_name='resource-owner' "
        "AND gr.group_id=?",
        (str(group.group_id),))
    role = cursor.fetchone()
    if not role:
        cursor.execute("SELECT * FROM roles WHERE role_name='resource-owner'")
        role = cursor.fetchone()
        cursor.execute(
            "INSERT INTO group_roles VALUES "
            "(:group_role_id, :group_id, :role_id)",
            {"group_role_id": str(uuid4()),
             "group_id": str(group.group_id),
             "role_id": role["role_id"]})

    cursor.execute(
            "INSERT INTO group_user_roles_on_resources "
            "VALUES ("
            ":group_id, :user_id, :role_id, :resource_id"
            ")",
            {"group_id": str(resource.group_id),
             "user_id": str(user.user_id),
             "role_id": role["role_id"],
             "resource_id": str(resource.resource_id)})

@authorised_p(("group:resource:create-resource",),
              error_description="Insufficient privileges to create a resource",
              oauth2_scope="profile resource")
def create_resource(
        conn: db.DbConnection, resource_name: str,
        resource_category: ResourceCategory, user: User,
        public: bool) -> Resource:
    """Create a resource item."""
    with db.cursor(conn) as cursor:
        group = user_group(conn, user).maybe(
            False, lambda grp: grp)# type: ignore[misc, arg-type]
        if not group:
            raise MissingGroupError(
                "User with no group cannot create a resource.")
        resource = Resource(uuid4(), resource_name, resource_category, public)
        cursor.execute(
            "INSERT INTO resources VALUES (?, ?, ?, ?)",
            (str(resource.resource_id),
             resource_name,
             str(resource.resource_category.resource_category_id),
             1 if resource.public else 0))
        cursor.execute("INSERT INTO resource_ownership (group_id, resource_id) "
                       "VALUES (?, ?)",
                       (str(group.group_id), str(resource.resource_id)))
        __assign_resource_owner_role__(cursor, resource, user, group)

    return resource

def resource_category_by_id(
        conn: db.DbConnection, category_id: UUID) -> ResourceCategory:
    """Retrieve a resource category by its ID."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM resource_categories WHERE "
            "resource_category_id=?",
            (str(category_id),))
        results = cursor.fetchone()
        if results:
            return ResourceCategory(
                UUID(results["resource_category_id"]),
                results["resource_category_key"],
                results["resource_category_description"])

    raise NotFoundError(
        f"Could not find a ResourceCategory with ID '{category_id}'")

def resource_categories(conn: db.DbConnection) -> Sequence[ResourceCategory]:
    """Retrieve all available resource categories"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        return tuple(
            ResourceCategory(UUID(row[0]), row[1], row[2])
            for row in cursor.fetchall())
    return tuple()

def public_resources(conn: db.DbConnection) -> Sequence[Resource]:
    """List all resources marked as public"""
    categories = {
        str(cat.resource_category_id): cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resources WHERE public=1")
        results = cursor.fetchall()
        group_uuids = tuple(row[0] for row in results)
        query = ("SELECT * FROM groups WHERE group_id IN "
                 f"({', '.join(['?'] * len(group_uuids))})")
        cursor.execute(query, group_uuids)
        groups = {
            row[0]: Group(
                UUID(row[0]), row[1], json.loads(row[2] or "{}"))
            for row in cursor.fetchall()
        }
        return tuple(
            Resource(groups[row[0]], UUID(row[1]), row[2], categories[row[3]],
                     bool(row[4]))
            for row in results)

def group_leader_resources(
        conn: db.DbConnection, user: User, group: Group,
        res_categories: Dict[UUID, ResourceCategory]) -> Sequence[Resource]:
    """Return all the resources available to the group leader"""
    if is_group_leader(conn, user, group):
        with db.cursor(conn) as cursor:
            cursor.execute("SELECT * FROM resources WHERE group_id=?",
                           (str(group.group_id),))
            return tuple(
                Resource(group, UUID(row[1]), row[2],
                         res_categories[UUID(row[3])], bool(row[4]))
                for row in cursor.fetchall())
    return tuple()

def user_resources(conn: db.DbConnection, user: User) -> Sequence[Resource]:
    """List the resources available to the user"""
    categories = { # Repeated in `public_resources` function
        cat.resource_category_id: cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        def __all_resources__(group) -> Sequence[Resource]:
            gl_resources = group_leader_resources(conn, user, group, categories)

            cursor.execute(
                ("SELECT resources.* FROM group_user_roles_on_resources "
                 "LEFT JOIN resources "
                 "ON group_user_roles_on_resources.resource_id=resources.resource_id "
                 "WHERE group_user_roles_on_resources.group_id = ? "
                 "AND group_user_roles_on_resources.user_id = ?"),
                (str(group.group_id), str(user.user_id)))
            rows = cursor.fetchall()
            private_res = tuple(
                Resource(group, UUID(row[1]), row[2], categories[UUID(row[3])],
                         bool(row[4]))
                for row in rows)
            return tuple({
                res.resource_id: res
                for res in
                (private_res + gl_resources + public_resources(conn))# type: ignore[operator]
            }.values())

        # Fix the typing here
        return user_group(conn, user).map(__all_resources__).maybe(# type: ignore[arg-type,misc]
            public_resources(conn), lambda res: res)# type: ignore[arg-type,return-value]

def resource_data(conn, resource, offset: int = 0, limit: Optional[int] = None) -> tuple[dict, ...]:
    """
    Retrieve the data for `resource`, optionally limiting the number of items.
    """
    resource_data_function = {
        "mrna": mrna_resource_data,
        "genotype": genotype_resource_data,
        "phenotype": phenotype_resource_data
    }
    with db.cursor(conn) as cursor:
        return tuple(
            dict(data_row) for data_row in
            resource_data_function[
                resource.resource_category.resource_category_key](
                    cursor, resource.resource_id, offset, limit))

def attach_resource_data(cursor: db.DbCursor, resource: Resource) -> Resource:
    """Attach the linked data to the resource"""
    resource_data_function = {
        "mrna": mrna_resource_data,
        "genotype": genotype_resource_data,
        "phenotype": phenotype_resource_data
    }
    category = resource.resource_category
    data_rows = tuple(
        dict(data_row) for data_row in
        resource_data_function[category.resource_category_key](
            cursor, resource.resource_id))
    return Resource(
        resource.group, resource.resource_id, resource.resource_name,
        resource.resource_category, resource.public, data_rows)

def resource_by_id(
        conn: db.DbConnection, user: User, resource_id: UUID) -> Resource:
    """Retrieve a resource by its ID."""
    if not authorised_for(
            conn, user, ("group:resource:view-resource",),
            (resource_id,))[resource_id]:
        raise AuthorisationError(
            "You are not authorised to access resource with id "
            f"'{resource_id}'.")

    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resources WHERE resource_id=:id",
                       {"id": str(resource_id)})
        row = cursor.fetchone()
        if row:
            return Resource(
                group_by_id(conn, UUID(row["group_id"])),
                UUID(row["resource_id"]), row["resource_name"],
                resource_category_by_id(conn, row["resource_category_id"]),
                bool(int(row["public"])))

    raise NotFoundError(f"Could not find a resource with id '{resource_id}'")

def link_data_to_resource(
        conn: db.DbConnection, user: User, resource_id: UUID, dataset_type: str,
        data_link_id: UUID) -> dict:
    """Link data to resource."""
    if not authorised_for(
            conn, user, ("group:resource:edit-resource",),
            (resource_id,))[resource_id]:
        raise AuthorisationError(
            "You are not authorised to link data to resource with id "
            f"{resource_id}")

    resource = with_db_connection(partial(
        resource_by_id, user=user, resource_id=resource_id))
    return {
        "mrna": mrna_link_data_to_resource,
        "genotype": genotype_link_data_to_resource,
        "phenotype": phenotype_link_data_to_resource,
    }[dataset_type.lower()](conn, resource, data_link_id)

def unlink_data_from_resource(
        conn: db.DbConnection, user: User, resource_id: UUID, data_link_id: UUID):
    """Unlink data from resource."""
    if not authorised_for(
            conn, user, ("group:resource:edit-resource",),
            (resource_id,))[resource_id]:
        raise AuthorisationError(
            "You are not authorised to link data to resource with id "
            f"{resource_id}")

    resource = with_db_connection(partial(
        resource_by_id, user=user, resource_id=resource_id))
    dataset_type = resource.resource_category.resource_category_key
    return {
        "mrna": mrna_unlink_data_from_resource,
        "genotype": genotype_unlink_data_from_resource,
        "phenotype": phenotype_unlink_data_from_resource,
    }[dataset_type.lower()](conn, resource, data_link_id)

def organise_resources_by_category(resources: Sequence[Resource]) -> dict[
        ResourceCategory, tuple[Resource]]:
    """Organise the `resources` by their categories."""
    def __organise__(accumulator, resource):
        category = resource.resource_category
        return {
            **accumulator,
            category: accumulator.get(category, tuple()) + (resource,)
        }
    return reduce(__organise__, resources, {})

def attach_resources_data(
        conn: db.DbConnection, resources: Sequence[Resource]) -> Sequence[
            Resource]:
    """Attach linked data for each resource in `resources`"""
    resource_data_function = {
        "mrna": mrna_attach_resources_data,
        "genotype": genotype_attach_resources_data,
        "phenotype": phenotype_attach_resources_data
    }
    organised = organise_resources_by_category(resources)
    with db.cursor(conn) as cursor:
        return tuple(
            resource for categories in
            (resource_data_function[category.resource_category_key](
                cursor, rscs)
             for category, rscs in organised.items())
            for resource in categories)

@authorised_p(
    ("group:user:assign-role",),
    "You cannot assign roles to users for this group.",
    oauth2_scope="profile group role resource")
def assign_resource_user(
        conn: db.DbConnection, resource: Resource, user: User,
        role: GroupRole) -> dict:
    """Assign `role` to `user` for the specific `resource`."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO "
            "group_user_roles_on_resources(group_id, user_id, role_id, "
            "resource_id) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT (group_id, user_id, role_id, resource_id) "
            "DO NOTHING",
            (str(resource.group.group_id), str(user.user_id),
             str(role.role.role_id), str(resource.resource_id)))
        return {
            "resource": dictify(resource),
            "user": dictify(user),
            "role": dictify(role),
            "description": (
                f"The user '{user.name}'({user.email}) was assigned the "
                f"'{role.role.role_name}' role on resource with ID "
                f"'{resource.resource_id}'.")}

@authorised_p(
    ("group:user:assign-role",),
    "You cannot assign roles to users for this group.",
    oauth2_scope="profile group role resource")
def unassign_resource_user(
        conn: db.DbConnection, resource: Resource, user: User,
        role: GroupRole) -> dict:
    """Assign `role` to `user` for the specific `resource`."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "DELETE FROM group_user_roles_on_resources "
            "WHERE group_id=? AND user_id=? AND role_id=? AND resource_id=?",
            (str(resource.group.group_id), str(user.user_id),
             str(role.role.role_id), str(resource.resource_id)))
        return {
            "resource": dictify(resource),
            "user": dictify(user),
            "role": dictify(role),
            "description": (
                f"The user '{user.name}'({user.email}) had the "
                f"'{role.role.role_name}' role on resource with ID "
                f"'{resource.resource_id}' taken away.")}

def save_resource(
        conn: db.DbConnection, user: User, resource: Resource) -> Resource:
    """Update an existing resource."""
    resource_id = resource.resource_id
    authorised = authorised_for(
        conn, user, ("group:resource:edit-resource",), (resource_id,))
    if authorised[resource_id]:
        with db.cursor(conn) as cursor:
            cursor.execute(
                "UPDATE resources SET "
                "resource_name=:resource_name, "
                "public=:public "
                "WHERE group_id=:group_id "
                "AND resource_id=:resource_id",
                {
                    "resource_name": resource.resource_name,
                    "public": 1 if resource.public else 0,
                    "group_id": str(resource.group.group_id),
                    "resource_id": str(resource.resource_id)
                })
            return resource

    raise AuthorisationError(
        "You do not have the appropriate privileges to edit this resource.")

def resource_group(conn: db.DbConnection, resource: Resource) -> Group:
    """Return the group that owns the resource."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT g.* FROM resource_ownership AS ro "
            "INNER JOIN groups AS g ON ro.group_id=g.group_id "
            "WHERE ro.resource_id=?",
            (str(resource.resource_id),))
        row = cursor.fetchone()
        if row:
            return Group(
                UUID(row["group_id"]),
                row["group_name"],
                json.loads(row["group_metadata"]))

    raise MissingGroupError("Resource has no 'owning' group.")
