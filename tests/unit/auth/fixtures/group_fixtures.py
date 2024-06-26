"""Fixtures and utilities for group-related tests"""
import uuid

import pytest

from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.authorisation.resources.groups import Group, GroupRole
from gn_auth.auth.authorisation.resources import Resource, ResourceCategory

from .role_fixtures import RESOURCE_EDITOR_ROLE, RESOURCE_READER_ROLE

TEST_GROUP_01 = Group(uuid.UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"),
                      "TheTestGroup", {})
TEST_GROUP_02 = Group(uuid.UUID("e37d59d7-c05e-4d67-b479-81e627d8d634"),
                      "AnotherTestGroup", {})
TEST_GROUPS = (TEST_GROUP_01, TEST_GROUP_02)

SYSTEM_CATEGORY = ResourceCategory(
    uuid.UUID("aa3d787f-af6a-44fa-9b0b-c82d40e54ad2"),
    "system",
    "The overall system.")
SYSTEM_RESOURCE = Resource(
    uuid.UUID("0248b289-b277-4eaa-8c94-88a434d14b6e"),
    "GeneNetwork System",
    SYSTEM_CATEGORY,
    True)

GROUP_CATEGORY = ResourceCategory(
    uuid.UUID("1e0f70ee-add5-4358-8c6c-43de77fa4cce"),
    "group",
    "A group resource.")
GROUPS_AS_RESOURCES = tuple({
    "group_id": str(group.group_id),
    "resource_id": res_id,
    "resource_name": group.group_name,
    "category_id": str(GROUP_CATEGORY.resource_category_id),
    "public": "0"
} for res_id, group in zip(
    ("38d1807d-105f-44a7-8327-7e2d973b6d8d",
     "89458ef6-e090-4b53-8c2c-59eaf2785f11"),
    TEST_GROUPS))
GROUP_RESOURCES = tuple(
    Resource(uuid.UUID(row["resource_id"]),
             row["resource_name"],
             GROUP_CATEGORY,
             False)
    for row in GROUPS_AS_RESOURCES)

