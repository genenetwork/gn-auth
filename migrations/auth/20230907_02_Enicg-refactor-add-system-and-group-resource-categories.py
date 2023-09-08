"""
refactor: add 'system' and 'group' resource categories
"""

from yoyo import step

__depends__ = {'20230907_01_pjnxz-refactor-add-resource-ownership-table'}

steps = [
    step(
        """
        INSERT INTO resource_categories VALUES
          ('aa3d787f-af6a-44fa-9b0b-c82d40e54ad2',
           'system',
           'The overall system.',
           '{"default-access-level": "public-read"}'),
          ('1e0f70ee-add5-4358-8c6c-43de77fa4cce',
           'group',
           'A group resource.',
           '{}')
        """,
        """
        DELETE FROM resource_categories
        WHERE resource_category_id IN (
          'aa3d787f-af6a-44fa-9b0b-c82d40e54ad2',
          '1e0f70ee-add5-4358-8c6c-43de77fa4cce'
        )
        """)
]
