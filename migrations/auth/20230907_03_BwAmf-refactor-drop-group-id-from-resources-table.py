"""
refactor: drop 'group_id' from 'resources' table.
"""

import sqlite3
from yoyo import step

__depends__ = {'20230907_02_Enicg-refactor-add-system-and-group-resource-categories'}

def drop_group_id_from_group_user_roles_on_resources(conn):
    conn.execute(
        "ALTER TABLE group_user_roles_on_resources "
        "RENAME TO group_user_roles_on_resources_bkp")
    conn.execute(
        """
        CREATE TABLE group_user_roles_on_resources (
          group_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          role_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          PRIMARY KEY (group_id, user_id, role_id, resource_id),
          FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (group_id, role_id)
            REFERENCES group_roles(group_id, role_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO group_user_roles_on_resources "
        "(group_id, user_id, role_id, resource_id)"
        "SELECT group_id, user_id, role_id, resource_id "
        "FROM group_user_roles_on_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS group_user_roles_on_resources_bkp")

def drop_group_id_from_mrna_resources(conn):
    conn.execute("ALTER TABLE mrna_resources RENAME TO mrna_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mrna_resources
        -- Link mRNA data to specific resource
        (
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id) REFERENCES linked_mrna_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO mrna_resources "
        "SELECT resource_id, data_link_id FROM mrna_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS mrna_resources_bkp")

def drop_group_id_from_genotype_resources(conn):
    conn.execute(
        "ALTER TABLE genotype_resources RENAME TO genotype_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS genotype_resources
        -- Link genotype data to specific resource
        (
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id)
            REFERENCES linked_genotype_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO genotype_resources "
        "SELECT resource_id, data_link_id FROM genotype_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS genotype_resources_bkp")

def drop_group_id_from_phenotype_resources(conn):
    conn.execute(
        "ALTER TABLE phenotype_resources RENAME TO phenotype_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phenotype_resources
        -- Link phenotype data to specific resources
        (
          resource_id TEXT NOT NULL, -- A resource can have multiple data items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY(resource_id, data_link_id),
          UNIQUE (data_link_id), -- ensure data is linked to only one resource
          FOREIGN KEY (resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id)
            REFERENCES linked_phenotype_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO phenotype_resources "
        "SELECT resource_id, data_link_id FROM phenotype_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS phenotype_resources_bkp")

def drop_group_id_from_resources_table(conn):
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resources_new(
          resource_id TEXT NOT NULL,
          resource_name TEXT NOT NULL UNIQUE,
          resource_category_id TEXT NOT NULL,
          public INTEGER NOT NULL DEFAULT 0 CHECK (public=0 or public=1),
          PRIMARY KEY(resource_id),
          FOREIGN KEY(resource_category_id)
            REFERENCES resource_categories(resource_category_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO resources_new "
        "SELECT resource_id, resource_name, resource_category_id, public "
        "FROM resources")
    conn.execute("DROP TABLE IF EXISTS resources")
    conn.execute("ALTER TABLE resources_new RENAME TO resources")

    drop_group_id_from_mrna_resources(conn)
    drop_group_id_from_genotype_resources(conn)
    drop_group_id_from_phenotype_resources(conn)
    drop_group_id_from_group_user_roles_on_resources(conn)

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

def restore_group_id_from_group_user_roles_on_resources(conn):
    conn.execute(
        "ALTER TABLE group_user_roles_on_resources "
        "RENAME TO group_user_roles_on_resources_bkp")
    conn.execute(
        """
        CREATE TABLE group_user_roles_on_resources (
          group_id TEXT NOT NULL,
          user_id TEXT NOT NULL,
          role_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          PRIMARY KEY (group_id, user_id, role_id, resource_id),
          FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (group_id, role_id)
            REFERENCES group_roles(group_id, role_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    conn.execute(
        "INSERT INTO group_user_roles_on_resources "
        "(group_id, user_id, role_id, resource_id)"
        "SELECT group_id, user_id, role_id, resource_id "
        "FROM group_user_roles_on_resources_bkp")
    conn.execute("DROP TABLE IF EXISTS group_user_roles_on_resources_bkp")

def restore_group_id_from_mrna_resources(conn, resource_group_map):
    conn.execute("ALTER TABLE mrna_resources RENAME TO mrna_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mrna_resources
        -- Link mRNA data to specific resource
        (
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id) REFERENCES linked_mrna_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mrna_resources_bkp")
    resources = tuple({
        "group_id": resource_group_map[row["resource_id"]],
        **dict(row)
    } for row in cursor.fetchall())
    cursor.executemany(
        "INSERT INTO mrna_resources(group_id, resource_id, data_link_id) "
        "VALUES(:group_id, :resource_id, :data_link_id)",
        resources)
    conn.execute("DROP TABLE IF EXISTS mrna_resources_bkp")

def restore_group_id_from_genotype_resources(conn, resource_group_map):
    conn.execute(
        "ALTER TABLE genotype_resources RENAME TO genotype_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS genotype_resources
        -- Link genotype data to specific resource
        (
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (group_id, resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id)
            REFERENCES linked_genotype_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM genotype_resources_bkp")
    resources = tuple({
        "group_id": resource_group_map[row["resource_id"]],
        **dict(row)
    } for row in cursor.fetchall())
    cursor.executemany(
        "INSERT INTO genotype_resources(group_id, resource_id, data_link_id) "
        "VALUES(:group_id, :resource_id, :data_link_id)",
        resources)
    conn.execute("DROP TABLE IF EXISTS genotype_resources_bkp")

def restore_group_id_from_phenotype_resources(conn, resource_group_map):
    conn.execute(
        "ALTER TABLE phenotype_resources RENAME TO phenotype_resources_bkp")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phenotype_resources
        -- Link phenotype data to specific resources
        (
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL, -- A resource can have multiple data items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY(group_id, resource_id, data_link_id),
          UNIQUE (data_link_id), -- ensure data is linked to only one resource
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id)
            REFERENCES linked_phenotype_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phenotype_resources_bkp")
    resources = tuple({
        "group_id": resource_group_map[row["resource_id"]],
        **dict(row)
    } for row in cursor.fetchall())
    cursor.executemany(
        "INSERT INTO phenotype_resources(group_id, resource_id, data_link_id) "
        "VALUES(:group_id, :resource_id, :data_link_id)",
        resources)
    conn.execute("DROP TABLE IF EXISTS phenotype_resources_bkp")

def restore_group_id_to_resources_table(conn):
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")

    cursor = conn.cursor()
    cursor.execute("ALTER TABLE resources RENAME TO resources_bkp")
    cursor.execute(
        "SELECT r.*, ro.group_id FROM resources_bkp AS r "
        "INNER JOIN resource_ownership AS ro "
        "ON r.resource_id=ro.resource_id")
    group_resources = tuple(dict(row) for row in cursor.fetchall())
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resources(
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          resource_name TEXT NOT NULL UNIQUE,
          resource_category_id TEXT NOT NULL,
          public INTEGER NOT NULL DEFAULT 0 CHECK (public=0 or public=1),
          PRIMARY KEY(group_id, resource_id),
          FOREIGN KEY(group_id)
            REFERENCES groups(group_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY(resource_category_id)
            REFERENCES resource_categories(resource_category_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
    cursor.executemany(
        "INSERT INTO resources"
        "(group_id, resource_id, resource_name, resource_category_id)"
        "VALUES "
        "(:group_id, :resource_id, :resource_name, :resource_category_id)",
        group_resources)
    cursor.execute("DROP TABLE IF EXISTS resources_bkp")

    resource_group_map = {
        res["resource_id"]: res["group_id"]
        for res in group_resources
    }
    restore_group_id_from_group_user_roles_on_resources(conn)
    restore_group_id_from_mrna_resources(conn, resource_group_map)
    restore_group_id_from_genotype_resources(conn, resource_group_map)
    restore_group_id_from_phenotype_resources(conn, resource_group_map)

    conn.execute("PRAGMA foreign_key_check")
    conn.execute("PRAGMA foreign_keys = ON")

steps = [
    step(
        drop_group_id_from_resources_table, restore_group_id_to_resources_table)
]
