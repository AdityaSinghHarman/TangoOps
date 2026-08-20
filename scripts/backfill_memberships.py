"""One-time backfill for the `memberships` table (SaaS Phase 2).

Run this exactly once, after scripts/run_migrations.py has created the
`memberships` table and `businesses.is_demo` column, and before app.py is
deployed with the version of `current_user_context()` that reads through
memberships. Running the migration and this backfill out of order — or
deploying the app change before this has run — would lock out every existing
login, since a login with zero membership rows falls back to reading `users`
directly only as a transitional safety net, not a permanent path.

What it does, both idempotent and safe to re-run:
  1. Insert one `memberships` row per existing `users` row that has a
     business_id and a role of 'owner' or 'sub_agency' (platform_admin is the
     bootstrap identity and was never a `users` row). Existing rows are left
     untouched (ON CONFLICT DO NOTHING) — this never overwrites a membership
     already created by the app itself since this change shipped.
  2. Flag every business that exists *before this script's first run* as
     `is_demo = true` — confirmed dummy/test data, not real customers, so
     later billing/lifecycle enforcement (Phase 6/7) skips them. A business
     created after this script has already run is never touched by it.

Uses the restricted runtime database role (same as the deployed app), not an
administrator connection — this is data backfill (DML), not a schema change.
"""
from pathlib import Path
import sys
import tomllib

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"


def _database_url() -> str:
    import os
    env_url = os.environ.get("TANGOOPS_DATABASE_URL")
    if env_url:
        return env_url
    with LOCAL_SECRETS_PATH.open("rb") as file_handle:
        return tomllib.load(file_handle)["postgres"]["connection_string"]


def main():
    database_url = _database_url()
    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.memberships')")
            if cur.fetchone()[0] is None:
                raise SystemExit(
                    "The memberships table doesn't exist yet. Run scripts/run_migrations.py "
                    "first, then re-run this script."
                )

            cur.execute(
                "SELECT username, role, business_id, sub_agency FROM users "
                "WHERE business_id IS NOT NULL AND role IN ('owner', 'sub_agency')"
            )
            candidate_users = cur.fetchall()

            cur.execute("SELECT business_id, business_name, is_demo FROM businesses")
            existing_businesses = cur.fetchall()

        preview_new_memberships = 0
        preview_new_demo_flags = 0
        with conn.cursor() as cur:
            for username, role, business_id, sub_agency in candidate_users:
                cur.execute(
                    "SELECT 1 FROM memberships WHERE business_id=%s AND username=%s",
                    (business_id, username),
                )
                if cur.fetchone() is None:
                    preview_new_memberships += 1
            preview_new_demo_flags = sum(1 for _, _, is_demo in existing_businesses if not is_demo)

        print(f"Users found:              {len(candidate_users)}")
        print(f"New membership rows:      {preview_new_memberships}")
        print(f"Businesses to flag demo:  {preview_new_demo_flags} of {len(existing_businesses)} total")
        if preview_new_memberships == 0 and preview_new_demo_flags == 0:
            print("Nothing to do — backfill already applied.")
            return

        confirmation = input(
            "\nThis will INSERT the membership rows above and mark the listed "
            "businesses is_demo=true. Type 'yes' to proceed: "
        ).strip().lower()
        if confirmation != "yes":
            raise SystemExit("Backfill cancelled — no changes made.")

        with conn.cursor() as cur:
            for username, role, business_id, sub_agency in candidate_users:
                cur.execute(
                    "INSERT INTO memberships (business_id, username, role, sub_agency, status) "
                    "SELECT %s, %s, %s, %s, status FROM users WHERE username=%s "
                    "ON CONFLICT (business_id, username) DO NOTHING",
                    (business_id, username, role, sub_agency, username),
                )
            for business_id, business_name, is_demo in existing_businesses:
                if not is_demo:
                    cur.execute(
                        "UPDATE businesses SET is_demo=true WHERE business_id=%s",
                        (business_id,),
                    )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(
        f"\nBackfill complete: {preview_new_memberships} membership rows inserted, "
        f"{preview_new_demo_flags} businesses flagged is_demo=true."
    )


if __name__ == "__main__":
    main()
