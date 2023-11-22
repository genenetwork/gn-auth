"""Script to register and mark a user account as sysadmin."""
import sys
import getpass
from pathlib import Path

import click
from email_validator import validate_email, EmailNotValidError

from gn_auth.auth.db import sqlite3 as db
from gn_auth.auth.authorisation.users.admin.models import make_sys_admin
from gn_auth.auth.authentication.users import save_user, set_user_password

def fetch_email() -> str:
    """Prompt user for email."""
    while True:
        try:
            user_input = input("Enter the administrator's email: ")
            email = validate_email(user_input.strip(), check_deliverability=True)
            return email["email"]
        except EmailNotValidError as _enve:
            print("You did not provide a valid email address. Try again...",
                  file=sys.stderr)

def fetch_password() -> str:
    """Prompt user for password."""
    while True:
        passwd = getpass.getpass(prompt="Enter password: ").strip()
        passwd2 = getpass.getpass(prompt="Confirm password: ").strip()
        if passwd != "" and passwd == passwd2:
            return passwd
        if passwd == "":
            print("Empty password not accepted", file=sys.stderr)
            continue
        if passwd != passwd2:
            print("Passwords *MUST* match", file=sys.stderr)
            continue

def fetch_name() -> str:
    """Prompt user for name"""
    while True:
        name = input("Enter the user's name: ").strip()
        if name == "":
            print("Invalid name.")
            continue
        return name

def save_admin(conn: db.DbConnection, name: str, email: str, passwd: str):
    """Save the details to the database and assign the new user as admin."""
    with db.cursor(conn) as cursor:
        usr, _hpasswd = set_user_password(
            cursor, save_user(cursor, email, name), passwd)
        make_sys_admin(cursor, usr)
        return 0

def register_admin(authdbpath: Path):
    """Register a user as a system admin."""
    assert authdbpath.exists(), "Could not find database file."
    with db.connection(str(authdbpath)) as conn:
        return save_admin(conn, fetch_name(), fetch_email(), fetch_password())

if __name__ == "__main__":
    @click.command()
    @click.argument("authdbpath")
    def run(authdbpath):
        """Entry-point for when script is run directly"""
        return register_admin(Path(authdbpath).absolute())

    run()# pylint: disable=[no-value-for-parameter]
