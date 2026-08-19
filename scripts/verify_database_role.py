"""Verify that a TangoOps database connection is operational and restricted.

By default, this reads the non-secret host/project shape from the existing
local Streamlit configuration and asks only for the new role password using a
hidden prompt. The password and resulting URL are never printed.
"""
import argparse
from getpass import getpass
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from urllib.parse import quote, urlparse, urlunparse

import psycopg2

TABLES = (
    "businesses", "users", "agencies", "raw_uploads", "assignments",
    "assignment_log", "archived_periods", "profiles", "security_audit",
)
SEQUENCES = ("raw_uploads_id_seq", "assignment_log_id_seq", "security_audit_id_seq")
TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE")
SEQUENCE_PRIVILEGES = ("USAGE", "SELECT")


def _restricted_url_from_existing() -> str:
    project_root = Path(__file__).resolve().parents[1]
    secrets_path = project_root / ".streamlit" / "secrets.toml"
    with secrets_path.open("rb") as file_handle:
        current_url = tomllib.load(file_handle)["postgres"]["connection_string"]

    parsed = urlparse(current_url)
    current_username = parsed.username or ""
    if "." in current_username:
        project_suffix = current_username.split(".", 1)[1]
        restricted_username = f"tangoops_app.{project_suffix}"
    else:
        restricted_username = "tangoops_app"

    password = getpass("New tangoops_app database password (hidden): ")
    if not password:
        raise SystemExit("No password supplied.")
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{quote(restricted_username, safe='.') }:{quote(password, safe='')}@{hostname}{port}"
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--copy-to-clipboard", action="store_true",
        help="Copy the verified restricted URL to the macOS clipboard without printing it.",
    )
    args = parser.parse_args()
    database_url = os.environ.get("TANGOOPS_DATABASE_URL")
    if not database_url:
        database_url = _restricted_url_from_existing()

    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_user, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            )
            role = cur.fetchone()
            if not role:
                raise SystemExit("Unable to inspect the configured database role.")
            unsafe = any(bool(value) for value in role[1:])
            for table in TABLES:
                for privilege in TABLE_PRIVILEGES:
                    cur.execute(
                        "SELECT has_table_privilege(current_user, %s, %s)",
                        (f"public.{table}", privilege),
                    )
                    if not cur.fetchone()[0]:
                        raise SystemExit(f"Missing {privilege} on public.{table}.")
            for sequence in SEQUENCES:
                for privilege in SEQUENCE_PRIVILEGES:
                    cur.execute(
                        "SELECT has_sequence_privilege(current_user, %s, %s)",
                        (f"public.{sequence}", privilege),
                    )
                    if not cur.fetchone()[0]:
                        raise SystemExit(f"Missing {privilege} on public.{sequence}.")
            cur.execute("SELECT COUNT(*) FROM public.businesses")
            cur.fetchone()
        conn.rollback()
    finally:
        conn.close()

    if unsafe:
        raise SystemExit(f"FAILED: role {role[0]} still has administrator or RLS-bypass privileges.")
    print(f"PASS: role {role[0]} has required TangoOps access and no administrator privileges.")
    if args.copy_to_clipboard:
        if sys.platform != "darwin":
            raise SystemExit("Verification passed, but clipboard copy is currently supported only on macOS.")
        subprocess.run(["pbcopy"], input=database_url.encode("utf-8"), check=True)
        print("The verified restricted connection is now on your clipboard; its value was not displayed.")


if __name__ == "__main__":
    main()
