"""
Multi-tenant persistence layer, backed by Postgres (free on Supabase).
Every table except `businesses` and `users` carries a business_id column,
which is how each business's data stays completely walled off from every
other business sharing this same app.

Tables (created through the administrator-only migration command):
  businesses        one row per top-level business (ABC, DEF, ...)
  users             every login on the platform, tagged with role + business_id
  memberships       one row per (business_id, username) a login belongs to;
                     the authoritative source for role/business resolution at
                     login, added so identity is no longer hardwired to a
                     single business_id/role pair on the users row itself
  subscriptions     one row per business: its current plan/billing state.
                     Schema only for now (no app wiring) — added early to
                     carry a one-time annual purchase (auto_renew=false)
  roles             the 8 named roles (Phase 3). Schema + seed data only —
                     app.py still branches on is_owner/is_sub_agency/
                     is_platform_admin, not this table, until the app.py
                     migration pass (see PHASE_LOG.md)
  permissions       atomic capabilities (e.g. 'broadcaster.upload')
  role_permissions  which permissions each role has; has_permission() reads
                     this but nothing calls it yet
  agencies          sub-agency names, per business
  raw_uploads       every uploaded period's broadcaster stats, per business
  assignments       permanent profile_url -> sub_agency mapping, per business
  assignment_log    append-only audit trail of every assignment made
  archived_periods  periods hidden from the active dropdowns, per business
"""
import datetime as dt
import re
import uuid
import pandas as pd
import streamlit as st
import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

