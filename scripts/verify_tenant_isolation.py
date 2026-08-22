"""Prove the Phase 8, Step 2 RLS enforcement actually isolates tenants.

Creates two throwaway businesses (A and B) as the restricted `tangoops_app`
role, inserts one row into every tenant-scoped table for each, then proves
two things and rolls everything back:

  1. A connection scoped to business A (app.current_business_id = A) can
     see A's rows in every in-scope table, but NEVER business B's - even
     though both exist in the same tables, in the same database, reachable
     by the same role.
  2. A connection with admin_scope on (app.bypass_tenant_scope = 'true')
     sees both businesses' rows, confirming the legitimate cross-tenant
     path (platform-admin views) still works.

This is the actual proof for Phase 8's stated goal ("a second tenant
cannot see the first tenant's data under any tested path") - not just an
assertion in a log entry. Setup writes use admin_scope, matching how
store.py's own admin-scope functions (get_businesses, create_user, etc.)
already behave - the isolation check itself is what matters here, and it
uses the same tangoops_app role and the same set_config() mechanism
store.py uses, not a superuser bypass.

Everything runs inside one transaction that is always rolled back.
"""
from pathlib import Path
import datetime as dt
import os
import tomllib
import uuid

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SECRETS_PATH = PROJECT_ROOT / ".streamlit" / "secrets.toml"

# (table, business_id column position doesn't matter - all in-scope tables
# use a plain "business_id" column, confirmed against store.py's SCHEMA).
IN_SCOPE_TABLES = [
    "memberships", "entitlements", "agencies", "raw_uploads", "assignments",
    "assignment_log", "archived_periods", "security_audit",
    "broadcaster_payout_rules", "broadcaster_payout_status", "billing_events",
    "reward_plans", "reward_plan_versions", "reward_plan_milestones",
    "broadcaster_reward_assignments", "recruiter_reward_assignments",
    "recruiter_reward_broadcaster_overrides", "manual_milestone_events",
    "reward_calculations", "reward_adjustments",
]


def _database_url() -> str:
    env_url = os.environ.get("TANGOOPS_DATABASE_URL")
    if env_url:
        return env_url
    with LOCAL_SECRETS_PATH.open("rb") as file_handle:
        return tomllib.load(file_handle)["postgres"]["connection_string"]


def _set_scope(cur, business_id=None, admin_scope=False):
    cur.execute(
        "SELECT set_config('app.current_business_id', %s, false), "
        "set_config('app.bypass_tenant_scope', %s, false)",
        (business_id or "", "true" if admin_scope else "false"),
    )


