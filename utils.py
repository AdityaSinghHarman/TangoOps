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


MAX_PDF_ROWS = 2_000


def safe_pdf_bytes(df: pd.DataFrame, title: str, subtitle: str = "") -> bytes:
    """Render a DataFrame as a branded, paginated PDF table report.

    Growth-plan-and-above alternative to safe_csv_bytes - same data, a
    presentable layout for sharing outside the dashboard. Row count is
    capped independently of MAX_CSV_ROWS: a PDF table becomes unreadable
    long before it hits a spreadsheet's row limits.
    """
    import io as _io
    from html import escape as html_escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    if len(df) > MAX_PDF_ROWS:
        raise ValueError(f"The PDF has too many rows. Maximum allowed is {MAX_PDF_ROWS:,}.")

    brand = colors.HexColor("#211A4A")
    row_alt = colors.HexColor("#F5F5FA")
    grid = colors.HexColor("#DDDDDD")

    buffer = _io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=title,
    )
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"])]
    if subtitle:
        elements.append(Paragraph(subtitle, styles["Normal"]))
    elements.append(Spacer(1, 10))

    # Cells are wrapped Paragraphs on a fixed, evenly-split column width -
    # not plain strings - so a long broadcaster name or profile URL wraps
    # onto a second line instead of silently overflowing the page width
    # (which reportlab won't catch as an error; it just clips or overlaps).
    cell_style = ParagraphStyle("cell", fontName="Helvetica", fontSize=7.5, leading=9)
    header_style = ParagraphStyle("cell_header", parent=cell_style, textColor=colors.white,
                                   fontName="Helvetica-Bold")

    def _cell(value, style):
        text = "" if pd.isna(value) else html_escape(str(value))
        return Paragraph(text, style)

    header = [_cell(str(c).replace("_", " ").title(), header_style) for c in df.columns]
    body = [[_cell(v, cell_style) for v in row] for row in df.itertuples(index=False, name=None)]
    available_width = landscape(A4)[0] - 32 * mm
    col_width = available_width / max(1, len(df.columns))
    table = Table([header] + body, repeatRows=1, colWidths=[col_width] * len(df.columns))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), brand),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.25, grid),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, row_alt]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()


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


# ============================================================================
# Reward Plan Management System - calculation engine.
#
# Kept here (not in app.py) deliberately: this module's whole design intent
# is Streamlit-independent, unit-testable logic (see the module docstring),
# which the existing Payouts-page payout math never actually followed - it
# lives in app.py today, untested. This new engine follows the stated intent
# instead. store.py's CRUD layer calls into these functions; app.py never
# calls them directly.
# ============================================================================

DIAMONDS_PER_USD = 200  # mirrors app.py's existing constant of the same value and
                        # meaning; kept as a separate definition rather than an
                        # import to avoid a circular import (app.py imports utils,
                        # never the reverse).

# Tango's referral_statistics export (RAW_COLUMNS above) always carries
# diamonds/streaming-days/streaming-hours - load_tango_csv() rejects anything
# missing them - so these trigger types are evaluated automatically on every
# upload. signup_completed/first_live_completed have no corresponding column
# in that export at all, and manual_approval/custom are manual by definition,
# so those four can only ever advance via a confirmed manual_milestone_events
# row. This is a static classification, not a runtime "detection" step.
CSV_DERIVABLE_TRIGGER_TYPES = {
    "diamonds_earned_target", "diamonds_redeemed_target",
    "streaming_days_target", "streaming_hours_target",
    "diamonds_redeemed_threshold", "diamonds_earned_threshold",
}
MANUAL_ONLY_TRIGGER_TYPES = {
    "signup_completed", "first_live_completed", "manual_approval", "custom",
}
_RECRUITER_TRIGGER_METRIC = {
    "streaming_days_target": "streaming_days",
    "streaming_hours_target": "streaming_hours",
    "diamonds_earned_target": "diamonds_earned",
    "diamonds_redeemed_target": "diamonds_redeemed",
}

REWARD_STATUS_TRANSITIONS = {
    "Not Eligible":      {"In Progress"},
    "In Progress":       {"Milestone Reached", "Not Eligible"},
    "Milestone Reached": {"Awaiting Approval", "In Progress"},
    "Awaiting Approval": {"Approved", "Rejected"},
    "Approved":          {"Paid", "Cancelled"},
    "Rejected":          {"In Progress"},
    "Paid":              set(),
    "Cancelled":         {"In Progress"},
}