SCHEMA = """
CREATE TABLE IF NOT EXISTS businesses (
    business_id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT now()
);

ALTER TABLE businesses
    ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    password_hash TEXT,
    role TEXT,
    business_id TEXT,
    sub_agency TEXT,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT now()
);

-- One row per (business_id, username) a login belongs to. A user still has
-- exactly one row today (backfilled 1:1 from users.business_id/role by
-- scripts/backfill_memberships.py), but identity is no longer hardwired to a
-- single business_id/role pair on the users row itself: this is what makes a
-- future login-in-two-tenants case (e.g. platform support staff) a data change
-- rather than a schema change.
CREATE TABLE IF NOT EXISTS memberships (
    business_id TEXT NOT NULL REFERENCES businesses(business_id),
    username TEXT NOT NULL REFERENCES users(username),
    role TEXT NOT NULL,
    sub_agency TEXT,
    status TEXT DEFAULT 'Active',
    invited_by TEXT,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, username)
);
CREATE INDEX IF NOT EXISTS idx_memberships_username
    ON memberships (username, status);

-- NULL for every normal role — permanent until someone suspends it. Set to a
-- real timestamp only for a time-boxed grant (the Trial Viewer role, Section
-- 15 of the SaaS blueprint): a demo/trial login that's meant to lapse on its
-- own rather than rely on someone remembering to revoke it. Enforcing the
-- expiry at login time is Phase 3 work — this column just gives it somewhere
-- to read from.
ALTER TABLE memberships
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'memberships_expires_at_after_created'
    ) THEN
        ALTER TABLE memberships
            ADD CONSTRAINT memberships_expires_at_after_created
            CHECK (expires_at IS NULL OR expires_at > created_at);
    END IF;
END $$;

-- One row per business: its current subscription state. Added early (ahead of
-- the full Phase 4/6 plans/entitlements/billing build) specifically to carry
-- a one-time annual purchase: auto_renew defaults false because there is no
-- payment gateway to auto-charge yet (Section 11) — a customer pays once for
-- a 12-month period, and current_period_end is what the future lifecycle
-- automation (Phase 7) checks to start the renewal-reminder cascade. No
-- plan_id FK yet: the `plans` catalog table doesn't exist until Phase 4, so
-- plan_code stays a plain string until then. Schema only for now — no store.py
-- or app.py wiring reads or writes this table yet.
CREATE TABLE IF NOT EXISTS subscriptions (
    business_id TEXT PRIMARY KEY REFERENCES businesses(business_id),
    plan_code TEXT NOT NULL DEFAULT 'essential',
    billing_cycle TEXT NOT NULL DEFAULT 'annual',
    status TEXT NOT NULL DEFAULT 'trialing',
    auto_renew BOOLEAN NOT NULL DEFAULT false,
    current_period_start DATE,
    current_period_end DATE,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT subscriptions_billing_cycle_valid
        CHECK (billing_cycle IN ('monthly', 'annual')),
    CONSTRAINT subscriptions_status_valid
        CHECK (status IN ('trialing', 'active', 'grace', 'restricted', 'cancelled', 'expired'))
);

-- Phase 3 (Roles & permissions), schema + seed data only for now — nothing
-- in app.py reads these tables yet, so seeding them here changes no runtime
-- behavior. `roles.code`/`permissions.key` reuse the same plain-text role
-- values already stored in users.role/memberships.role (e.g. 'owner',
-- 'sub_agency') rather than a surrogate ID, so no existing row needs
-- rewriting when this catalog is introduced.
CREATE TABLE IF NOT EXISTS roles (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS permissions (
    key TEXT PRIMARY KEY,
    description TEXT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_code TEXT NOT NULL REFERENCES roles(code),
    permission_key TEXT NOT NULL REFERENCES permissions(key),
    PRIMARY KEY (role_code, permission_key)
);

INSERT INTO roles (code, name, description) VALUES
    ('platform_admin', 'SaaS Super Admin', 'Entire platform, all tenants, billing, plans, and role definitions.'),
    ('support_admin', 'Platform Support Admin', 'Platform-wide, read-mostly, time-boxed impersonation for support.'),
    ('owner', 'Agency Owner', 'Full control of one tenant, including billing and plan.'),
    ('agency_manager', 'Agency Manager', 'Operational tier under Owner; everything except billing/plan.'),
    ('sub_agency', 'Recruiter / Sub-Agency', 'Own assigned broadcasters only.'),
    ('broadcaster', 'Broadcaster', 'Own performance only, plan-gated dashboard access.'),
    ('auditor', 'Read-only / Auditor', 'Compliance/finance, configurable scope, no write access.'),
    ('trial_viewer', 'Trial Viewer', 'Time-boxed demo/trial access, read-only, no export.')
ON CONFLICT (code) DO NOTHING;

INSERT INTO permissions (key, description, category) VALUES
    ('platform.manage_businesses', 'Create, suspend, rename, or delete tenants', 'platform'),
    ('platform.view_all_activity', 'View cross-tenant platform activity and billing status', 'platform'),
    ('platform.impersonate', 'Time-boxed, audited impersonation of a tenant login', 'platform'),
    ('agency.view_dashboard', 'View the tenant dashboard and reports', 'agency'),
    ('agency.manage_profile', 'Edit agency profile and commission rates', 'agency'),
    ('agency.create_sub_agency', 'Create new sub-agencies within a tenant', 'agency'),
    ('agency.manage_users', 'Invite/suspend users within a tenant (subject to role-hierarchy rules)', 'agency'),
    ('agency.manage_billing', 'View and change the tenant''s own plan/subscription', 'agency'),
    ('broadcaster.view', 'View the full tenant-wide broadcaster list and dashboard', 'broadcaster'),
    ('broadcaster.view_own_only', 'View only broadcasters/data assigned to or owned by this login', 'broadcaster'),
    ('broadcaster.assign', 'Assign broadcasters to a sub-agency', 'broadcaster'),
    ('broadcaster.upload', 'Upload monthly/daily broadcaster report CSVs', 'broadcaster'),
    ('broadcaster.manage_payouts', 'Manage broadcaster payout rules and mark payouts paid', 'broadcaster'),
    ('data.manage', 'Archive/manage uploaded periods (Data Management page)', 'data'),
    ('report.export', 'Export reports/data in the formats the plan allows', 'data'),
    ('audit.view', 'View security/audit history', 'data'),
    ('profile.manage', 'Manage own display name/avatar', 'profile')
ON CONFLICT (key) DO NOTHING;

INSERT INTO role_permissions (role_code, permission_key) VALUES
    ('platform_admin', 'platform.manage_businesses'),
    ('platform_admin', 'platform.view_all_activity'),
    ('platform_admin', 'profile.manage'),
    ('support_admin', 'platform.view_all_activity'),
    ('support_admin', 'platform.impersonate'),
    ('support_admin', 'profile.manage'),
    ('owner', 'agency.view_dashboard'),
    ('owner', 'agency.manage_profile'),
    ('owner', 'agency.create_sub_agency'),
    ('owner', 'agency.manage_users'),
    ('owner', 'agency.manage_billing'),
    ('owner', 'broadcaster.view'),
    ('owner', 'broadcaster.assign'),
    ('owner', 'broadcaster.upload'),
    ('owner', 'broadcaster.manage_payouts'),
    ('owner', 'data.manage'),
    ('owner', 'report.export'),
    ('owner', 'profile.manage'),
    ('agency_manager', 'agency.view_dashboard'),
    ('agency_manager', 'agency.manage_users'),
    ('agency_manager', 'broadcaster.view'),
    ('agency_manager', 'broadcaster.assign'),
    ('agency_manager', 'broadcaster.upload'),
    ('agency_manager', 'report.export'),
    ('agency_manager', 'profile.manage'),
    ('sub_agency', 'broadcaster.view_own_only'),
    ('sub_agency', 'profile.manage'),
    ('broadcaster', 'broadcaster.view_own_only'),
    ('broadcaster', 'profile.manage'),
    ('auditor', 'agency.view_dashboard'),
    ('auditor', 'audit.view'),
    ('auditor', 'report.export'),
    ('auditor', 'profile.manage'),
    ('trial_viewer', 'agency.view_dashboard'),
    ('trial_viewer', 'broadcaster.view')
ON CONFLICT (role_code, permission_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS agencies (
    business_id TEXT,
    agency_name TEXT,
    commission_pct NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, agency_name)
);

ALTER TABLE agencies
    ADD COLUMN IF NOT EXISTS commission_pct NUMERIC(5,2);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'agencies_commission_pct_range'
    ) THEN
        ALTER TABLE agencies
            ADD CONSTRAINT agencies_commission_pct_range
            CHECK (commission_pct IS NULL OR commission_pct BETWEEN 1 AND 20);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS raw_uploads (
    id SERIAL PRIMARY KEY,
    business_id TEXT,
    upload_id TEXT,
    uploaded_at TIMESTAMP,
    period TEXT,
    period_type TEXT,
    profile_url TEXT,
    broadcaster_name TEXT,
    first_name TEXT,
    last_name TEXT,
    is_new BOOLEAN,
    diamonds_earned NUMERIC,
    diamonds_redeemed NUMERIC,
    my_earnings_diamonds NUMERIC,
    streaming_days NUMERIC,
    streaming_hours NUMERIC,
    usd_earned NUMERIC,
    usd_redeemed NUMERIC,
    my_earnings_usd NUMERIC
);
CREATE INDEX IF NOT EXISTS idx_raw_uploads_lookup
    ON raw_uploads (business_id, period_type, period);

CREATE TABLE IF NOT EXISTS assignments (
    business_id TEXT,
    profile_url TEXT,
    broadcaster_name TEXT,
    sub_agency TEXT,
    assigned_at TIMESTAMP,
    PRIMARY KEY (business_id, profile_url)
);

CREATE TABLE IF NOT EXISTS assignment_log (
    id SERIAL PRIMARY KEY,
    business_id TEXT,
    profile_url TEXT,
    broadcaster_name TEXT,
    sub_agency TEXT,
    assigned_by TEXT,
    assigned_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS archived_periods (
    business_id TEXT,
    period TEXT,
    period_type TEXT,
    archived_at TIMESTAMP,
    PRIMARY KEY (business_id, period, period_type)
);

CREATE TABLE IF NOT EXISTS profiles (
    username TEXT PRIMARY KEY,
    display_name TEXT,
    avatar_base64 TEXT,
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS security_audit (
    id BIGSERIAL PRIMARY KEY,
    business_id TEXT,
    actor_username TEXT,
    actor_role TEXT,
    event_type TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_security_audit_business_time
    ON security_audit (business_id, created_at DESC);

CREATE TABLE IF NOT EXISTS broadcaster_payout_rules (
    business_id TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    broadcaster_name TEXT,
    effective_from TEXT NOT NULL,
    agency_rate_pct NUMERIC(5,2) NOT NULL,
    payout_rate_pct NUMERIC(5,2) NOT NULL,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, profile_url, effective_from),
    CONSTRAINT broadcaster_payout_rules_period_format
        CHECK (effective_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT broadcaster_payout_rules_agency_rate
        CHECK (agency_rate_pct BETWEEN 0 AND 20),
    CONSTRAINT broadcaster_payout_rules_payout_rate
        CHECK (payout_rate_pct BETWEEN 0 AND agency_rate_pct)
);
CREATE INDEX IF NOT EXISTS idx_payout_rules_effective
    ON broadcaster_payout_rules (business_id, profile_url, effective_from DESC);

CREATE TABLE IF NOT EXISTS broadcaster_payout_status (
    business_id TEXT NOT NULL,
    period TEXT NOT NULL,
    profile_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    paid_at TIMESTAMP,
    paid_by TEXT,
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (business_id, period, profile_url),
    CONSTRAINT broadcaster_payout_status_period_format
        CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    CONSTRAINT broadcaster_payout_status_value
        CHECK (status IN ('Pending', 'Paid'))
);
CREATE INDEX IF NOT EXISTS idx_payout_status_period
    ON broadcaster_payout_status (business_id, period, status);

-- The browser-facing Supabase API must never expose these tables. StreamOperiq
-- accesses Postgres only from the server, so anon/authenticated need no grants.
DO $$
DECLARE table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'businesses', 'users', 'memberships', 'subscriptions', 'roles', 'permissions',
        'role_permissions', 'agencies', 'raw_uploads',
        'assignments', 'assignment_log', 'archived_periods', 'profiles', 'security_audit',
        'broadcaster_payout_rules', 'broadcaster_payout_status'
    ] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon', table_name);
        END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            EXECUTE format('REVOKE ALL ON TABLE public.%I FROM authenticated', table_name);
        END IF;
    END LOOP;
END $$;
"""

