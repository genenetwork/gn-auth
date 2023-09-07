"""
refactor: add resource_ownership table
"""

from yoyo import step

__depends__ = {'20230410_02_WZqSf-create-mrna-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS resource_ownership(
        -- This table links resources to groups, where relevant
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          PRIMARY KEY(group_id, resource_id),
          FOREIGN KEY(group_id)
            REFERENCES groups(group_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY(resource_id)
            REFERENCES resources(resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS resource_ownership"),
    step(# Copy over data
        """
        INSERT INTO resource_ownership
        SELECT group_id, resource_id FROM resources
        """
    )
]
