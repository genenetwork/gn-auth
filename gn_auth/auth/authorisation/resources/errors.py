"""Exceptions for Authorisation"""

from gn_auth.auth.authorisation.errors import AuthorisationError

class MissingGroupError(AuthorisationError):
    """Raised for any resource operation without a group."""
