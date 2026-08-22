"""Exercise StreamOperiq runtime database writes and roll the transaction back.

This proves the configured role can perform the application's required DML
without leaving test records or modifying customer data.
"""
from pathlib import Path
import datetime as dt
import tomllib
import uuid

import psycopg2


def main():
    project_root = Path(__file__).resolve().parents[1]
    with (project_root / ".streamlit" / "secrets.toml").open("rb") as file_handle:
        database_url = tomllib.load(file_handle)["postgres"]["connection_string"]

    marker = f"security_test_{uuid.uuid4().hex}"
    business_id = marker[:48]
    username = f"{marker}@invalid.local"
    profile_url = f"https://tango.me/{marker}"
    now = dt.datetime.now(dt.timezone.utc)

    conn = psycopg2.connect(database_url, sslmode="require", connect_timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_user, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            )
            role = cur.fetchone()
            if not role or any(bool(value) for value in role[1:]):
                raise RuntimeError("The configured role still has elevated database privileges.")

            cur.execute(
                "INSERT INTO businesses (business_id, business_name, status) VALUES (%s,%s,'Active')",
                (business_id, marker),
            )
            cur.execute(
                "INSERT INTO users (username, name, password_hash, role, business_id, status) "
                "VALUES (%s,%s,%s,'owner',%s,'Active')",
                (username, marker, "transaction-only-test", business_id),
            )
            cur.execute(
                "INSERT INTO memberships (business_id, username, role, sub_agency, status, expires_at, profile_url) "
                "VALUES (%s,%s,'owner',NULL,'Active',%s,%s)",
                (business_id, username, now + dt.timedelta(days=5), profile_url),
            )
            cur.execute(
                "INSERT INTO subscriptions (business_id, plan_code, billing_cycle, status, auto_renew) "
                "VALUES (%s,'growth','annual','trialing',false)",
                (business_id,),
            )
            role_code = f"{marker}_role"
            permission_key = f"{marker}.permission"
            cur.execute(
                "INSERT INTO roles (code, name, description) VALUES (%s,%s,%s)",
                (role_code, marker, "transaction-only-test"),
            )
            cur.execute(
                "INSERT INTO permissions (key, description, category) VALUES (%s,%s,%s)",
                (permission_key, "transaction-only-test", marker),
            )
            cur.execute(
                "INSERT INTO role_permissions (role_code, permission_key) VALUES (%s,%s)",
                (role_code, permission_key),
            )
            plan_code = f"{marker}_plan"
            cur.execute(
                "INSERT INTO plans (code, name, price_monthly, price_annual, currency, billing_mode) "
                "VALUES (%s,%s,999,9990,'INR','recurring')",
                (plan_code, marker),
            )
            cur.execute(
                "INSERT INTO plan_features (plan_code, feature_key, value_type, value) "
                "VALUES (%s,'test_feature','numeric','5')",
                (plan_code,),
            )
            cur.execute(
                "INSERT INTO entitlements (business_id, feature_key, value_type, value, overridden_by) "
                "VALUES (%s,'test_feature','numeric','10',%s)",
                (business_id, username),
            )
            cur.execute(
                "INSERT INTO agencies (business_id, agency_name, commission_pct) VALUES (%s,%s,5)",
                (business_id, marker),
            )
            cur.execute(
                "INSERT INTO raw_uploads "
                "(business_id, upload_id, uploaded_at, period, period_type, profile_url, broadcaster_name) "
                "VALUES (%s,%s,%s,'2099-01','monthly',%s,%s) RETURNING id",
                (business_id, marker, now, profile_url, marker),
            )
            cur.fetchone()
            cur.execute(
                "INSERT INTO assignments "
                "(business_id, profile_url, broadcaster_name, sub_agency, assigned_at) "
                "VALUES (%s,%s,%s,%s,%s)",
                (business_id, profile_url, marker, marker, now),
            )
            cur.execute(
                "INSERT INTO assignment_log "
                "(business_id, profile_url, broadcaster_name, sub_agency, assigned_by, assigned_at) "
                "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (business_id, profile_url, marker, marker, username, now),
            )
            cur.fetchone()
            cur.execute(
                "INSERT INTO archived_periods (business_id, period, period_type) "
                "VALUES (%s,'2099-01','monthly')",
                (business_id,),
            )
            cur.execute(
                "INSERT INTO profiles (username, display_name) VALUES (%s,%s)",
                (username, marker),
            )
            cur.execute(
                "INSERT INTO security_audit "
                "(business_id, actor_username, actor_role, event_type, target_type, target_id) "
                "VALUES (%s,%s,'platform_admin','transaction_test','business',%s) RETURNING id",
                (business_id, username, business_id),
            )
            cur.fetchone()
            cur.execute(
                "INSERT INTO broadcaster_payout_rules "
                "(business_id, profile_url, broadcaster_name, effective_from, agency_rate_pct, "
                "payout_rate_pct, created_by) VALUES (%s,%s,%s,'2099-01',10,3.5,%s)",
                (business_id, profile_url, marker, username),
            )
            cur.execute(
                "INSERT INTO broadcaster_payout_status "
                "(business_id, period, profile_url, status, paid_at, paid_by) "
                "VALUES (%s,'2099-01',%s,'Paid',%s,%s)",
                (business_id, profile_url, now, username),
            )
            cur.execute(
                "INSERT INTO billing_events "
                "(business_id, event_type, method, amount, currency, reference_note, recorded_by) "
                "VALUES (%s,'payment_recorded','bank_transfer',999.00,'INR',%s,%s) RETURNING id",
                (business_id, marker, username),
            )
            cur.fetchone()

            cur.execute(
                "UPDATE businesses SET business_name=%s WHERE business_id=%s RETURNING business_name",
                (marker + "_updated", business_id),
            )
            if cur.fetchone()[0] != marker + "_updated":
                raise RuntimeError("Runtime UPDATE verification failed.")
            cur.execute("DELETE FROM profiles WHERE username=%s RETURNING username", (username,))
            if cur.fetchone()[0] != username:
                raise RuntimeError("Runtime DELETE verification failed.")
    finally:
        conn.rollback()
        conn.close()

    print(
        f"PASS: restricted role {role[0]} completed SELECT/INSERT/UPDATE/DELETE and sequence operations; "
        "the verification transaction was rolled back."
    )


if __name__ == "__main__":
    main()
