"""The views/routes for the resources package"""
import uuid
import json
import sqlite3

from dataclasses import asdict
from functools import reduce

from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.db.sqlite3 import with_db_connection

from gn_auth.auth.authorisation.roles import Role
from gn_auth.auth.authorisation.errors import InvalidData, InconsistencyError, AuthorisationError

from gn_auth.auth.authentication.oauth2.resource_server import require_oauth
from gn_auth.auth.authentication.users import User, user_by_id, user_by_email

from .checks import authorised_for
from .models import (
    Resource, resource_data, resource_by_id, public_resources,
    resource_categories, assign_resource_user, link_data_to_resource,
    unassign_resource_user, resource_category_by_id, user_roles_on_resources,
    unlink_data_from_resource, create_resource as _create_resource,
    get_resource_id)
from .groups.models import Group, resource_owner, group_role_by_id

resources = Blueprint("resources", __name__)

@resources.route("/categories", methods=["GET"])
@require_oauth("profile group resource")
def list_resource_categories() -> Response:
    """Retrieve all resource categories"""
    db_uri = app.config["AUTH_DB"]
    with db.connection(db_uri) as conn:
        return jsonify(tuple(
            asdict(category) for category in resource_categories(conn)))

@resources.route("/create", methods=["POST"])
@require_oauth("profile group resource")
def create_resource() -> Response:
    """Create a new resource"""
    with require_oauth.acquire("profile group resource") as the_token:
        form = request.form
        resource_name = form.get("resource_name")
        resource_category_id = uuid.UUID(form.get("resource_category"))
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            try:
                resource = _create_resource(
                    conn,
                    resource_name,
                    resource_category_by_id(conn, resource_category_id),
                    the_token.user,
                    (form.get("public") == "on"))
                return jsonify(asdict(resource))
            except sqlite3.IntegrityError as sql3ie:
                if sql3ie.args[0] == ("UNIQUE constraint failed: "
                                      "resources.resource_name"):
                    raise InconsistencyError(
                        "You cannot have duplicate resource names.") from sql3ie
                app.logger.debug(
                    f"{type(sql3ie)=}: {sql3ie=}")
                raise

@resources.route("/view/<uuid:resource_id>")
@require_oauth("profile group resource")
def view_resource(resource_id: uuid.UUID) -> Response:
    """View a particular resource's details."""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            return jsonify(
                asdict(
                    resource_by_id(conn, the_token.user, resource_id)
                )
            )

def __safe_get_requests_page__(key: str = "page") -> int:
    """Get the results page if it exists or default to the first page."""
    try:
        return abs(int(request.args.get(key, "1"), base=10))
    except ValueError as _valerr:
        return 1

def __safe_get_requests_count__(key: str = "count_per_page") -> int:
    """Get the results page if it exists or default to the first page."""
    try:
        count = request.args.get(key, "0")
        if count != 0:
            return abs(int(count, base=10))
        return 0
    except ValueError as _valerr:
        return 0

@resources.route("/view/<uuid:resource_id>/data")
@require_oauth("profile group resource")
def view_resource_data(resource_id: uuid.UUID) -> Response:
    """Retrieve a particular resource's data."""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        count_per_page = __safe_get_requests_count__("count_per_page")
        offset = (__safe_get_requests_page__("page") - 1)
        with db.connection(db_uri) as conn:
            resource = resource_by_id(conn, the_token.user, resource_id)
            return jsonify(resource_data(
                conn,
                resource,
                ((offset * count_per_page) if bool(count_per_page) else offset),
                count_per_page))

@resources.route("/data/link", methods=["POST"])
@require_oauth("profile group resource")
def link_data():
    """Link group data to a specific resource."""
    try:
        form = request.form
        assert "resource_id" in form, "Resource ID not provided."
        assert "data_link_id" in form, "Data Link ID not provided."
        assert "dataset_type" in form, "Dataset type not specified"
        assert form["dataset_type"].lower() in (
            "mrna", "genotype", "phenotype"), "Invalid dataset type provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __link__(conn: db.DbConnection):
                return link_data_to_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    form["dataset_type"], uuid.UUID(form["data_link_id"]))

            return jsonify(with_db_connection(__link__))
    except AssertionError as aserr:
        raise InvalidData(aserr.args[0]) from aserr



@resources.route("/data/unlink", methods=["POST"])
@require_oauth("profile group resource")
def unlink_data():
    """Unlink data bound to a specific resource."""
    try:
        form = request.form
        assert "resource_id" in form, "Resource ID not provided."
        assert "data_link_id" in form, "Data Link ID not provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __unlink__(conn: db.DbConnection):
                return unlink_data_from_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    uuid.UUID(form["data_link_id"]))
            return jsonify(with_db_connection(__unlink__))
    except AssertionError as aserr:
        raise InvalidData(aserr.args[0]) from aserr