RUNTIME_TABLES = (
    "businesses", "users", "memberships", "subscriptions", "roles", "permissions",
    "role_permissions", "agencies", "raw_uploads",
    "assignments", "assignment_log", "archived_periods", "profiles", "security_audit",
    "broadcaster_payout_rules", "broadcaster_payout_status",
)

RUNTIME_SEQUENCES = (
    "raw_uploads_id_seq", "assignment_log_id_seq", "security_audit_id_seq",
)

RUNTIME_TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE")
RUNTIME_SEQUENCE_PRIVILEGES = ("USAGE", "SELECT")


def _verify_runtime_permissions(conn):
    """Fail safely when the configured role lacks StreamOperiq runtime access."""
    missing = []
    with conn.cursor() as cur:
        for table in RUNTIME_TABLES:
            qualified = f"public.{table}"
            cur.execute("SELECT to_regclass(%s)", (qualified,))
            if cur.fetchone()[0] is None:
                missing.append(f"missing table {qualified}")
                continue
            for privilege in RUNTIME_TABLE_PRIVILEGES:
                cur.execute(
                    "SELECT has_table_privilege(current_user, %s, %s)",
                    (qualified, privilege),
                )
                if not cur.fetchone()[0]:
                    missing.append(f"{privilege} permission on {qualified}")
        for sequence in RUNTIME_SEQUENCES:
            qualified = f"public.{sequence}"
            cur.execute("SELECT to_regclass(%s)", (qualified,))
            if cur.fetchone()[0] is None:
                missing.append(f"missing sequence {qualified}")
                continue
            for privilege in RUNTIME_SEQUENCE_PRIVILEGES:
                cur.execute(
                    "SELECT has_sequence_privilege(current_user, %s, %s)",
                    (qualified, privilege),
                )
                if not cur.fetchone()[0]:
                    missing.append(f"{privilege} permission on {qualified}")
    if missing:
        raise RuntimeError(
            "The configured database role is missing required StreamOperiq runtime access: "
            + "; ".join(missing)
        )


