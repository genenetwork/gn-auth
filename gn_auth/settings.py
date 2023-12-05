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

# Redis settings
REDIS_URI = "redis://localhost:6379/0"
REDIS_JOB_QUEUE = "GN_AUTH::job-queue"

# OAuth2 settings
OAUTH2_SCOPE = (
    "profile", "group", "role", "resource", "user", "masquerade",
    "introspect")

CORS_ORIGINS = "*"
CORS_HEADERS = [
    "Content-Type",
    "Authorization",
    "Access-Control-Allow-Credentials"
]