def validate_status_transition(old_status: str, new_status: str) -> bool:
    """Python-side mirror of the reward_calculations_enforce_status_transition
    DB trigger (store.SCHEMA) - lets the UI show a clear error before a round
    trip to the database. The DB trigger remains the real guarantee (a
    concurrent write can't bypass a Python-only check)."""
    if old_status == new_status:
        return True
    return new_status in REWARD_STATUS_TRANSITIONS.get(old_status, set())


def calculate_percentage_reward(diamonds_redeemed: float, agency_pct: float, payout_pct: float,
                                 min_diamonds: float = 0, max_monthly_payout=None) -> dict:
    """Broadcaster/recruiter percentage reward - the exact formula the
    existing Payouts page already uses (app.py), reimplemented here as one
    Reward Plan method ('percentage_cash'), never as a replacement for that
    page. redeemed_value = diamonds_redeemed / 200."""
    diamonds_redeemed = float(diamonds_redeemed or 0)
    if diamonds_redeemed < float(min_diamonds or 0):
        return {"redeemed_value": 0.0, "agency_earnings": 0.0, "broadcaster_reward": 0.0,
                "net_earnings": 0.0, "eligible": False}
    redeemed_value = diamonds_redeemed / DIAMONDS_PER_USD
    agency_earnings = redeemed_value * float(agency_pct or 0) / 100
    broadcaster_reward = redeemed_value * float(payout_pct or 0) / 100
    if max_monthly_payout is not None:
        broadcaster_reward = min(broadcaster_reward, float(max_monthly_payout))
    net_earnings = agency_earnings - broadcaster_reward
    return {
        "redeemed_value": round(redeemed_value, 2),
        "agency_earnings": round(agency_earnings, 2),
        "broadcaster_reward": round(broadcaster_reward, 2),
        "net_earnings": round(net_earnings, 2),
        "eligible": True,
    }


def calculate_fixed_reward(fixed_amount: float, unit: str) -> dict:
    """Flat per-period cash/coin amount, no diamond dependency."""
    if unit not in ("cash", "coins"):
        raise ValueError("unit must be 'cash' or 'coins'.")
    return {"amount": round(float(fixed_amount or 0), 2), "unit": unit}


def calculate_milestone_reward(performance_value: float, milestones: list, tier_calculation_mode: str,
                                frequency: str, already_awarded: set) -> dict:
    """Evaluate a broadcaster tier/milestone plan for one performance value.

    milestones: ascending-or-unsorted list of
        {milestone_key, threshold, reward_value, unit, name} dicts (entries
        with threshold=None, e.g. manual-only milestones, are ignored here -
        those go through calculate_recruiter_milestone_reward instead).
    already_awarded: milestone_keys this recipient has already received a
        reward for under the rules that apply to `frequency` (the caller
        decides the scope - lifetime: ever; monthly/period: this period
        only) - an engine-side defense-in-depth check on top of the
        database's partial unique indexes, so a duplicate never even
        reaches an INSERT attempt.

    tier_calculation_mode:
      - 'highest_only': award only the single highest not-yet-awarded
        threshold crossed.
      - 'cumulative': award every not-yet-awarded threshold at/below
        performance_value (each milestone's reward_value is independent and
        additive - already_awarded is what prevents a milestone re-firing
        across periods).
      - 'incremental_difference': treats each milestone's reward_value as a
        cumulative target *at* that tier, and awards only the difference
        between the highest eligible tier's value and the highest tier
        already awarded - i.e. the marginal reward for newly-crossed
        ground since the last time this recipient was evaluated, rather
        than the full tier value or a sum of tier values.

    Never sums cash and coins into one total - always returned separately.
    """
    eligible = sorted(
        (m for m in milestones if m.get("threshold") is not None
         and float(performance_value or 0) >= float(m["threshold"])),
        key=lambda m: float(m["threshold"]),
    )
    if not eligible:
        return {"awarded": [], "total_cash": 0.0, "total_coins": 0.0, "tier_reached": None}

    already_awarded = already_awarded or set()

    if tier_calculation_mode == "incremental_difference":
        highest = eligible[-1]
        if highest.get("milestone_key") in already_awarded:
            return {"awarded": [], "total_cash": 0.0, "total_coins": 0.0,
                     "tier_reached": float(highest["threshold"])}
        previously_awarded_values = [
            float(m["reward_value"]) for m in milestones
            if m.get("milestone_key") in already_awarded
        ]
        previous_value = max(previously_awarded_values, default=0.0)
        delta = round(float(highest["reward_value"]) - previous_value, 2)
        awarded = [{
            "milestone_key": highest.get("milestone_key"), "name": highest.get("name"),
            "threshold": float(highest["threshold"]), "reward_value": delta,
            "unit": highest["unit"],
        }] if delta > 0 else []
        return {
            "awarded": awarded,
            "total_cash": delta if awarded and highest["unit"] == "cash" else 0.0,
            "total_coins": delta if awarded and highest["unit"] == "coins" else 0.0,
            "tier_reached": float(highest["threshold"]),
        }

    candidates = [eligible[-1]] if tier_calculation_mode == "highest_only" else eligible
    awarded = []
    for milestone in candidates:
        if milestone.get("milestone_key") in already_awarded:
            continue
        awarded.append({
            "milestone_key": milestone.get("milestone_key"), "name": milestone.get("name"),
            "threshold": float(milestone["threshold"]), "reward_value": float(milestone["reward_value"]),
            "unit": milestone["unit"],
        })
    total_cash = round(sum(a["reward_value"] for a in awarded if a["unit"] == "cash"), 2)
    total_coins = round(sum(a["reward_value"] for a in awarded if a["unit"] == "coins"), 2)
    return {
        "awarded": awarded, "total_cash": total_cash, "total_coins": total_coins,
        "tier_reached": float(eligible[-1]["threshold"]),
    }


