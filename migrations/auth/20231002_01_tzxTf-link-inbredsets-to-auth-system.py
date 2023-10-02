"""
link InbredSets to auth system
"""

from yoyo import step

__depends__ = {'20230925_01_TWJuR-add-new-public-view-role', '__init__'}

steps = [
    step(
        """
        INSERT INTO resource_categories
        (
          resource_category_id,
          resource_category_key,
          resource_category_description,
          resource_meta
        )
        VALUES
        (
          'b3654600-4ab0-4745-8292-5849b34173a7',
          'inbredset-group',
          'A resource that controls access to a particular InbredSet group',
          '{"default-access-level":"public-read"}'
        )
        """,
        """
        DELETE FROM resource_categories WHERE
          resource_category_id = 'b3654600-4ab0-4745-8292-5849b34173a7'
        """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS linked_inbredset_groups
        -- Link InbredSet groups in MariaDB to auth system
        (
          data_link_id TEXT NOT NULL PRIMARY KEY, -- A new ID for the auth system
          SpeciesId TEXT NOT NULL, -- Species ID in MariaDB
          InbredSetId TEXT NOT NULL, -- The InbredSet ID in MariaDB
          InbredSetName TEXT NOT NULL, -- The InbredSet group's name in MariaDB
          InbredSetFullName TEXT NOT NULL, -- The InbredSet group's full name in MariaDB
          UNIQUE(SpeciesId, InbredSetId)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS linked_inbredset_groups"),
    step(
        """
        CREATE TABLE IF NOT EXISTS inbredset_group_resources
        -- Link the InbredSet data to a specific resource
        (
          resource_id TEXT NOT NULL, -- Linked resource: one-to-one
          data_link_id TEXT NOT NULL,
          PRIMARY KEY(resource_id, data_link_id),
          UNIQUE(resource_id), -- resource is linked to only one InbredSet
          UNIQUE(data_link_id), -- InbredSet is linked to only one resource
          FOREIGN KEY(resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY(data_link_id)
            REFERENCES linked_inbredset_groups(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS inbredset_group_resources"),
    step(
        """
        INSERT INTO privileges(privilege_id, privilege_description) VALUES
        ('system:inbredset:create-case-attribute', 'Create a new case attribute for an InbredSet group.'),
        ('system:inbredset:delete-case-attribute', 'Delete an existing case-attribute from an InbredSet group'),
        ('system:inbredset:edit-case-attribute', 'Edit the values of case-attributes of an InbredSet group'),
        ('system:inbredset:view-case-attribute', 'View the case-attributes of an InbredSet group'),
        ('system:inbredset:apply-case-attribute-edit', 'Apply an edit to case-attributes performed by another user for an InbredSet group'),
        ('system:inbredset:reject-case-attribute-edit', 'Reject an edit to case-attributes performed by another user for an InbredSet group')
        """,
        """
        DELETE FROM privileges WHERE privilege_id IN (
          'system:inbredset:create-case-attribute',
          'system:inbredset:delete-case-attribute',
          'system:inbredset:edit-case-attribute',
          'system:inbredset:view-case-attribute',
          'system:inbredset:apply-case-attribute-edit',
          'system:inbredset:reject-case-attribute-edit')
        """)
]
