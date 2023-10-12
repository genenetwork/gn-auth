"""
Link any unlinked InbredSet groups.
"""
import sys
import uuid
from pathlib import Path

import click

import gn_auth.auth.db.sqlite3 as authdb

from gn_auth.auth.db import mariadb as biodb

from scripts.migrate_existing_data import sys_admins, admin_group, select_sys_admin

def linked_inbredsets(conn):
    """Fetch all inbredset groups that are linked to the auth system."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT SpeciesId, InbredSetId FROM linked_inbredset_groups")
        return tuple((row["SpeciesId"], row["InbredSetId"])
                     for row in cursor.fetchall())

def unlinked_inbredsets(conn, linked):
    """Fetch any inbredset groups that are not linked to the auth system."""
    with conn.cursor() as cursor:
        where_clause = ""
        query = "SELECT SpeciesId, InbredSetId, InbredSetName, FullName FROM InbredSet"
        if len(linked) > 0:
            pholders = ["(%s, %s)"] * len(linked)
            where_clause = (f" WHERE (SpeciesId, InbredSetId) "
                            f"NOT IN ({pholders})")
            cursor.execute(query + where_clause,
                           tuple(arg for sublist in linked for arg in sublist))
            return cursor.fetchall()

        cursor.execute(query)
        return cursor.fetchall()

def link_unlinked(conn, unlinked):
    """Link the unlinked inbredset groups to the auth system."""
    params = tuple((str(uuid.uuid4()),) + row for row in unlinked)
    with authdb.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO linked_inbredset_groups VALUES (?, ?, ?, ?, ?)",
            params)

    return params

def build_resources(conn, new_linked):
    """Build resources for newly linked inbredsets."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT resource_category_id FROM resource_categories "
            "WHERE resource_category_key='inbredset-group'")
        category_id = cursor.fetchone()["resource_category_id"]
        resources = tuple({
            "resource_id": str(uuid.uuid4()),
            "resource_name": f"InbredSet: {name}",
            "resource_category_id": category_id,
            "public": 1,
            "data_link_id": datalinkid
        } for datalinkid, _sid, _isetid, name, _name in new_linked)
        cursor.executemany(
            "INSERT INTO resources VALUES "
            "(:resource_id, :resource_name, :resource_category_id, :public)",
            resources)
        cursor.executemany(
            "INSERT INTO inbredset_group_resources VALUES "
            "(:resource_id, :data_link_id)",
            resources)
        return resources

def own_resources(conn, group, resources):
    """Link new resources to admin group."""
    with authdb.cursor(conn) as cursor:
        params = tuple({
            "group_id": str(group.group_id),
            **resource
        } for resource in resources)
        cursor.executemany(
            "INSERT INTO resource_ownership VALUES "
            "(:group_id, :resource_id)",
            params)
        return params

def assign_role_for_admin(conn, user, resources):
    """Assign basic role to admin on the inbredset-group resources."""
    with authdb.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM roles WHERE role_name='inbredset-group-owner'")
        role_id = cursor.fetchone()["role_id"]
        cursor.executemany(
            "INSERT INTO user_roles(user_id, role_id, resource_id) "
            "VALUES (:user_id, :role_id, :resource_id)",
            tuple({**rsc, "user_id": str(user.user_id), "role_id": role_id}
                  for rsc in resources))

@click.command()
@click.argument("authdbpath") # "Path to the Auth(entic|oris)ation database"
@click.argument("mysqldburi") # "URI to the MySQL database with the biology data"
def run(authdbpath, mysqldburi):
    """Setup command-line arguments."""
    if not Path(authdbpath).exists():
        print(
            f"ERROR: Auth db file `{authdbpath}` does not exist.",
            file=sys.stderr)
        sys.exit(2)

    with (authdb.connection(authdbpath) as authconn,
          biodb.database_connection(mysqldburi) as bioconn):
        admin = select_sys_admin(sys_admins(authconn))
        unlinked = assign_role_for_admin(authconn, admin, own_resources(
            authconn,
            admin_group(authconn, admin),
            build_resources(
                authconn, link_unlinked(
                    authconn,
                    unlinked_inbredsets(bioconn, linked_inbredsets(authconn))))))

if __name__ == "__main__":
    run() # pylint: disable=[no-value-for-parameter]