@resources.route("<uuid:resource_id>/user/list", methods=["GET"])
@require_oauth("profile group resource")
def resource_users(resource_id: uuid.UUID):
    """Retrieve all users with access to the given resource."""
    with require_oauth.acquire("profile group resource") as the_token:
        def __the_users__(conn: db.DbConnection):
            authorised = authorised_for(
                conn, the_token.user,
                ("group:resource:edit-resource","group:resource:view-resource"),
                (resource_id,))
            if authorised.get(resource_id, False):
                with db.cursor(conn) as cursor:
                    def __organise_users_n_roles__(users_n_roles, row):
                        user_id = uuid.UUID(row["user_id"])
                        user = users_n_roles.get(user_id, {}).get(
                            "user", User(user_id, row["email"], row["name"]))
                        role = Role(
                            uuid.UUID(row["role_id"]), row["role_name"],
                            bool(int(row["user_editable"])), tuple())
                        return {
                            **users_n_roles,
                            user_id: {
                                "user": user,
                                "user_group": Group(
                                    uuid.UUID(row["group_id"]), row["group_name"],
                                    json.loads(row["group_metadata"])),
                                "roles": users_n_roles.get(
                                    user_id, {}).get("roles", tuple()) + (role,)
                            }
                        }
                    cursor.execute(
                        "SELECT g.*, u.*, r.* "
                        "FROM groups AS g INNER JOIN group_users AS gu "
                        "ON g.group_id=gu.group_id INNER JOIN users AS u "
                        "ON gu.user_id=u.user_id INNER JOIN user_roles AS ur "
                        "ON u.user_id=ur.user_id INNER JOIN roles AS r "
                        "ON ur.role_id=r.role_id "
                        "WHERE ur.resource_id=?",
                        (str(resource_id),))
                    return reduce(__organise_users_n_roles__, cursor.fetchall(), {})
            raise AuthorisationError(
                "You do not have sufficient privileges to view the resource "
                "users.")
        results = (
            {
                "user": asdict(row["user"]),
                "user_group": asdict(row["user_group"]),
                "roles": tuple(asdict(role) for role in row["roles"])
            } for row in (
                user_row for user_id, user_row
                in with_db_connection(__the_users__).items()))
        return jsonify(tuple(results))

@resources.route("<uuid:resource_id>/user/assign", methods=["POST"])
@require_oauth("profile group resource role")
def assign_role_to_user(resource_id: uuid.UUID) -> Response:
    """Assign a role on the specified resource to a user."""
    with require_oauth.acquire("profile group resource role") as the_token:
        try:
            form = request.form
            group_role_id = form.get("group_role_id", "")
            user_email = form.get("user_email", "")
            assert bool(group_role_id), "The role must be provided."
            assert bool(user_email), "The user email must be provided."

            def __assign__(conn: db.DbConnection) -> dict:
                resource = resource_by_id(conn, the_token.user, resource_id)
                user = user_by_email(conn, user_email)
                return assign_resource_user(
                    conn, resource, user,
                    group_role_by_id(conn,
                                     resource_owner(conn, resource),
                                     uuid.UUID(group_role_id)))
        except AssertionError as aserr:
            raise AuthorisationError(aserr.args[0]) from aserr

        return jsonify(with_db_connection(__assign__))

@resources.route("<uuid:resource_id>/user/unassign", methods=["POST"])
@require_oauth("profile group resource role")
def unassign_role_to_user(resource_id: uuid.UUID) -> Response:
    """Unassign a role on the specified resource from a user."""
    with require_oauth.acquire("profile group resource role") as the_token:
        try:
            form = request.form
            group_role_id = form.get("group_role_id", "")
            user_id = form.get("user_id", "")
            assert bool(group_role_id), "The role must be provided."
            assert bool(user_id), "The user id must be provided."

            def __assign__(conn: db.DbConnection) -> dict:
                resource = resource_by_id(conn, the_token.user, resource_id)
                return unassign_resource_user(
                    conn, resource, user_by_id(conn, uuid.UUID(user_id)),
                    group_role_by_id(conn,
                                     resource_owner(conn, resource),
                                     uuid.UUID(group_role_id)))
        except AssertionError as aserr:
            raise AuthorisationError(aserr.args[0]) from aserr

        return jsonify(with_db_connection(__assign__))

