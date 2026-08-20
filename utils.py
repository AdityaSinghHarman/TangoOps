"""
Core data logic for StreamOperiq.
Kept separate from app.py so it can be unit-tested without Streamlit running.
"""
import math
import re

import pandas as pd

MAX_CSV_ROWS = 50_000
TANGO_PROFILE_RE = re.compile(r"^https://(?:www\.)?tango\.me/[A-Za-z0-9._~%/?=&+\-]+$", re.IGNORECASE)

# ---- Canonical column names coming out of the Tango "referral_statistics" export ----
RAW_COLUMNS = [
    "Profile Url", "First Name", "Last Name", "Is New",
    "Diamonds Earned", "Diamonds Redeemed", "My Earnings (Diamonds)",
    "Streaming Days", "Streaming Hours", "USD Earned", "USD Redeemed",
    "My Earnings (USD)",
]


def hms_to_hours(value: str) -> float:
    """Convert Tango's 'HH:MM' text (hours can exceed 24, e.g. '37:15') to decimal hours."""
    if pd.isna(value) or value == "":
        return 0.0
    try:
        h, m = str(value).split(":")
        return round(int(h) + int(m) / 60, 2)
    except (ValueError, AttributeError):
        return 0.0


def load_tango_csv(filepath_or_buffer) -> pd.DataFrame:
    """Read a raw Tango referral_statistics CSV and normalize it into a clean DataFrame."""
    df = pd.read_csv(filepath_or_buffer)

    if df.empty:
        raise ValueError("The CSV is empty.")
    if len(df) > MAX_CSV_ROWS:
        raise ValueError(f"The CSV has too many rows. Maximum allowed is {MAX_CSV_ROWS:,}.")

    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"This file doesn't look like a Tango referral_statistics export. "
            f"Missing columns: {missing}"
        )

    df = df.rename(columns={
        "Profile Url": "profile_url",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Is New": "is_new",
        "Diamonds Earned": "diamonds_earned",
        "Diamonds Redeemed": "diamonds_redeemed",
        "My Earnings (Diamonds)": "my_earnings_diamonds",
        "Streaming Days": "streaming_days",
        "Streaming Hours": "streaming_hours_raw",
        "USD Earned": "usd_earned",
        "USD Redeemed": "usd_redeemed",
        "My Earnings (USD)": "my_earnings_usd",
    })

    df["streaming_hours"] = df["streaming_hours_raw"].apply(hms_to_hours)
    df["is_new"] = df["is_new"].astype(str).str.strip().str.lower().eq("yes")
    df["last_name"] = df["last_name"].fillna("")
    df["broadcaster_name"] = (df["first_name"].astype(str).str.strip() + " " +
                               df["last_name"].astype(str).str.strip()).str.strip()

    if (df["broadcaster_name"].str.len() > 200).any():
        raise ValueError("A broadcaster name is longer than 200 characters.")

    # numeric safety
    for col in ["diamonds_earned", "diamonds_redeemed", "my_earnings_diamonds",
                "streaming_days", "usd_earned", "usd_redeemed", "my_earnings_usd"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    numeric_cols = [
        "diamonds_earned", "diamonds_redeemed", "my_earnings_diamonds",
        "streaming_days", "streaming_hours", "usd_earned", "usd_redeemed",
        "my_earnings_usd",
    ]
    if any((df[col] < 0).any() for col in numeric_cols):
        raise ValueError("The CSV contains negative activity or earnings values.")
    if any(not df[col].map(math.isfinite).all() for col in numeric_cols):
        raise ValueError("The CSV contains invalid or excessively large numeric values.")
    if (df["streaming_days"] > 31).any():
        raise ValueError("Streaming Days cannot exceed 31 in one report row.")
    if (df["streaming_hours"] > 744).any():
        raise ValueError("Streaming Hours cannot exceed 744 in one report row.")

    df["profile_url"] = df["profile_url"].astype(str).str.strip()
    invalid_urls = ~df["profile_url"].map(lambda value: bool(TANGO_PROFILE_RE.fullmatch(value)))
    if invalid_urls.any():
        raise ValueError("Every Profile Url must be a valid https://tango.me/ link.")
    df = df.drop_duplicates(subset="profile_url", keep="last")

    return df[[
        "profile_url", "broadcaster_name", "first_name", "last_name", "is_new",
        "diamonds_earned", "diamonds_redeemed", "my_earnings_diamonds",
        "streaming_days", "streaming_hours", "usd_earned", "usd_redeemed",
        "my_earnings_usd",
    ]]


def safe_csv_bytes(df: pd.DataFrame) -> bytes:
    """Export CSV data without allowing spreadsheet-formula injection."""
    safe = df.copy()
    dangerous = ("=", "+", "-", "@", "\t", "\r")
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(dangerous) else value
        )
    return safe.to_csv(index=False).encode("utf-8-sig")


