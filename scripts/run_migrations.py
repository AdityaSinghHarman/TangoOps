"""Run TangoOps schema upgrades with a temporary administrator connection.

Normal Streamlit startup never executes DDL. Run this script only when a
TangoOps release explicitly contains a database migration.
"""
from getpass import getpass
from pathlib import Path
import os
import sys

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import store  # noqa: E402


def main():
    database_url = os.environ.get("TANGOOPS_MIGRATION_DATABASE_URL")
    if not database_url:
        database_url = getpass("Administrator database connection string (hidden): ").strip()
    if not database_url:
        raise SystemExit("No administrator connection string supplied.")

    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rolsuper OR rolcreatedb OR rolcreaterole "
                "FROM pg_roles WHERE rolname=current_user"
            )
            privileged = cur.fetchone()
            if not privileged or not privileged[0]:
                raise SystemExit("Migration cancelled: this connection is not an administrator role.")
            cur.execute(store.SCHEMA)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print("TangoOps database migration completed successfully.")


if __name__ == "__main__":
    main()