def __public_view_params__(cursor, user_id, resource_id):
    ignore = (str(user_id),)
    # sys admins
    cursor.execute(
        "SELECT ur.user_id FROM user_roles AS ur INNER JOIN roles AS r "
        "ON ur.role_id=r.role_id WHERE r.role_name='system-administrator'")
    ignore = ignore + tuple(
        row["user_id"] for row in cursor.fetchall())
    # group admins
    cursor.execute(
        "SELECT DISTINCT gu.user_id FROM resource_ownership AS ro "
        "INNER JOIN groups AS g ON ro.group_id=g.group_id "
        "INNER JOIN group_users AS gu ON g.group_id=gu.group_id "
        "INNER JOIN user_roles AS ur ON gu.user_id=ur.user_id "
        "INNER JOIN roles AS r ON ur.role_id=r.role_id "
        "WHERE ro.resource_id=? AND r.role_name='group-leader'",
        (str(resource_id),))
    ignore = tuple(set(
        ignore + tuple(row["user_id"] for row in cursor.fetchall())))

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id NOT IN "
        f"({', '.join(['?'] * len(ignore))})",
        ignore)
    user_ids = tuple(row["user_id"] for row in cursor.fetchall())
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name='public-view'")
    role_id = cursor.fetchone()["role_id"]
    return tuple({
        "user_id": user_id,
        "role_id": role_id,
        "resource_id": str(resource_id)
    } for user_id in user_ids)

def __assign_revoke_public_view__(cursor, user_id, resource_id, public):
    if public:
        cursor.executemany(
            "INSERT INTO user_roles(user_id, role_id, resource_id) "
            "VALUES(:user_id, :role_id, :resource_id) "
            "ON CONFLICT (user_id, role_id, resource_id) "
            "DO NOTHING",
            __public_view_params__(cursor, user_id, resource_id))
        return
    cursor.executemany(
        "DELETE FROM user_roles WHERE user_id=:user_id "
        "AND role_id=:role_id AND resource_id=:resource_id",
        __public_view_params__(cursor, user_id, resource_id))

@resources.route("<uuid:resource_id>/toggle-public", methods=["POST"])
@require_oauth("profile group resource role")
def toggle_public(resource_id: uuid.UUID) -> Response:
    """Make a resource public if it is private, or private if public."""
    with require_oauth.acquire("profile group resource") as the_token:
        def __toggle__(conn: db.DbConnection) -> Resource:
            old_rsc = resource_by_id(conn, the_token.user, resource_id)
            public = not old_rsc.public
            new_resource = Resource(
                old_rsc.resource_id, old_rsc.resource_name,
                old_rsc.resource_category, public,
                old_rsc.resource_data)
            with db.cursor(conn) as cursor:
                cursor.execute(
                    "UPDATE resources SET public=:public "
                    "WHERE resource_id=:resource_id",
                    {
                        "public": 1 if public else 0,
                        "resource_id": str(resource_id)
                    })
                __assign_revoke_public_view__(
                    cursor, the_token.user.user_id, resource_id, public)
                return new_resource
            return new_resource

        resource = with_db_connection(__toggle__)
        return jsonify({
            "resource": asdict(resource),
            "description": (
                "Made resource public" if resource.public
                else "Made resource private")})

@resources.route("/authorisation", methods=["POST"])
def resources_authorisation():
    """Get user authorisations for given resource(s):"""
    try:
        data = request.json
        assert (data and "resource-ids" in data)
        resource_ids = tuple(uuid.UUID(resid) for resid in data["resource-ids"])
        pubres = tuple(
            res.resource_id for res in with_db_connection(public_resources)
            if res.resource_id in resource_ids)
        with require_oauth.acquire("profile resource") as the_token:
            the_resources = with_db_connection(lambda conn: user_roles_on_resources(
                conn, the_token.user, resource_ids))
            resp = jsonify({
                str(resid): {
                    "public-read": resid in pubres,
                    "roles": tuple(
                        asdict(rol) for rol in
                        the_resources.get(resid, {}).get("roles", tuple()))
                } for resid in resource_ids
            })
    except _HTTPException as _httpe:
        err_msg = json.loads(_httpe.body)
        if err_msg["error"] == "missing_authorization":
            resp = jsonify({
                str(resid): {
                    "public-read": resid in pubres
                } for resid in resource_ids
            })
    except AssertionError as _aerr:
        resp = jsonify({
            "status": "bad-request",
            "error_description": (
                "Expected a JSON object with a 'resource-ids' key.")
        })
        resp.status_code = 400

    return resp


@resources.route("/authorisation/<name>", methods=["GET"])
def get_user_roles_on_resource(name) -> Response:
    """Get user authorisation for a given resource given it's name"""
    resid = with_db_connection(
        lambda conn: get_resource_id(conn, name)
    )
    with require_oauth.acquire("profile resource") as _token:
        _resources = with_db_connection(
            lambda conn: user_roles_on_resources(
                conn, _token.user, (resid,)
            )
        )
        return jsonify({
                name: {
                    "roles": tuple(
                        asdict(rol) for rol in
                        _resources.get(resid, {}).get("roles", tuple()))
                }
            })