@st.cache_resource(show_spinner=False)
def _pool():
    p = pg_pool.SimpleConnectionPool(
        1, 5, st.secrets["postgres"]["connection_string"],
        sslmode="require", connect_timeout=10,
    )
    conn = p.getconn()
    try:
        # Runtime connections never create/alter tables or permissions. Schema
        # changes must be run separately with scripts/run_migrations.py using a
        # temporary administrator connection.
        _verify_runtime_permissions(conn)
    finally:
        p.putconn(conn)
    return p


def get_database_role_posture() -> dict:
    """Return non-secret role properties used to verify least privilege."""
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_user, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            )
            row = cur.fetchone()
        return {
            "role": row[0], "superuser": bool(row[1]), "create_database": bool(row[2]),
            "create_role": bool(row[3]), "replication": bool(row[4]),
            "bypass_rls": bool(row[5]),
        }
    finally:
        p.putconn(conn)


def _query(sql, params=None, columns=None):
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            cols = columns or [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        p.putconn(conn)


def _execute(sql, params=None):
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
    finally:
        p.putconn(conn)


def _execute_values(sql, rows):
    if not rows:
        return
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, sql, rows)
        conn.commit()
    finally:
        p.putconn(conn)


# ---------------- businesses ----------------

def get_businesses() -> pd.DataFrame:
    return _query("SELECT business_id, business_name, status, created_at FROM businesses ORDER BY created_at")


def create_business(name: str) -> str:
    business_id = uuid.uuid4().hex[:8]
    _execute(
        "INSERT INTO businesses (business_id, business_name, status) VALUES (%s, %s, 'Active')",
        (business_id, name),
    )
    return business_id


def set_business_status(business_id: str, status: str):
    _execute("UPDATE businesses SET status=%s WHERE business_id=%s", (status, business_id))


def update_business_name(business_id: str, new_name: str):
    _execute("UPDATE businesses SET business_name=%s WHERE business_id=%s", (new_name, business_id))


