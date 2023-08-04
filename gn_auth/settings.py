"""Default application settings."""
import os

# LOGLEVEL
LOGLEVEL = "WARNING"

# Flask settings
SECRET_KEY = ""

# Database settings
SQL_URI = "mysql://webqtlout:webqtlout@localhost/db_webqtl"
AUTH_DB = f"{os.environ.get('HOME')}/genenetwork/gn3_files/db/auth.db"
AUTH_MIGRATIONS = "migrations/auth"

# OAuth2 settings
OAUTH2_SCOPE = (
    "profile", "group", "role", "resource", "user", "masquerade",
    "introspect")
