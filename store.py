"""
Multi-tenant persistence layer, backed by Postgres (free on Supabase).
Every table except `businesses` and `users` carries a business_id column,
which is how each business's data stays completely walled off from every
other business sharing this same app.

Tables (auto-created on first run — nothing to set up by hand):
  businesses        one row per top-level business (ABC, DEF, ...)
  users             every login on the platform, tagged with role + business_id
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

-- The browser-facing Supabase API must never expose these tables. TangoOps
-- accesses Postgres only from the server, so anon/authenticated need no grants.
DO $$
DECLARE table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'businesses', 'users', 'agencies', 'raw_uploads', 'assignments',
        'assignment_log', 'archived_periods', 'profiles', 'security_audit'
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


@st.cache_resource(show_spinner=False)
def _pool():
    p = pg_pool.SimpleConnectionPool(
        1, 5, st.secrets["postgres"]["connection_string"],
        sslmode="require", connect_timeout=10,
    )
    conn = p.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        conn.commit()
    finally:
        p.putconn(conn)
    return p


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
                 business_id: str, sub_agency: str = "", status: str = "Active") -> tuple:
    import streamlit_authenticator as stauth
    username = _normalize_username(username)
    policy_error = password_policy_error(password_plain)
    if policy_error:
        return False, policy_error
    if username_taken(username):
        return False, f"'{username}' is already registered on this platform."
    password_hash = stauth.Hasher().hash(password_plain)
    _execute(
        "INSERT INTO users (username, name, password_hash, role, business_id, sub_agency, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (username, name, password_hash, role, business_id, sub_agency, status),
    )
    return True, f"Created login for {username}."


def set_user_status(username: str, status: str):
    _execute("UPDATE users SET status=%s WHERE lower(trim(username))=%s", (status, _normalize_username(username)))


def reset_user_password(username: str, new_password_plain: str):
    import streamlit_authenticator as stauth
    policy_error = password_policy_error(new_password_plain)
    if policy_error:
        return False, policy_error
    _execute("UPDATE users SET password_hash=%s WHERE lower(trim(username))=%s",
              (stauth.Hasher().hash(new_password_plain), _normalize_username(username)))
    return True, "Password updated."


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
