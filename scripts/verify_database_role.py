"""Verify that a TangoOps database connection is operational and restricted."""
from getpass import getpass
import os

import psycopg2

TABLES = (
    "businesses", "users", "agencies", "raw_uploads", "assignments",
    "assignment_log", "archived_periods", "profiles", "security_audit",
)
SEQUENCES = ("raw_uploads_id_seq", "assignment_log_id_seq", "security_audit_id_seq")


def main():
    database_url = os.environ.get("TANGOOPS_DATABASE_URL")
    if not database_url:
        database_url = getpass("Restricted database connection string (hidden): ").strip()
    if not database_url:
        raise SystemExit("No connection string supplied.")

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
                cur.execute(
                    "SELECT has_table_privilege(current_user, %s, 'SELECT,INSERT,UPDATE,DELETE')",
                    (f"public.{table}",),
                )
                if not cur.fetchone()[0]:
                    raise SystemExit(f"Missing runtime permissions on public.{table}.")
            for sequence in SEQUENCES:
                cur.execute(
                    "SELECT has_sequence_privilege(current_user, %s, 'USAGE,SELECT')",
                    (f"public.{sequence}",),
                )
                if not cur.fetchone()[0]:
                    raise SystemExit(f"Missing runtime permissions on public.{sequence}.")
            cur.execute("SELECT COUNT(*) FROM public.businesses")
            cur.fetchone()
        conn.rollback()
    finally:
        conn.close()

    if unsafe:
        raise SystemExit(f"FAILED: role {role[0]} still has administrator or RLS-bypass privileges.")
    print(f"PASS: role {role[0]} has required TangoOps access and no administrator privileges.")


if __name__ == "__main__":
    main()