def set_business_demo_flag(business_id: str, is_demo: bool):
    """Mark a business as demo/dummy data, excluding it from future billing
    and lifecycle enforcement (SaaS blueprint Sections 06/07). Used once by
    scripts/backfill_memberships.py for businesses that predate the SaaS
    launch; not exposed in the UI yet."""
    _execute("UPDATE businesses SET is_demo=%s WHERE business_id=%s", (bool(is_demo), business_id))


# ---------------- users (global table, business_id-tagged) ----------------

def _normalize_username(username: str) -> str:
    return str(username or "").strip().lower()


def password_policy_error(password: str):
    """Return a user-safe policy message, or None when the password is strong."""
    value = str(password or "")
    if len(value) < 12:
        return "Password must be at least 12 characters."
    if len(value) > 128:
        return "Password must be 128 characters or fewer."
    checks = (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]")
    if not all(re.search(pattern, value) for pattern in checks):
        return "Password must include uppercase, lowercase, a number, and a special character."
    return None

def get_all_users() -> pd.DataFrame:
    return _query(
        "SELECT username, name, password_hash, role, business_id, sub_agency, status, created_at "
        "FROM users ORDER BY created_at"
    )


def get_users(business_id: str) -> pd.DataFrame:
    return _query(
        "SELECT username, name, password_hash, role, business_id, sub_agency, status, created_at "
        "FROM users WHERE business_id=%s ORDER BY created_at",
        (business_id,),
    )


def get_user(username: str):
    df = _query("SELECT * FROM users WHERE lower(trim(username))=%s", (_normalize_username(username),))
    return None if df.empty else df.iloc[0]


def username_taken(username: str) -> bool:
    df = _query("SELECT 1 FROM users WHERE lower(trim(username))=%s", (_normalize_username(username),))
    return not df.empty


def create_user(username: str, name: str, password_plain: str, role: str,
                 business_id: str, sub_agency: str = "", status: str = "Active",
                 invited_by: str = "") -> tuple:
    import streamlit_authenticator as stauth
    username = _normalize_username(username)
    policy_error = password_policy_error(password_plain)
    if policy_error:
        return False, policy_error
    if username_taken(username):
        return False, f"'{username}' is already registered on this platform."
    password_hash = stauth.Hasher().hash(password_plain)
    # Written atomically with its membership row so users and memberships can
    # never drift apart for a login created after this change.
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, name, password_hash, role, business_id, sub_agency, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (username, name, password_hash, role, business_id, sub_agency, status),
            )
            cur.execute(
                "INSERT INTO memberships (business_id, username, role, sub_agency, status, invited_by) "
                "VALUES (%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (business_id, username) DO UPDATE SET "
                "role=EXCLUDED.role, sub_agency=EXCLUDED.sub_agency, status=EXCLUDED.status",
                (business_id, username, role, sub_agency, status, _normalize_username(invited_by)),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)
    return True, f"Created login for {username}."


def set_user_status(username: str, status: str):
    """Suspend/reactivate a login. Updates every membership row for this
    username in the same transaction, so a suspended account can never keep
    signing in through a stale 'Active' membership row (Section 10 of the
    SaaS blueprint: this check must hold even if a future code path reads
    membership status without re-checking users.status)."""
    normalized = _normalize_username(username)
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET status=%s WHERE lower(trim(username))=%s",
                (status, normalized),
            )
            cur.execute(
                "UPDATE memberships SET status=%s WHERE lower(trim(username))=%s",
                (status, normalized),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def reset_user_password(username: str, new_password_plain: str):
    import streamlit_authenticator as stauth
    policy_error = password_policy_error(new_password_plain)
    if policy_error:
        return False, policy_error
    _execute("UPDATE users SET password_hash=%s WHERE lower(trim(username))=%s",
              (stauth.Hasher().hash(new_password_plain), _normalize_username(username)))
    return True, "Password updated."


# ---------------- memberships ----------------

def get_memberships(username: str) -> pd.DataFrame:
    """Every business this login belongs to. Today a login has exactly one
    active row; ordering by created_at desc anticipates a future login
    holding more than one without changing behavior for anyone who doesn't."""
    return _query(
        "SELECT business_id, role, sub_agency, status, expires_at, created_at FROM memberships "
        "WHERE lower(trim(username))=%s ORDER BY created_at DESC",
        (_normalize_username(username),),
    )


def get_all_memberships() -> pd.DataFrame:
    return _query(
        "SELECT business_id, username, role, sub_agency, status, invited_by, "
        "expires_at, created_at FROM memberships ORDER BY created_at"
    )


def get_business_memberships(business_id: str) -> pd.DataFrame:
    return _query(
        "SELECT username, role, sub_agency, status, invited_by, created_at FROM memberships "
        "WHERE business_id=%s ORDER BY created_at",
        (business_id,),
    )


def set_membership_status(business_id: str, username: str, status: str):
    _execute(
        "UPDATE memberships SET status=%s WHERE business_id=%s AND lower(trim(username))=%s",
        (status, business_id, _normalize_username(username)),
    )


# ---------------- roles & permissions (Phase 3, schema/seed only — see PHASE_LOG.md) ----------------

def get_roles() -> pd.DataFrame:
    return _query("SELECT code, name, description FROM roles ORDER BY code")


def get_permissions() -> pd.DataFrame:
    return _query("SELECT key, description, category FROM permissions ORDER BY category, key")


def get_role_permissions() -> pd.DataFrame:
    """Every (role_code, permission_key) pair. Cheap to load in full and
    check in memory, the same pattern as memberships — this table is small
    and changes rarely."""
    return _query("SELECT role_code, permission_key FROM role_permissions")


def has_permission(role_code: str, permission_key: str) -> bool:
    """Not yet called from app.py — the accessor Phase 3's app.py migration
    will use in place of is_owner/is_sub_agency/is_platform_admin checks."""
    df = _query(
        "SELECT 1 FROM role_permissions WHERE role_code=%s AND permission_key=%s",
        (role_code, permission_key),
    )
    return not df.empty


def log_security_event(event_type: str, actor_username: str = "", actor_role: str = "",
                       business_id: str = None, target_type: str = "",
                       target_id: str = "", details: str = ""):
    """Append a non-secret audit record for a security-sensitive action."""
    _execute(
        "INSERT INTO security_audit "
        "(business_id, actor_username, actor_role, event_type, target_type, target_id, details) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (business_id, _normalize_username(actor_username), actor_role, event_type,
         target_type, str(target_id or "")[:500], str(details or "")[:2000]),
    )


