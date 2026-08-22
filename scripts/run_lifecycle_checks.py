"""Scheduled subscription lifecycle check (Phase 7, first slice).

Advances subscriptions.status through active -> grace -> restricted based
purely on elapsed time past current_period_end - no email is sent, this
only updates the status column. The in-app banner (app.py) reads that
status live on every page load, so a status change here is visible to
the tenant on their very next request.

Intended to run on a schedule (see .github/workflows/lifecycle_checks.yml),
but safe to run manually and idempotent:
  - A subscription already in 'grace' or 'restricted' is only ever moved
    forward, never backward, by this script.
  - A tenant that pays (store.record_payment() sets status back to
    'active' with a fresh period) is picked back up correctly on the very
    next run, since the UPDATE only matches rows still in the stale state.
  - Running it twice in the same day is a no-op the second time - nothing
    newly matches the WHERE clause.

Demo/test tenants (businesses.is_demo = true) are explicitly excluded -
"demo tenant never gets suspended for non-payment" was Phase 2's stated
acceptance criterion, honored here too. All 3 of prod's current tenants
were flagged is_demo=true by the Phase 2 backfill, so none of them will
be moved by this script until that flag is cleared on a specific test
business (store.set_business_demo_flag) for testing purposes.

Uses the restricted runtime database role (TANGOOPS_DATABASE_URL), same
as every other ad-hoc script in this directory - this only needs the
SELECT/UPDATE/INSERT privileges tangoops_app already has, no admin
connection required.
"""
from pathlib import Path
import datetime as dt
import os
import tomllib

import psycopg2

GRACE_PERIOD_DAYS = 7
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"


def _database_url() -> str:
    env_url = os.environ.get("TANGOOPS_DATABASE_URL")
    if env_url:
        return env_url
    with LOCAL_SECRETS_PATH.open("rb") as file_handle:
        return tomllib.load(file_handle)["postgres"]["connection_string"]


def main():
    database_url = _database_url()
    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    today = dt.date.today()
    grace_cutoff = today - dt.timedelta(days=GRACE_PERIOD_DAYS)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscriptions s SET status='grace', updated_at=now() "
                "FROM businesses b WHERE s.business_id=b.business_id "
                "AND s.status='active' AND s.current_period_end < %s AND NOT b.is_demo "
                "RETURNING s.business_id",
                (today,),
            )
            moved_to_grace = [row[0] for row in cur.fetchall()]

            cur.execute(
                "UPDATE subscriptions s SET status='restricted', updated_at=now() "
                "FROM businesses b WHERE s.business_id=b.business_id "
                "AND s.status='grace' AND s.current_period_end < %s AND NOT b.is_demo "
                "RETURNING s.business_id",
                (grace_cutoff,),
            )
            moved_to_restricted = [row[0] for row in cur.fetchall()]

            for business_id in moved_to_grace:
                cur.execute(
                    "INSERT INTO security_audit "
                    "(business_id, actor_username, actor_role, event_type, target_type, target_id) "
                    "VALUES (%s,'system','system','subscription_grace','subscription',%s)",
                    (business_id, business_id),
                )
            for business_id in moved_to_restricted:
                cur.execute(
                    "INSERT INTO security_audit "
                    "(business_id, actor_username, actor_role, event_type, target_type, target_id) "
                    "VALUES (%s,'system','system','subscription_restricted','subscription',%s)",
                    (business_id, business_id),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"Moved to grace ({GRACE_PERIOD_DAYS}-day window starts): {moved_to_grace}")
    print(f"Moved to restricted (grace period expired): {moved_to_restricted}")


if __name__ == "__main__":
    main()