def main():
    database_url = _database_url()
    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    marker = uuid.uuid4().hex[:8]
    biz_a, biz_b = f"iso_test_a_{marker}", f"iso_test_b_{marker}"
    user_a, user_b = f"iso_a_{marker}@invalid.local", f"iso_b_{marker}@invalid.local"
    profile_a, profile_b = f"https://tango.me/iso_a_{marker}", f"https://tango.me/iso_b_{marker}"
    now = dt.datetime.now(dt.timezone.utc)

    try:
        with conn.cursor() as cur:
            _set_scope(cur, admin_scope=True)  # setup writes span both tenants

            for biz, user, profile in ((biz_a, user_a, profile_a), (biz_b, user_b, profile_b)):
                cur.execute(
                    "INSERT INTO businesses (business_id, business_name, status) VALUES (%s,%s,'Active')",
                    (biz, biz),
                )
                cur.execute(
                    "INSERT INTO users (username, name, password_hash, role, business_id, status) "
                    "VALUES (%s,%s,'x','owner',%s,'Active')",
                    (user, biz, biz),
                )
                cur.execute(
                    "INSERT INTO memberships (business_id, username, role, status) "
                    "VALUES (%s,%s,'owner','Active')",
                    (biz, user),
                )
                cur.execute(
                    "INSERT INTO entitlements (business_id, feature_key, value_type, value) "
                    "VALUES (%s,'iso_test','boolean','true')",
                    (biz,),
                )
                cur.execute(
                    "INSERT INTO agencies (business_id, agency_name, commission_pct) VALUES (%s,%s,5)",
                    (biz, biz),
                )
                cur.execute(
                    "INSERT INTO raw_uploads "
                    "(business_id, upload_id, uploaded_at, period, period_type, profile_url, broadcaster_name) "
                    "VALUES (%s,%s,%s,'2099-01','monthly',%s,%s)",
                    (biz, biz, now, profile, biz),
                )
                cur.execute(
                    "INSERT INTO assignments (business_id, profile_url, broadcaster_name, sub_agency, assigned_at) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (biz, profile, biz, biz, now),
                )
                cur.execute(
                    "INSERT INTO assignment_log "
                    "(business_id, profile_url, broadcaster_name, sub_agency, assigned_by, assigned_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s)",
                    (biz, profile, biz, biz, user, now),
                )
                cur.execute(
                    "INSERT INTO archived_periods (business_id, period, period_type) VALUES (%s,'2099-01','monthly')",
                    (biz,),
                )
                cur.execute(
                    "INSERT INTO security_audit "
                    "(business_id, actor_username, actor_role, event_type, target_type, target_id) "
                    "VALUES (%s,%s,'owner','iso_test','business',%s)",
                    (biz, user, biz),
                )
                cur.execute(
                    "INSERT INTO broadcaster_payout_rules "
                    "(business_id, profile_url, broadcaster_name, effective_from, agency_rate_pct, "
                    "payout_rate_pct, created_by) VALUES (%s,%s,%s,'2099-01',10,3.5,%s)",
                    (biz, profile, biz, user),
                )
                cur.execute(
                    "INSERT INTO broadcaster_payout_status "
                    "(business_id, period, profile_url, status) VALUES (%s,'2099-01',%s,'Pending')",
                    (biz, profile),
                )
                cur.execute(
                    "INSERT INTO billing_events "
                    "(business_id, event_type, method, amount, currency, recorded_by) "
                    "VALUES (%s,'payment_recorded','cash',999,'INR',%s)",
                    (biz, user),
                )
                cur.execute(
                    "INSERT INTO reward_plans "
                    "(business_id, name, recipient_type, reward_method, status, created_by) "
                    "VALUES (%s,%s,'broadcaster','diamond_milestone_coins','active',%s) RETURNING id",
                    (biz, biz, user),
                )
                plan_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO reward_plan_versions "
                    "(plan_id, business_id, version_number, effective_from, config, "
                    "tier_calculation_mode, frequency, created_by) "
                    "VALUES (%s,%s,1,'2099-01','{}'::jsonb,'highest_only','lifetime_once',%s) "
                    "RETURNING id",
                    (plan_id, biz, user),
                )
                plan_version_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO reward_plan_milestones "
                    "(plan_version_id, business_id, order_index, name, trigger_type, threshold, "
                    "reward_value, unit, frequency) "
                    "VALUES (%s,%s,0,%s,'diamonds_redeemed_threshold',25000,1000,'coins','lifetime_once') "
                    "RETURNING id, milestone_key",
                    (plan_version_id, biz, biz),
                )
                milestone_id, milestone_key = cur.fetchone()
                cur.execute(
                    "INSERT INTO broadcaster_reward_assignments "
                    "(business_id, profile_url, plan_id, effective_from, assigned_by) "
                    "VALUES (%s,%s,%s,'2099-01',%s)",
                    (biz, profile, plan_id, user),
                )
                cur.execute(
                    "INSERT INTO recruiter_reward_assignments "
                    "(business_id, agency_name, plan_id, effective_from, assigned_by) "
                    "VALUES (%s,%s,%s,'2099-01',%s)",
                    (biz, biz, plan_id, user),
                )
                cur.execute(
                    "INSERT INTO recruiter_reward_broadcaster_overrides "
                    "(business_id, agency_name, profile_url, plan_id, effective_from, assigned_by) "
                    "VALUES (%s,%s,%s,%s,'2099-01',%s)",
                    (biz, biz, profile, plan_id, user),
                )
                cur.execute(
                    "INSERT INTO manual_milestone_events "
                    "(business_id, recipient_type, recipient_id, trigger_type, event_date, created_by) "
                    "VALUES (%s,'broadcaster',%s,'signup_completed',%s,%s)",
                    (biz, profile, now.date(), user),
                )
                cur.execute(
                    "INSERT INTO reward_calculations "
                    "(business_id, recipient_type, recipient_id, plan_id, plan_version_id, "
                    "milestone_id, milestone_key, frequency, period, reward_method, "
                    "performance_snapshot, config_snapshot, calculated_amount, unit, status) "
                    "VALUES (%s,'broadcaster',%s,%s,%s,%s,%s,'lifetime_once','2099-01', "
                    "'diamond_milestone_coins','{}'::jsonb,'{}'::jsonb,1000,'coins','Awaiting Approval') "
                    "RETURNING id",
                    (biz, profile, plan_id, plan_version_id, milestone_id, milestone_key),
                )
                reward_calc_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO reward_adjustments "
                    "(business_id, reward_calculation_id, adjustment_type, reason, original_amount, "
                    "adjustment_amount, final_amount, created_by) "
                    "VALUES (%s,%s,'bonus','isolation-test',1000,100,1100,%s)",
                    (biz, reward_calc_id, user),
                )
            _set_scope(cur)  # reset before the real test, same as store.py always does

            failures = []

            for table in IN_SCOPE_TABLES:
                _set_scope(cur, business_id=biz_a)
                cur.execute(
                    f"SELECT DISTINCT business_id FROM {table} WHERE business_id IN (%s,%s)",
                    (biz_a, biz_b),
                )
                seen_scoped = {row[0] for row in cur.fetchall()}
                _set_scope(cur, admin_scope=True)
                cur.execute(
                    f"SELECT DISTINCT business_id FROM {table} WHERE business_id IN (%s,%s)",
                    (biz_a, biz_b),
                )
                seen_admin = {row[0] for row in cur.fetchall()}
                _set_scope(cur)

                if seen_scoped != {biz_a}:
                    failures.append(
                        f"{table}: scoped to A saw {seen_scoped!r}, expected {{'{biz_a}'}} only"
                    )
                if seen_admin != {biz_a, biz_b}:
                    failures.append(
                        f"{table}: admin_scope saw {seen_admin!r}, expected both businesses"
                    )

            # also confirm a call scoped to NEITHER business (no set_config at
            # all, or explicitly reset) sees nothing - the fail-closed default.
            _set_scope(cur)
            for table in IN_SCOPE_TABLES:
                cur.execute(
                    f"SELECT count(*) FROM {table} WHERE business_id IN (%s,%s)", (biz_a, biz_b),
                )
                count = cur.fetchone()[0]
                if count != 0:
                    failures.append(f"{table}: unscoped read saw {count} rows, expected 0 (fail-closed)")
    finally:
        conn.rollback()
        conn.close()

    if failures:
        print("FAIL - tenant isolation is broken for:")
        for line in failures:
            print(f"  - {line}")
        raise SystemExit(1)

    print(
        f"PASS: all {len(IN_SCOPE_TABLES)} in-scope tables correctly isolated business A from "
        "business B, admin_scope correctly saw both, and an unscoped read correctly saw neither. "
        "Test transaction rolled back."
    )


if __name__ == "__main__":
    main()