def get_security_audit(business_id: str, limit: int = 200) -> pd.DataFrame:
    return _query(
        "SELECT created_at, actor_username, actor_role, event_type, target_type, target_id, details "
        "FROM security_audit WHERE business_id=%s ORDER BY created_at DESC LIMIT %s",
        (business_id, max(1, min(int(limit), 1000))),
    )


# ---------------- broadcaster payouts ----------------

def get_payout_rules(business_id: str) -> pd.DataFrame:
    """Return the full effective-dated rule history for one agency."""
    return _query(
        "SELECT profile_url, broadcaster_name, effective_from, agency_rate_pct, "
        "payout_rate_pct, created_by, created_at, updated_at "
        "FROM broadcaster_payout_rules WHERE business_id=%s "
        "ORDER BY effective_from DESC, broadcaster_name, profile_url",
        (business_id,),
    )


def get_effective_payout_rules(business_id: str, period: str) -> pd.DataFrame:
    """Return the latest rule at or before a reporting month for each profile."""
    return _query(
        "SELECT DISTINCT ON (profile_url) profile_url, broadcaster_name, effective_from, "
        "agency_rate_pct, payout_rate_pct, created_by, updated_at "
        "FROM broadcaster_payout_rules "
        "WHERE business_id=%s AND effective_from<=%s "
        "ORDER BY profile_url, effective_from DESC",
        (business_id, period),
    )


def save_payout_rule(business_id: str, profile_url: str, broadcaster_name: str,
                     effective_from: str, agency_rate_pct: float,
                     payout_rate_pct: float, created_by: str):
    """Create or replace a broadcaster rule without rewriting earlier months."""
    agency_rate = float(agency_rate_pct)
    payout_rate = float(payout_rate_pct)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(effective_from or "")):
        raise ValueError("Effective month must use YYYY-MM format.")
    if not 0 <= agency_rate <= 20:
        raise ValueError("Agency earning rate must be between 0% and 20%.")
    if not 0 <= payout_rate <= agency_rate:
        raise ValueError("Broadcaster payout rate cannot exceed the agency earning rate.")
    _execute(
        "INSERT INTO broadcaster_payout_rules "
        "(business_id, profile_url, broadcaster_name, effective_from, agency_rate_pct, "
        "payout_rate_pct, created_by, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,now(),now()) "
        "ON CONFLICT (business_id, profile_url, effective_from) DO UPDATE SET "
        "broadcaster_name=EXCLUDED.broadcaster_name, "
        "agency_rate_pct=EXCLUDED.agency_rate_pct, "
        "payout_rate_pct=EXCLUDED.payout_rate_pct, "
        "created_by=EXCLUDED.created_by, updated_at=now()",
        (business_id, profile_url, broadcaster_name, effective_from,
         agency_rate, payout_rate, _normalize_username(created_by)),
    )


