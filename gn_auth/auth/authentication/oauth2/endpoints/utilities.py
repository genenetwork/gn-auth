"""endpoint utilities"""
from typing import Any, Optional

from flask import current_app
from pymonad.maybe import Nothing

from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.authentication.oauth2.models.oauth2token import (
    OAuth2Token, token_by_access_token, token_by_refresh_token)

def query_token(# pylint: disable=[unused-argument]
        endpoint_object: Any, token_str: str, token_type_hint) -> Optional[
            OAuth2Token]:
    """Retrieve the token from the database."""
    def __identity__(val):
        """Identity function."""
        return val
    token = Nothing
    with db.connection(current_app.config["AUTH_DB"]) as conn:
        match token_type_hint:
            case "access_token":
                token = token_by_access_token(
                    conn, token_str
                )
            case "refresh_token":
                token = token_by_refresh_token(
                    conn, token_str
                )
            case _:
                token = Nothing

        return token.maybe(
            token_by_access_token(conn, token_str).maybe(
                token_by_refresh_token(conn, token_str).maybe(
                    None, __identity__),
                __identity__),
            __identity__)

    return None