def calculate_recruiter_milestone_reward(broadcaster_performance: dict, milestone: dict,
                                          manual_event: dict = None, already_awarded: set = None,
                                          total_already_paid: float = 0.0) -> dict:
    """Evaluate one recruiter-plan milestone for one recruited broadcaster.
    CSV-derivable trigger types read straight from broadcaster_performance
    (diamonds/streaming values from the current uploaded period);
    manual-only trigger types require a manual_event with status='Approved'.
    max_total_reward_per_broadcaster (on the milestone) caps the running
    total across every milestone in the plan for this one broadcaster."""
    already_awarded = already_awarded or set()
    key = milestone.get("milestone_key")
    trigger_type = milestone.get("trigger_type")
    reward_value = float(milestone.get("reward_value", 0) or 0)
    unit = milestone.get("unit")
    cap = milestone.get("max_total_reward_per_broadcaster")

    if key in already_awarded and milestone.get("frequency") != "manual_repeatable":
        return {"eligible": False, "reward_value": 0.0, "unit": unit,
                "requires_manual_approval": False, "reason": "Already awarded."}

    if trigger_type in CSV_DERIVABLE_TRIGGER_TYPES:
        threshold = milestone.get("threshold")
        metric_key = _RECRUITER_TRIGGER_METRIC.get(trigger_type)
        value = float((broadcaster_performance or {}).get(metric_key, 0) or 0)
        eligible = threshold is None or value >= float(threshold)
    elif trigger_type in MANUAL_ONLY_TRIGGER_TYPES:
        eligible = bool(manual_event) and manual_event.get("status") == "Approved"
    else:
        eligible = False

    if not eligible:
        return {"eligible": False, "reward_value": 0.0, "unit": unit,
                "requires_manual_approval": bool(milestone.get("requires_manual_approval")),
                "reason": "Trigger condition not met."}

    payable = reward_value
    if cap is not None:
        remaining = max(0.0, float(cap) - float(total_already_paid or 0))
        payable = min(payable, remaining)

    return {
        "eligible": payable > 0, "reward_value": round(payable, 2), "unit": unit,
        "requires_manual_approval": bool(milestone.get("requires_manual_approval")),
        "reason": "" if payable > 0 else "Plan reward cap reached.",
    }


def diff_period_for_reward_flags(old_rows: pd.DataFrame, new_rows: pd.DataFrame) -> list:
    """profile_urls whose diamonds/streaming values changed between an old
    and a re-uploaded period. Drives the CSV-replace-flagging mechanism
    (req #15): the caller flags (never silently recalculates) any already-
    Approved/Paid reward for these profiles for that period."""
    if old_rows is None or old_rows.empty:
        return []
    compare_cols = ["diamonds_earned", "diamonds_redeemed", "streaming_days", "streaming_hours"]
    old_slim = old_rows[["profile_url"] + compare_cols].copy()
    new_slim = (
        new_rows[["profile_url"] + compare_cols].copy()
        if new_rows is not None and not new_rows.empty
        else pd.DataFrame(columns=["profile_url"] + compare_cols)
    )
    merged = old_slim.merge(new_slim, on="profile_url", how="left", suffixes=("_old", "_new"))
    changed = []
    for _, row in merged.iterrows():
        for col in compare_cols:
            new_val = row.get(f"{col}_new")
            if pd.isna(new_val) or not math.isclose(float(row[f"{col}_old"]), float(new_val), abs_tol=1e-6):
                changed.append(row["profile_url"])
                break
    return changed