def get_payout_statuses(business_id: str, period: str) -> pd.DataFrame:
    return _query(
        "SELECT profile_url, status, paid_at, paid_by, updated_at "
        "FROM broadcaster_payout_status WHERE business_id=%s AND period=%s",
        (business_id, period),
    )


def mark_payouts_paid(business_id: str, period: str, profile_urls: list,
                      paid_by: str):
    """Mark selected monthly payouts paid within the authenticated business."""
    clean_profiles = sorted({str(value).strip() for value in profile_urls if str(value).strip()})
    if not clean_profiles:
        return
    now = dt.datetime.utcnow()
    rows = [
        (business_id, period, profile_url, "Paid", now, _normalize_username(paid_by), now)
        for profile_url in clean_profiles
    ]
    _execute_values(
        "INSERT INTO broadcaster_payout_status "
        "(business_id, period, profile_url, status, paid_at, paid_by, updated_at) VALUES %s "
        "ON CONFLICT (business_id, period, profile_url) DO UPDATE SET "
        "status=EXCLUDED.status, paid_at=EXCLUDED.paid_at, "
        "paid_by=EXCLUDED.paid_by, updated_at=EXCLUDED.updated_at",
        rows,
    )


# ---------------- agencies ----------------

def get_agencies(business_id: str) -> list:
    df = _query("SELECT agency_name FROM agencies WHERE business_id=%s ORDER BY agency_name", (business_id,))
    return df["agency_name"].tolist() if not df.empty else []


def get_agency_details(business_id: str) -> pd.DataFrame:
    return _query(
        "SELECT agency_name, commission_pct, created_at FROM agencies "
        "WHERE business_id=%s ORDER BY agency_name",
        (business_id,),
    )


def get_agency_commission(business_id: str, agency_name: str):
    df = _query(
        "SELECT commission_pct FROM agencies WHERE business_id=%s AND agency_name=%s",
        (business_id, agency_name),
    )
    if df.empty or pd.isna(df.iloc[0]["commission_pct"]):
        return None
    return float(df.iloc[0]["commission_pct"])


def add_agency(name: str, business_id: str, commission_pct: float):
    _execute(
        "INSERT INTO agencies (business_id, agency_name, commission_pct) VALUES (%s,%s,%s) "
        "ON CONFLICT (business_id, agency_name) DO UPDATE "
        "SET commission_pct=EXCLUDED.commission_pct",
        (business_id, name, commission_pct),
    )


def update_agency_commission(business_id: str, agency_name: str, commission_pct: float):
    _execute(
        "UPDATE agencies SET commission_pct=%s WHERE business_id=%s AND agency_name=%s",
        (commission_pct, business_id, agency_name),
    )


# ---------------- raw_uploads ----------------

RAW_COLS = ["business_id", "upload_id", "uploaded_at", "period", "period_type", "profile_url",
            "broadcaster_name", "first_name", "last_name", "is_new", "diamonds_earned",
            "diamonds_redeemed", "my_earnings_diamonds", "streaming_days", "streaming_hours",
            "usd_earned", "usd_redeemed", "my_earnings_usd"]


