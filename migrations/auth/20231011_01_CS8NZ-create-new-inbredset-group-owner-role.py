"""
Create new 'inbredset-group-owner' role
"""

from yoyo import step

__depends__ = {'20231002_01_tzxTf-link-inbredsets-to-auth-system'}

steps = [
    step(
        """
        INSERT INTO roles(role_id, role_name, user_editable)
        VALUES('bde1c08b-b067-4d56-8353-462fc5928c32', 'inbredset-group-owner', 0)
        """,
        """
        DELETE FROM roles WHERE role_id='bde1c08b-b067-4d56-8353-462fc5928c32'
        """),
    step(
        """
        INSERT INTO role_privileges(role_id, privilege_id)
        VALUES
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:apply-case-attribute-edit'),
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:create-case-attribute'),
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:delete-case-attribute'),
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:edit-case-attribute'),
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:reject-case-attribute-edit'),
          ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:view-case-attribute')
        """,
        """
        DELETE FROM role_privileges
        WHERE (role_id, privilege_id)
        IN
          (('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:apply-case-attribute-edit'),
           ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:create-case-attribute'),
           ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:delete-case-attribute'),
           ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:edit-case-attribute'),
           ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:reject-case-attribute-edit'),
           ('bde1c08b-b067-4d56-8353-462fc5928c32', 'system:inbredset:view-case-attribute'))
        """)
]