TEST_RESOURCES_GROUP_01 = (
    Resource(uuid.UUID("26ad1668-29f5-439d-b905-84d551f85955"),
             "ResourceG01R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             True),
    Resource(uuid.UUID("2130aec0-fefd-434d-92fd-9ca342348b2d"),
             "ResourceG01R02",
             ResourceCategory(uuid.UUID("548d684b-d4d1-46fb-a6d3-51a56b7da1b3"),
                              "phenotype", "Phenotype (Publish) Dataset"),
             False),
    Resource(uuid.UUID("e9a1184a-e8b4-49fb-b713-8d9cbeea5b83"),
             "ResourceG01R03",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             False))

TEST_RESOURCES_GROUP_02 = (
    Resource(uuid.UUID("14496a1c-c234-49a2-978c-8859ea274054"),
             "ResourceG02R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             False),
    Resource(uuid.UUID("04ad9e09-94ea-4390-8a02-11f92999806b"),
             "ResourceG02R02",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             True))

TEST_RESOURCES = TEST_RESOURCES_GROUP_01 + TEST_RESOURCES_GROUP_02
TEST_RESOURCES_PUBLIC = (
    SYSTEM_RESOURCE, TEST_RESOURCES_GROUP_01[0], TEST_RESOURCES_GROUP_02[1])

def __gtuple__(cursor):
    return tuple(dict(row) for row in cursor.fetchall())

@pytest.fixture(scope="function")
def fxtr_group(conn_after_auth_migrations):# pylint: disable=[redefined-outer-name]
    """Fixture: setup a test group."""
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(
            "INSERT INTO groups(group_id, group_name) VALUES (?, ?)",
            tuple(
                (str(group.group_id), group.group_name)
                for group in TEST_GROUPS))

        cursor.executemany(
            "INSERT INTO resources "
            "VALUES(:resource_id, :resource_name, :category_id, :public)",
            GROUPS_AS_RESOURCES)

        cursor.executemany(
            "INSERT INTO group_resources(resource_id, group_id) "
            "VALUES(:resource_id, :group_id)",
            GROUPS_AS_RESOURCES)

    yield (conn_after_auth_migrations, TEST_GROUPS[0])

    with db.cursor(conn_after_auth_migrations) as cursor:
        resource_id_params = tuple(
            (str(res["resource_id"]),) for res in GROUPS_AS_RESOURCES)
        cursor.executemany("DELETE FROM group_resources WHERE resource_id=?",
                           resource_id_params)
        cursor.executemany("DELETE FROM resources WHERE resource_id=?",
                           resource_id_params)
        cursor.executemany(
            "DELETE FROM groups WHERE group_id=?",
            ((str(group.group_id),) for group in TEST_GROUPS))

@pytest.fixture(scope="function")
def fxtr_users_in_group(fxtr_group, fxtr_users):# pylint: disable=[redefined-outer-name, unused-argument]
    """Link the users to the groups."""
    conn, all_users = fxtr_users
    users = tuple(
        user for user in all_users if user.email not in ("unaff@iliated.user",))
    query_params = tuple(
        (str(TEST_GROUP_01.group_id), str(user.user_id)) for user in users)
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO group_users(group_id, user_id) VALUES (?, ?)",
            query_params)

    yield (conn, TEST_GROUP_01, users)

    with db.cursor(conn) as cursor:
        cursor.executemany(
            "DELETE FROM group_users WHERE group_id=? AND user_id=?",
            query_params)

@pytest.fixture(scope="function")
def fxtr_group_roles(fxtr_group, fxtr_roles):# pylint: disable=[redefined-outer-name,unused-argument]
    """Link roles to group"""
    group_roles = (
        GroupRole(uuid.UUID("9c25efb2-b477-4918-a95c-9914770cbf4d"),
                  TEST_GROUP_01, RESOURCE_EDITOR_ROLE),
        GroupRole(uuid.UUID("82aed039-fe2f-408c-ab1e-81cd1ba96630"),
                  TEST_GROUP_02, RESOURCE_READER_ROLE))
    conn, groups = fxtr_group
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO group_roles VALUES (?, ?, ?)",
            ((str(role.group_role_id), str(role.group.group_id),
              str(role.role.role_id))
             for role in group_roles))

    yield conn, groups, group_roles

    with db.cursor(conn) as cursor:
        cursor.executemany(
            ("DELETE FROM group_roles "
             "WHERE group_role_id=? AND group_id=? AND role_id=?"),
            ((str(role.group_role_id), str(role.group.group_id),
              str(role.role.role_id))
             for role in group_roles))

@pytest.fixture(scope="function")
def fxtr_group_user_roles(fxtr_resources, fxtr_group_roles, fxtr_users_in_group):#pylint: disable=[redefined-outer-name,unused-argument]
    """Assign roles to users."""
    conn, _groups, group_roles = fxtr_group_roles
    _conn, group_resources = fxtr_resources
    _conn, _group, group_users = fxtr_users_in_group
    users = tuple(user for user in group_users if user.email
                  not in ("unaff@iliated.user", "group@lead.er"))
    users_roles_resources = (
        (user, RESOURCE_EDITOR_ROLE, TEST_RESOURCES_GROUP_01[1])
        for user in users if user.email == "group@mem.ber01")
    with db.cursor(conn) as cursor:
        params = tuple({
            "user_id": str(user.user_id),
            "role_id": str(role.role_id),
            "resource_id": str(resource.resource_id)
        } for user, role, resource in users_roles_resources)
        cursor.executemany(
            ("INSERT INTO user_roles "
             "VALUES (:user_id, :role_id, :resource_id)"),
            params)

    yield conn, group_users, group_roles, group_resources

    with db.cursor(conn) as cursor:
        cursor.executemany(
            ("DELETE FROM user_roles WHERE "
             "user_id=:user_id AND role_id=:role_id AND "
             "resource_id=:resource_id"),
            params)