def get_raw_uploads(business_id: str) -> pd.DataFrame:
    df = _query(f"SELECT {', '.join(RAW_COLS)} FROM raw_uploads WHERE business_id=%s", (business_id,))
    if df.empty:
        return df
    numeric_cols = ["diamonds_earned", "diamonds_redeemed", "my_earnings_diamonds",
                     "streaming_days", "streaming_hours", "usd_earned", "usd_redeemed", "my_earnings_usd"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def save_period(clean_df: pd.DataFrame, period: str, period_type: str, business_id: str):
    """Add/update uploaded profiles while preserving other rows in the same period."""
    if clean_df.empty:
        return
    now = dt.datetime.utcnow()
    upload_id = f"{period_type}_{period}_{now.isoformat()}"
    rows = []
    for _, r in clean_df.iterrows():
        rows.append((
            business_id, upload_id, now, period, period_type, r["profile_url"],
            r["broadcaster_name"], r["first_name"], r["last_name"], bool(r["is_new"]),
            float(r["diamonds_earned"]), float(r["diamonds_redeemed"]), float(r["my_earnings_diamonds"]),
            float(r["streaming_days"]), float(r["streaming_hours"]), float(r["usd_earned"]),
            float(r["usd_redeemed"]), float(r["my_earnings_usd"]),
        ))
    profiles = clean_df["profile_url"].astype(str).tolist()
    p = _pool()
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM raw_uploads WHERE business_id=%s AND period=%s "
                "AND period_type=%s AND profile_url = ANY(%s)",
                (business_id, period, period_type, profiles),
            )
            psycopg2.extras.execute_values(
                cur, f"INSERT INTO raw_uploads ({', '.join(RAW_COLS)}) VALUES %s", rows,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def clear_period(period: str, period_type: str, business_id: str):
    _execute(
        "DELETE FROM raw_uploads WHERE business_id=%s AND period=%s AND period_type=%s",
        (business_id, period, period_type),
    )


def list_periods(period_type: str, business_id: str, exclude_archived: bool = True) -> list:
    df = _query(
        "SELECT DISTINCT period FROM raw_uploads WHERE business_id=%s AND period_type=%s ORDER BY period",
        (business_id, period_type),
    )
    periods = df["period"].tolist() if not df.empty else []
    if exclude_archived:
        archived = get_archived_periods(business_id)
        periods = [p for p in periods if (p, period_type) not in archived]
    return periods


# ---------------- assignments ----------------

def get_assignments(business_id: str) -> pd.DataFrame:
    return _query(
        "SELECT profile_url, broadcaster_name, sub_agency, assigned_at FROM assignments WHERE business_id=%s",
        (business_id,),
    )


def assign_broadcasters(profile_urls: list, names: dict, sub_agency: str, business_id: str, assigned_by: str = ""):
    if not profile_urls:
        return
    now = dt.datetime.utcnow()
    rows = [(business_id, u, names.get(u, ""), sub_agency, now) for u in profile_urls]
    _execute_values(
        "INSERT INTO assignments (business_id, profile_url, broadcaster_name, sub_agency, assigned_at) "
        "VALUES %s ON CONFLICT (business_id, profile_url) DO UPDATE SET "
        "sub_agency=EXCLUDED.sub_agency, broadcaster_name=EXCLUDED.broadcaster_name, "
        "assigned_at=EXCLUDED.assigned_at",
        rows,
    )
    log_rows = [(business_id, u, names.get(u, ""), sub_agency, assigned_by, now) for u in profile_urls]
    _execute_values(
        "INSERT INTO assignment_log (business_id, profile_url, broadcaster_name, sub_agency, assigned_by, assigned_at) "
        "VALUES %s",
        log_rows,
    )


def get_assignment_history(profile_url: str, business_id: str) -> pd.DataFrame:
    return _query(
        "SELECT sub_agency, assigned_by, assigned_at FROM assignment_log "
        "WHERE business_id=%s AND profile_url=%s ORDER BY assigned_at DESC",
        (business_id, profile_url),
    )


def get_recent_platform_activity(limit: int = 12) -> pd.DataFrame:
    """Recent cross-agency operational events for the Platform Admin dashboard."""
    return _query(
        "SELECT al.business_id, b.business_name, al.broadcaster_name, al.sub_agency, "
        "al.assigned_by, al.assigned_at "
        "FROM assignment_log al LEFT JOIN businesses b ON b.business_id=al.business_id "
        "ORDER BY al.assigned_at DESC LIMIT %s",
        (int(limit),),
    )


# ---------------- archive ----------------

def get_archived_periods(business_id: str) -> set:
    df = _query("SELECT period, period_type FROM archived_periods WHERE business_id=%s", (business_id,))
    if df.empty:
        return set()
    return set(zip(df["period"], df["period_type"]))


def archive_period(period: str, period_type: str, business_id: str):
    _execute(
        "INSERT INTO archived_periods (business_id, period, period_type) VALUES (%s,%s,%s) "
        "ON CONFLICT (business_id, period, period_type) DO NOTHING",
        (business_id, period, period_type),
    )


def unarchive_period(period: str, period_type: str, business_id: str):
    _execute(
        "DELETE FROM archived_periods WHERE business_id=%s AND period=%s AND period_type=%s",
        (business_id, period, period_type),
    )


# ---------------- profiles (display name + avatar, independent of login) ----------------

def get_profile(username: str):
    df = _query("SELECT username, display_name, avatar_base64 FROM profiles WHERE username=%s", (username,))
    return None if df.empty else df.iloc[0].to_dict()


def upsert_profile(username: str, display_name: str = None, avatar_base64: str = None):
    existing = get_profile(username)
    new_display_name = display_name if display_name is not None else (existing["display_name"] if existing else None)
    new_avatar = avatar_base64 if avatar_base64 is not None else (existing["avatar_base64"] if existing else None)
    _execute(
        "INSERT INTO profiles (username, display_name, avatar_base64, updated_at) VALUES (%s,%s,%s, now()) "
        "ON CONFLICT (username) DO UPDATE SET display_name=EXCLUDED.display_name, "
        "avatar_base64=EXCLUDED.avatar_base64, updated_at=now()",
        (username, new_display_name, new_avatar),
    )