def merge_assignments(stats_df: pd.DataFrame, assignments_df: pd.DataFrame) -> pd.DataFrame:
    """Attach a permanent recruitment source using the broadcaster profile URL."""
    out = stats_df.copy()
    if assignments_df is None or assignments_df.empty:
        out["sub_agency"] = "Agency Direct"
        return out

    a = assignments_df[["profile_url", "sub_agency"]].drop_duplicates(
        subset="profile_url", keep="last"
    )
    out = out.merge(a, on="profile_url", how="left")
    out["sub_agency"] = out["sub_agency"].fillna("Agency Direct")
    return out


def filter_by_agency(df: pd.DataFrame, agency: str) -> pd.DataFrame:
    if agency in (None, "All"):
        return df
    return df[df["sub_agency"] == agency]


def compute_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return dict(broadcasters=0, active=0, diamonds_redeemed=0,
                     days_worked=0, live_hours=0.0, my_earnings_usd=0.0)
    return dict(
        broadcasters=int(df["profile_url"].nunique()),
        active=int((df["streaming_days"] > 0).sum()),
        diamonds_redeemed=int(df["diamonds_redeemed"].sum()),
        days_worked=int(df["streaming_days"].sum()),
        live_hours=round(float(df["streaming_hours"].sum()), 1),
        my_earnings_usd=round(float(df["my_earnings_usd"].sum()), 2),
    )


def compare_periods(current_kpis: dict, previous_kpis: dict, metric: str = "diamonds_redeemed"):
    """Return (pct_change, direction) for a given metric between two KPI dicts."""
    cur = current_kpis.get(metric, 0)
    prev = previous_kpis.get(metric, 0)
    if prev == 0:
        pct = 100.0 if cur > 0 else 0.0
    else:
        pct = round((cur - prev) / prev * 100, 1)
    return pct, ("up" if pct >= 0 else "down")


def broadcaster_status(current_days: int, previous_days) -> str:
    """Classify a broadcaster's month-over-month state."""
    was_active = (previous_days is not None) and (previous_days > 0)
    is_active = current_days > 0
    existed_before = previous_days is not None
    if is_active and not existed_before:
        return "New"
    if is_active and was_active:
        return "Active"
    if is_active and not was_active:
        return "Reactivated"
    if not is_active and was_active:
        return "Went inactive"
    return "Inactive"


