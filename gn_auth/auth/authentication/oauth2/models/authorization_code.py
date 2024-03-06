"""Model and functions for handling the Authorisation Code"""
from uuid import UUID
from datetime import datetime
from typing import NamedTuple

from pymonad.tools import monad_from_none_or_value
from pymonad.maybe import Just, Maybe, Nothing

from gn_auth.auth.db import sqlite3 as db

from .oauth2client import OAuth2Client

from ...users import User, user_by_id


EXPIRY_IN_SECONDS = 300  # in seconds


class AuthorisationCode(NamedTuple):
    """
    The AuthorisationCode model for the auth(entic|oris)ation system.
    """
    # Instance variables
    code_id: UUID
    code: str
    client: OAuth2Client
    redirect_uri: str
    scope: str
    nonce: str
    auth_time: int
    code_challenge: str
    code_challenge_method: str
    user: User

    @property
    def response_type(self) -> str:
        """
        For authorisation code flow, the response_type type MUST always be
        'code'.
        """
        return "code"

    def is_expired(self):
        """Check whether the code is expired."""
        return self.auth_time + EXPIRY_IN_SECONDS < datetime.now().timestamp()

    def get_redirect_uri(self):
        """Get the redirect URI"""
        return self.redirect_uri

    def get_scope(self):
        """Return the assigned scope for this AuthorisationCode."""
        return self.scope

    def get_nonce(self):
        """Get the one-time use token."""
        return self.nonce

def authorisation_code(conn: db.DbConnection ,
                       code: str,
                       client: OAuth2Client) -> Maybe[AuthorisationCode]:
    """
    Retrieve the authorisation code object that corresponds to `code` and the
    given OAuth2 client.
    """
    with db.cursor(conn) as cursor:
        query = ("SELECT * FROM authorisation_code "
                 "WHERE code=:code AND client_id=:client_id")
        cursor.execute(
            query, {"code": code, "client_id": str(client.client_id)})

        return monad_from_none_or_value(
            Nothing, Just, cursor.fetchone()
        ).then(
            lambda result: AuthorisationCode(
                code_id=UUID(result["code_id"]),
                code=result["code"],
                client=client,
                redirect_uri=result["redirect_uri"],
                scope=result["scope"],
                nonce=result["nonce"],
                auth_time=int(result["auth_time"]),
                code_challenge=result["code_challenge"],
                code_challenge_method=result["code_challenge_method"],
                user=user_by_id(conn, UUID(result["user_id"]))))

def save_authorisation_code(conn: db.DbConnection,
                            auth_code: AuthorisationCode) -> AuthorisationCode:
    """Persist the `auth_code` into the database."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO authorisation_code VALUES("
            ":code_id, :code, :client_id, :redirect_uri, :scope, :nonce, "
            ":auth_time, :code_challenge, :code_challenge_method, :user_id"
            ")",
            {
                **auth_code._asdict(),
                "code_id": str(auth_code.code_id),
                "client_id": str(auth_code.client.client_id),
                "user_id": str(auth_code.user.user_id)
            })
        return auth_code
