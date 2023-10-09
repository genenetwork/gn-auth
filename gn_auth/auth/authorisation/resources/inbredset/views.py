"""Views for InbredSet resources."""
from flask import jsonify, Response, Blueprint

from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.db.sqlite3 import with_db_connection
from gn_auth.auth.authentication.oauth2.resource_server import require_oauth

iset = Blueprint("inbredset", __name__)

@iset.route("/resource-id/<int:speciesid>/<int:inbredsetid>")
def resource_id_by_inbredset_id(speciesid: int, inbredsetid: int) -> Response:
    """Retrieve the resource ID for resource attached to the inbredset."""
    def __res_by_iset_id__(conn):
        with db.cursor(conn) as cursor:
            cursor.execute(
                "SELECT r.resource_id FROM linked_inbredset_groups AS lisg "
                "INNER JOIN inbredset_group_resources AS isgr "
                "ON lisg.data_link_id=isgr.data_link_id "
                "INNER JOIN resources AS r ON isgr.resource_id=r.resource_id "
                "WHERE lisg.SpeciesId=? AND lisg.InbredSetId=?",
                (speciesid, inbredsetid))
            return cursor.fetchone()

    res = with_db_connection(__res_by_iset_id__)
    if res:
        resp = jsonify({"status": "success", "resource-id": res["resource_id"]})
    else:
        resp = jsonify({
            "status": "not-found",
            "error_description": (
                "Could not find resource handling InbredSet group with ID "
                f"'{inbredsetid}' that belongs to Species with ID "
                f"'{speciesid}'")
        })
        resp.status_code = 404

    return resp