def add_growth_status(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
    """Attach status (New/Active/Growing/Declining/Went inactive/Inactive) and
    diamond growth % versus the previous period, using profile_url to match."""
    out = current_df.copy()
    if previous_df is None or previous_df.empty:
        out["status"] = out["streaming_days"].apply(
            lambda d: "New" if d > 0 else "Inactive"
        )
        out["prev_diamonds"] = None
        out["growth_pct"] = None
        return out

    prev_days = dict(zip(previous_df["profile_url"], previous_df["streaming_days"]))
    prev_diamonds = dict(zip(previous_df["profile_url"], previous_df["diamonds_redeemed"]))

    def _status(row):
        base = broadcaster_status(row["streaming_days"], prev_days.get(row["profile_url"]))
        if base == "Active":
            pd_ = prev_diamonds.get(row["profile_url"], 0)
            if pd_ > 0:
                change = (row["diamonds_redeemed"] - pd_) / pd_
                if change >= 0.10:
                    return "Growing"
                if change <= -0.10:
                    return "Declining"
        return base

    out["status"] = out.apply(_status, axis=1)
    out["prev_diamonds"] = out["profile_url"].map(prev_diamonds)
    out["growth_pct"] = out.apply(
        lambda r: round((r["diamonds_redeemed"] - r["prev_diamonds"]) / r["prev_diamonds"] * 100, 1)
        if r["prev_diamonds"] not in (None, 0) and not pd.isna(r["prev_diamonds"]) else None,
        axis=1,
    )
    return out


def diamonds_per_day(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["diamonds_per_day"] = out.apply(
        lambda r: round(r["diamonds_redeemed"] / r["streaming_days"], 1)
        if r["streaming_days"] > 0 else 0.0,
        axis=1,
    )
    return out


def retention_rate(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> float:
    """% of previously-active broadcasters (streaming_days > 0) still active now."""
    if previous_df is None or previous_df.empty:
        return None
    prev_active = set(previous_df[previous_df["streaming_days"] > 0]["profile_url"])
    if not prev_active:
        return None
    cur_active = set(current_df[current_df["streaming_days"] > 0]["profile_url"])
    still_active = prev_active & cur_active
    return round(len(still_active) / len(prev_active) * 100, 1)


def at_risk_broadcasters(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
    """Broadcasters who redeemed diamonds last period but streamed 0 days this period."""
    if previous_df is None or previous_df.empty:
        return current_df.iloc[0:0]
    prev_earners = set(previous_df[previous_df["diamonds_redeemed"] > 0]["profile_url"])
    at_risk = current_df[
        (current_df["profile_url"].isin(prev_earners)) & (current_df["streaming_days"] == 0)
    ]
    return at_risk


def attribution_completeness(df: pd.DataFrame) -> dict:
    total = df["profile_url"].nunique()
    if total == 0:
        return dict(total=0, assigned=0, unassigned=0, pct_assigned=0.0)
    assigned = df[df["sub_agency"] != "Agency Direct"]["profile_url"].nunique()
    unassigned = total - assigned
    return dict(total=total, assigned=assigned, unassigned=unassigned,
                pct_assigned=round(assigned / total * 100, 1))


def leaderboard(df: pd.DataFrame, n: int = 5, metric: str = "diamonds_redeemed") -> pd.DataFrame:
    return df.sort_values(metric, ascending=False).head(n)


def broadcaster_health_score(current_df: pd.DataFrame, previous_df: pd.DataFrame = None) -> int:
    """Explainable 0-100 operating score for the selected broadcaster roster.

    The score rewards active participation, retention, positive diamond movement,
    and consistent streaming. It intentionally uses only data already uploaded to
    StreamOperiq, so no paid AI service or hidden model is involved.
    """
    if current_df is None or current_df.empty:
        return 0
    total = max(1, current_df["profile_url"].nunique())
    active_rate = (current_df["streaming_days"] > 0).sum() / total
    consistency = min(1.0, float(current_df["streaming_days"].mean()) / 18.0)
    retention = retention_rate(current_df, previous_df) if previous_df is not None and not previous_df.empty else None
    retention_factor = (retention / 100) if retention is not None else active_rate
    current_diamonds = float(current_df["diamonds_redeemed"].sum())
    if previous_df is not None and not previous_df.empty:
        previous_diamonds = float(previous_df["diamonds_redeemed"].sum())
        growth_factor = min(1.0, max(0.0, 0.5 + ((current_diamonds - previous_diamonds) / max(previous_diamonds, 1)) * 1.5))
    else:
        growth_factor = 0.5
    score = active_rate * 35 + retention_factor * 30 + consistency * 20 + growth_factor * 15
    return int(round(min(100, max(0, score))))


def data_quality_score(df: pd.DataFrame) -> int:
    """Return a transparent completeness/validity score for an uploaded period."""
    if df is None or df.empty:
        return 0
    required = ["profile_url", "broadcaster_name", "diamonds_redeemed", "streaming_days", "streaming_hours"]
    present = [c for c in required if c in df.columns]
    if not present:
        return 0
    complete = df[present].notna().mean().mean()
    unique_profiles = df["profile_url"].nunique() / max(1, len(df)) if "profile_url" in df.columns else 0
    numeric_valid = 1.0
    for col in ["diamonds_redeemed", "streaming_days", "streaming_hours"]:
        if col in df.columns:
            numeric_valid -= float((pd.to_numeric(df[col], errors="coerce") < 0).mean()) / 3
    return int(round(min(100, max(0, complete * 55 + unique_profiles * 25 + numeric_valid * 20))))


def performance_target(current_value: float, previous_value: float, growth_goal: float = 0.08) -> dict:
    """Create a dynamic target from the prior period and return progress details."""
    current_value = float(current_value or 0)
    previous_value = float(previous_value or 0)
    target = previous_value * (1 + growth_goal) if previous_value > 0 else current_value
    progress = (current_value / target * 100) if target > 0 else 0
    return {
        "target": round(target, 2),
        "progress_pct": round(progress, 1),
        "remaining": round(max(0, target - current_value), 2),
        "ahead": current_value >= target and target > 0,
    }
