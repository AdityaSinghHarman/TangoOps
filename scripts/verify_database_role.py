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
import tempfile
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
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"


def _restricted_url_from_existing() -> str:
    with LOCAL_SECRETS_PATH.open("rb") as file_handle:
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


def _update_local_secrets(database_url: str, secrets_path: Path = LOCAL_SECRETS_PATH):
    """Atomically replace only [postgres].connection_string in an ignored file."""
    original = secrets_path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    section = ""
    replaced = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
        elif section == "postgres" and stripped.startswith("connection_string"):
            newline = "\n" if line.endswith("\n") else ""
            indentation = line[:len(line) - len(line.lstrip())]
            lines[index] = f'{indentation}connection_string = "{database_url}"{newline}'
            replaced = True
            break
    if not replaced:
        raise SystemExit("Could not find [postgres].connection_string in local Streamlit Secrets.")

    mode = secrets_path.stat().st_mode & 0o777
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=secrets_path.parent, delete=False,
    ) as temporary:
        temporary.writelines(lines)
        temporary_path = Path(temporary.name)
    os.chmod(temporary_path, mode)
    os.replace(temporary_path, secrets_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    clipboard_group = parser.add_mutually_exclusive_group()
    clipboard_group.add_argument(
        "--copy-to-clipboard", action="store_true",
        help="Copy the verified restricted URL to the macOS clipboard without printing it.",
    )
    clipboard_group.add_argument(
        "--copy-streamlit-block", action="store_true",
        help="Copy a complete verified [postgres] TOML block for Streamlit Cloud.",
    )
    parser.add_argument(
        "--update-local-secrets", action="store_true",
        help="Atomically switch the ignored local Streamlit Secrets file after verification.",
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
    if args.update_local_secrets:
        _update_local_secrets(database_url)
        print("Local Streamlit Secrets now uses the verified restricted role.")
    if args.copy_to_clipboard or args.copy_streamlit_block:
        if sys.platform != "darwin":
            raise SystemExit("Verification passed, but clipboard copy is currently supported only on macOS.")
        clipboard_value = database_url
        if args.copy_streamlit_block:
            clipboard_value = f'[postgres]\nconnection_string = "{database_url}"\n'
        subprocess.run(["pbcopy"], input=clipboard_value.encode("utf-8"), check=True)
        if args.copy_streamlit_block:
            print("A complete verified [postgres] block is on your clipboard; its value was not displayed.")
        else:
            print("The verified restricted connection is now on your clipboard; its value was not displayed.")


if __name__ == "__main__":
    main()
