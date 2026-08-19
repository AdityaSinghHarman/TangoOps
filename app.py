import datetime as dt
import re
import secrets as pysecrets
import string
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import streamlit_authenticator as stauth

import utils
import store

st.set_page_config(page_title="TangoOps – Agency Control", layout="wide", page_icon="\u25c8")

# ---------------------------------------------------------------- styling ---
st.markdown("""
<style>
:root{ --brand:#3F6B1E; --brand-soft:#EEF3E7; --ink:#1C1D1A; --card-radius:14px; --border:#E3E3DD; }

.kpi-card{
  background:#FFFFFF; border:1px solid var(--border); border-radius:var(--card-radius);
  padding:20px 22px; margin-bottom:14px;
  transition:box-shadow .15s ease, transform .15s ease;
}
.kpi-card:hover{ box-shadow:0 6px 20px rgba(28,29,26,0.07); transform:translateY(-1px); }
.kpi-card.dark{ background:linear-gradient(135deg,#1C1D1A 0%,#2B2D26 100%); color:#fff; border:none; }
.kpi-label{ font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; opacity:0.55; margin-bottom:8px; }
.kpi-value{ font-size:1.75rem; font-weight:700; letter-spacing:-0.02em; }

section[data-testid="stSidebar"] .stButton>button{
  text-align:left; justify-content:flex-start; font-weight:500; border:1px solid transparent;
}
section[data-testid="stSidebar"] .stButton>button:hover{ background:#F6F6F3; border-color:var(--border); }
section[data-testid="stSidebar"] .stButton>button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  background:var(--brand-soft) !important; color:var(--brand) !important;
  border:1px solid var(--brand-soft) !important; box-shadow:none !important; font-weight:600;
}

h1, h2, h3 { letter-spacing:-0.02em; }
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, dark=False):
    cls = "kpi-card dark" if dark else "kpi-card"
    st.markdown(f"""<div class="{cls}"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div></div>""", unsafe_allow_html=True)


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


# ---------------------------------------------------------------- auth -----
@st.cache_data(ttl=30, show_spinner=False)
def load_all_users_df():
    return store.get_all_users()


@st.cache_data(ttl=30, show_spinner=False)
def load_businesses_df():
    return store.get_businesses()


def build_credentials():
    boot = st.secrets["bootstrap_admin"]
    boot_hash = stauth.Hasher().hash(boot["password"])

    creds = {
        "usernames": {
            boot["username"]: {
                "name": boot["name"],
                "email": boot["username"],
                "password": boot_hash,
            }
        }
    }

    users_df = load_all_users_df()
    businesses_df = load_businesses_df()

    active_business_ids = set(
        businesses_df[businesses_df["status"] == "Active"]["business_id"]
    ) if not businesses_df.empty else set()

    if not users_df.empty:
        active = users_df[
            (users_df["status"] == "Active")
            & (users_df["business_id"].isin(active_business_ids))
        ]

        for _, row in active.iterrows():
            creds["usernames"][row["username"]] = {
                "name": row["name"],
                "email": row["username"],
                "password": row["password_hash"],
            }

    # Ensure Streamlit Secrets always controls the Platform Admin login.
    creds["usernames"][boot["username"]] = {
        "name": boot["name"],
        "email": boot["username"],
        "password": boot_hash,
    }

    return creds, boot["username"]

credentials, bootstrap_username = build_credentials()
authenticator = stauth.Authenticate(
    credentials,
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    st.secrets["cookie"]["expiry_days"],
    auto_hash=False,
)

authenticator.login(location="main")
auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("Username or password is incorrect.")
    st.stop()
elif auth_status is None:
    st.info("Enter your email and password to continue.")
    st.stop()

display_name = st.session_state.get("name", "")
username = st.session_state.get("username", "")


def current_user_context():
    """Returns (role, business_id, sub_agency)."""
    if username == bootstrap_username:
        return "platform_admin", None, None
    users_df = load_all_users_df()
    if users_df.empty:
        return "platform_admin", None, None
    row = users_df[users_df["username"] == username]
    if row.empty:
        return "platform_admin", None, None
    r = row.iloc[0]
    return r["role"], r["business_id"], (r["sub_agency"] if r["role"] == "sub_agency" else None)


user_role, user_business_id, user_agency = current_user_context()
is_platform_admin = user_role == "platform_admin"
is_owner = user_role == "owner"
is_sub_agency = user_role == "sub_agency"
business_id = user_business_id

business_name = ""
if business_id:
    biz_row = load_businesses_df()
    biz_row = biz_row[biz_row["business_id"] == business_id]
    business_name = biz_row.iloc[0]["business_name"] if not biz_row.empty else ""

if "page" not in st.session_state:
    st.session_state.page = "Businesses" if is_platform_admin else "Admin"
if "selected_profile_url" not in st.session_state:
    st.session_state.selected_profile_url = None


def nav_button(label, page_key):
    if st.sidebar.button(label, width='stretch',
                          type="primary" if st.session_state.page == page_key else "secondary"):
        st.session_state.page = page_key
        st.rerun()


with st.sidebar:
    st.markdown("### \u25c8 TangoOps")
    st.caption("AGENCY CONTROL")
    if business_name:
        st.caption(business_name)
    st.write("")
    if is_platform_admin:
        nav_button("Businesses", "Businesses")
    elif is_owner:
        nav_button("Admin", "Admin")
        nav_button("Statistics", "Statistics")
        st.caption("BROADCASTERS")
        nav_button("Broadcasters", "Broadcasters")
        nav_button("Assign broadcasters", "Assign")
        st.caption("SUB-AGENCIES")
        nav_button("Sub-agency management", "SubAgencies")
        nav_button("Create sub-agency", "CreateAgency")
        st.caption("UPLOAD REPORTS")
        nav_button("Monthly report", "UploadMonthly")
        nav_button("Daily report", "UploadDaily")
        st.caption("ADMINISTRATION")
        nav_button("User access", "UserAccess")
        nav_button("Data management", "DataManagement")
    else:
        nav_button("Dashboard", "Admin")
        nav_button("My broadcasters", "Broadcasters")
        nav_button("Upload report", "UploadMonthly")
    st.write("")
    st.caption(f"Signed in as **{display_name}**")
    authenticator.logout("Sign out", "sidebar")

# --------------------------------------------------------- shared loaders --
@st.cache_data(ttl=60, show_spinner=False)
def load_all_raw(biz_id):
    return store.get_raw_uploads(biz_id)


@st.cache_data(ttl=60, show_spinner=False)
def load_assignments(biz_id):
    return store.get_assignments(biz_id)


@st.cache_data(ttl=60, show_spinner=False)
def load_agencies(biz_id):
    return store.get_agencies(biz_id)


@st.cache_data(ttl=30, show_spinner=False)
def load_business_users(biz_id):
    return store.get_users(biz_id)


def refresh_caches():
    load_all_raw.clear()
    load_assignments.clear()
    load_agencies.clear()
    load_all_users_df.clear()
    load_businesses_df.clear()
    load_business_users.clear()


def period_data(period, period_type, force_agency=None):
    raw = load_all_raw(business_id)
    if raw.empty:
        return raw
    subset = raw[(raw["period"] == period) & (raw["period_type"] == period_type)].copy()
    merged = utils.merge_assignments(subset, load_assignments(business_id))
    if force_agency:
        merged = utils.filter_by_agency(merged, force_agency)
    return merged


def agency_filter_widget(df, key):
    if not is_owner:
        return utils.filter_by_agency(df, user_agency), user_agency
    agencies = ["All"] + load_agencies(business_id) + ["Unassigned"]
    choice = st.selectbox("Sub-agency", agencies, key=key)
    return utils.filter_by_agency(df, choice), choice


def previous_period_of(period, period_type):
    periods = sorted(set(store.list_periods(period_type, business_id) + [period]), reverse=True)
    idx = periods.index(period)
    remaining = periods[idx + 1:]
    return remaining[0] if remaining else None


# ============================================================== BUSINESSES
if st.session_state.page == "Businesses":
    if not is_platform_admin:
        st.error("Platform admin access only.")
        st.stop()
    st.title("Businesses")
    st.caption("Each business below gets its own completely separate broadcasters, sub-agencies, and logins.")

    st.markdown("##### Create business")
    biz_name = st.text_input("Business name", key="biz_name")
    st.markdown("###### Owner login for this business")
    c1, c2 = st.columns(2)
    with c1:
        owner_email = st.text_input("Owner email", key="biz_owner_email")
        owner_name = st.text_input("Owner name", key="biz_owner_name")
    with c2:
        st.write("")
        if st.button("Generate password"):
            alphabet = string.ascii_letters + string.digits
            st.session_state.biz_owner_password = "".join(pysecrets.choice(alphabet) for _ in range(10))
        owner_password = st.text_input("Owner password", key="biz_owner_password")

    if st.button("Create business", type="primary", disabled=not biz_name.strip()):
        if not is_valid_email(owner_email):
            st.error("Enter a valid owner email address.")
            st.stop()
        if not owner_password.strip():
            st.error("Enter a password, or use Generate password.")
            st.stop()
        new_business_id = store.create_business(biz_name.strip())
        ok, msg = store.create_user(
            owner_email.strip(), owner_name.strip() or owner_email.strip(),
            owner_password, "owner", new_business_id,
        )
        if not ok:
            st.error(msg)
            st.stop()
        refresh_caches()
        st.toast(f"Created {biz_name.strip()} with owner login {owner_email.strip()}.", icon="\u2705")
        st.rerun()

    st.markdown("##### Existing businesses")
    businesses = store.get_businesses()
    if businesses.empty:
        st.caption("No businesses yet.")
    else:
        for _, b in businesses.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                owners_df = store.get_users(b["business_id"])
                owner_count = int((owners_df["role"] == "owner").sum()) if not owners_df.empty else 0
                agency_count = len(store.get_agencies(b["business_id"]))
                c1.markdown(f"**{b['business_name']}**  \n`{b['business_id']}` \u00b7 "
                            f"{owner_count} owner login(s) \u00b7 {agency_count} sub-agencies \u00b7 "
                            f"status: {b['status']}")
                with c2:
                    if b["status"] == "Active":
                        if st.button("Disable", key=f"disbiz_{b['business_id']}"):
                            store.set_business_status(b["business_id"], "Disabled")
                            refresh_caches()
                            st.rerun()
                    else:
                        if st.button("Enable", key=f"enbiz_{b['business_id']}"):
                            store.set_business_status(b["business_id"], "Active")
                            refresh_caches()
                            st.rerun()

# ==================================================================== ADMIN
elif st.session_state.page == "Admin":
    st.markdown("#### Admin panel" if is_owner else "#### My dashboard")
    st.title(business_name if is_owner else f"{user_agency} dashboard")

    monthly_periods = store.list_periods("monthly", business_id)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet. Go to **Upload report** in the sidebar.")
        st.stop()

    current_period = st.selectbox("Month", sorted(monthly_periods, reverse=True), key="admin_month")
    df_current_all = period_data(current_period, "monthly")
    df_current, agency_choice = agency_filter_widget(df_current_all, "admin_agency")

    previous_period = previous_period_of(current_period, "monthly")
    df_previous = period_data(previous_period, "monthly") if previous_period else pd.DataFrame()
    scope_agency = agency_choice if is_owner else user_agency
    if not df_previous.empty:
        df_previous = utils.filter_by_agency(df_previous, scope_agency)

    if is_owner:
        attribution_all = utils.attribution_completeness(df_current_all)
        if attribution_all["unassigned"] > 0:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.warning(
                    f"{attribution_all['unassigned']} broadcasters need assignment "
                    f"({attribution_all['pct_assigned']}% of roster attributed)."
                )
            with c2:
                st.write("")
                if st.button("Review & assign"):
                    st.session_state.page = "Assign"
                    st.rerun()

    kpis = utils.compute_kpis(df_current)
    prev_kpis = utils.compute_kpis(df_previous) if not df_previous.empty else {}
    n_agencies = max(1, len(load_agencies(business_id))) if is_owner else 1
    avg_dpb = round(kpis["diamonds_redeemed"] / kpis["broadcasters"], 1) if kpis["broadcasters"] else 0

    c1, c2 = st.columns(2)
    with c1: kpi_card("Total broadcasters", f"{kpis['broadcasters']:,}")
    with c2: kpi_card("Active broadcasters", f"{kpis['active']:,}")
    c3, c4 = st.columns(2)
    with c3: kpi_card("Diamonds redeemed", f"{kpis['diamonds_redeemed']:,}")
    with c4: kpi_card("Days streamed", f"{kpis['days_worked']:,}")
    c5, c6 = st.columns(2)
    with c5: kpi_card("Active sub-agencies", n_agencies)
    with c6: kpi_card("Avg diamonds / broadcaster", f"{avg_dpb:,}")

    st.markdown("#### Insights")
    retention = utils.retention_rate(df_current, df_previous) if not df_previous.empty else None
    at_risk_df = utils.at_risk_broadcasters(df_current, df_previous) if not df_previous.empty else df_current.iloc[0:0]
    dpd_df = utils.diamonds_per_day(df_current)
    avg_dpd = round(dpd_df["diamonds_per_day"].mean(), 1) if not dpd_df.empty else 0

    i1, i2, i3 = st.columns(3)
    with i1: kpi_card("Retention rate", f"{retention}%" if retention is not None else "\u2014")
    with i2: kpi_card("At-risk broadcasters", len(at_risk_df))
    with i3:
        if is_owner:
            kpi_card("Attribution complete", f"{attribution_all['pct_assigned']}%")
        else:
            kpi_card("Avg diamonds / day", f"{avg_dpd:,}")

    if len(at_risk_df) > 0:
        with st.expander(f"{len(at_risk_df)} broadcaster(s) earned diamonds last period, streamed 0 days this period"):
            st.dataframe(
                at_risk_df[["broadcaster_name", "sub_agency"]].reset_index(drop=True),
                hide_index=True, width='stretch',
            )

    st.markdown("#### Performance comparison")
    if prev_kpis:
        pct, direction = utils.compare_periods(kpis, prev_kpis, "diamonds_redeemed")
        st.caption(f"{previous_period} vs {current_period} \u00b7 diamonds redeemed")
        fig = go.Figure()
        metrics = ["broadcasters", "active", "diamonds_redeemed", "days_worked"]
        fig.add_trace(go.Bar(name=current_period, x=metrics, y=[kpis[m] for m in metrics],
                              marker_color="#3F6B1E"))
        fig.add_trace(go.Bar(name=previous_period, x=metrics, y=[prev_kpis[m] for m in metrics],
                              marker_color="#C8C6BC"))
        fig.update_layout(barmode="group", height=360,
                           title=f"{'+' if pct >= 0 else ''}{pct}% change in diamonds redeemed")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Upload a second month to see the month-over-month comparison here.")

    st.markdown("#### Top performers this period")
    top5 = utils.leaderboard(df_current, 5)
    if top5.empty:
        st.caption("No data yet.")
    else:
        cols = ["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"] if is_owner \
            else ["broadcaster_name", "diamonds_redeemed", "streaming_days"]
        st.dataframe(top5[cols], hide_index=True, width='stretch')

# ================================================================ STATISTICS
elif st.session_state.page == "Statistics":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Statistics")
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="stats_month")
    df_current = period_data(current_period, "monthly")
    df_current, agency_choice = agency_filter_widget(df_current, "stats_agency")

    prev_period = previous_period_of(current_period, "monthly")
    df_prev = utils.filter_by_agency(period_data(prev_period, "monthly"), agency_choice) if prev_period else pd.DataFrame()

    if df_current.empty:
        st.info("No broadcasters in this view.")
    else:
        df_current = utils.add_growth_status(df_current, df_prev)
        df_current = utils.diamonds_per_day(df_current)
        show_cols = ["broadcaster_name", "sub_agency", "status", "streaming_days",
                     "streaming_hours", "diamonds_redeemed", "diamonds_per_day", "growth_pct", "is_new"]
        st.dataframe(
            df_current[show_cols].sort_values("diamonds_redeemed", ascending=False),
            width='stretch', hide_index=True
        )
        st.download_button(
            "Export this view as CSV",
            df_current[show_cols].to_csv(index=False).encode("utf-8"),
            file_name=f"statistics_{current_period}_{agency_choice}.csv",
        )

# =============================================================== BROADCASTERS
elif st.session_state.page == "Broadcasters":
    st.title("Broadcasters" if is_owner else "My broadcasters")
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="bl_month")
    force = None if is_owner else user_agency
    df = period_data(current_period, "monthly", force_agency=force)
    prev_period = previous_period_of(current_period, "monthly")
    df_prev = period_data(prev_period, "monthly", force_agency=force) if prev_period else pd.DataFrame()

    if df.empty:
        st.info("No broadcasters in this view yet.")
        st.stop()

    df = utils.add_growth_status(df, df_prev)
    df = utils.diamonds_per_day(df)

    search = st.text_input("Search broadcasters", key="bl_search")
    col1, col2 = st.columns(2)
    with col1:
        agency_pick = st.selectbox("Sub-agency", ["All"] + load_agencies(business_id) + ["Unassigned"], key="bl_agency") \
            if is_owner else "All"
    with col2:
        status_pick = st.multiselect("Status", sorted(df["status"].dropna().unique().tolist()), key="bl_status")

    view = df.copy()
    if search:
        view = view[view["broadcaster_name"].str.contains(search, case=False, na=False)]
    if is_owner and agency_pick != "All":
        view = utils.filter_by_agency(view, agency_pick)
    if status_pick:
        view = view[view["status"].isin(status_pick)]

    sort_choice = st.selectbox(
        "Sort by", ["Diamonds, high to low", "Days streamed", "Growth %", "Name, A-Z"], key="bl_sort"
    )
    sort_map = {"Diamonds, high to low": ("diamonds_redeemed", False), "Days streamed": ("streaming_days", False),
                "Growth %": ("growth_pct", False), "Name, A-Z": ("broadcaster_name", True)}
    col, asc = sort_map[sort_choice]
    view = view.sort_values(col, ascending=asc, na_position="last").reset_index(drop=True)

    st.caption(f"{len(view)} broadcaster(s)")
    show_cols = ["broadcaster_name", "sub_agency", "status", "diamonds_redeemed",
                 "streaming_days", "diamonds_per_day", "growth_pct"] if is_owner else \
                ["broadcaster_name", "status", "diamonds_redeemed", "streaming_days", "diamonds_per_day", "growth_pct"]
    event = st.dataframe(
        view[show_cols], hide_index=True, width='stretch',
        on_select="rerun", selection_mode="single-row", key="bl_table",
    )
    rows = event.selection.rows if hasattr(event, "selection") else []
    if rows:
        chosen = view.iloc[rows[0]]
        if st.button(f"View {chosen['broadcaster_name']} \u2192", type="primary"):
            st.session_state.selected_profile_url = chosen["profile_url"]
            st.session_state.page = "BroadcasterDetail"
            st.rerun()

# ============================================================ BROADCASTER DETAIL
elif st.session_state.page == "BroadcasterDetail":
    profile_url = st.session_state.get("selected_profile_url")
    if not profile_url:
        st.info("Pick a broadcaster from the Broadcasters list first.")
        if st.button("Go to broadcasters"):
            st.session_state.page = "Broadcasters"
            st.rerun()
        st.stop()

    raw = load_all_raw(business_id)
    hist = raw[(raw["profile_url"] == profile_url) & (raw["period_type"] == "monthly")].sort_values("period") \
        if not raw.empty else raw
    if hist.empty:
        st.warning("No data found for this broadcaster.")
        st.stop()

    assignments = load_assignments(business_id)
    a_row = assignments[assignments["profile_url"] == profile_url] if not assignments.empty else assignments
    sub_agency = a_row.iloc[0]["sub_agency"] if not a_row.empty else "Unassigned"

    if not is_owner and sub_agency != user_agency:
        st.error("You don't have access to this broadcaster.")
        st.stop()

    if st.button("\u2190 Back to broadcasters"):
        st.session_state.page = "Broadcasters"
        st.rerun()

    latest = hist.iloc[-1]
    prev = hist.iloc[-2] if len(hist) > 1 else None

    st.title(latest["broadcaster_name"])
    st.caption(f"{profile_url}  \u00b7  {sub_agency}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("This period", f"{int(latest['diamonds_redeemed']):,}")
    c2.metric("Previous period", f"{int(prev['diamonds_redeemed']):,}" if prev is not None else "\u2014")
    c3.metric("Days streamed", int(latest["streaming_days"]))
    status = utils.broadcaster_status(latest["streaming_days"], prev["streaming_days"] if prev is not None else None)
    c4.metric("Status", status)

    st.markdown("###### Diamonds, all uploaded months")
    st.line_chart(hist.set_index("period")["diamonds_redeemed"], height=220)
    st.markdown("###### Days streamed, all uploaded months")
    st.bar_chart(hist.set_index("period")["streaming_days"], height=160)

    st.markdown("###### Assignment history")
    log = store.get_assignment_history(profile_url, business_id)
    if log.empty:
        st.caption("No assignment recorded yet.")
    else:
        for _, r in log.iterrows():
            when = str(r["assigned_at"])[:10]
            by = r["assigned_by"] or "owner"
            st.write(f"**Assigned to {r['sub_agency']}** \u2014 {when} by {by}")

# ================================================================ SUB-AGENCIES
elif st.session_state.page == "SubAgencies":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Sub-agency management")
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="sa_month")
    df = period_data(current_period, "monthly")
    prev_period = previous_period_of(current_period, "monthly")
    df_prev = period_data(prev_period, "monthly") if prev_period else pd.DataFrame()

    agencies = load_agencies(business_id)
    rows = []
    for a in agencies + ["Unassigned"]:
        sub = utils.filter_by_agency(df, a)
        sub_prev = utils.filter_by_agency(df_prev, a) if not df_prev.empty else pd.DataFrame()
        k = utils.compute_kpis(sub)
        pk = utils.compute_kpis(sub_prev) if not sub_prev.empty else {}
        pct, _ = utils.compare_periods(k, pk, "diamonds_redeemed") if pk else (None, None)
        rows.append(dict(agency=a, broadcasters=k["broadcasters"], active=k["active"],
                          diamonds=k["diamonds_redeemed"], days=k["days_worked"], growth=pct))
    summary = pd.DataFrame(rows)

    sort_choice = st.selectbox(
        "Sort by", ["Diamonds", "Growth", "Active broadcasters", "Days streamed", "Broadcaster count"], key="sa_sort"
    )
    sort_map = {"Diamonds": "diamonds", "Growth": "growth", "Active broadcasters": "active",
                "Days streamed": "days", "Broadcaster count": "broadcasters"}
    summary = summary.sort_values(sort_map[sort_choice], ascending=False, na_position="last")

    for _, r in summary.iterrows():
        with st.container(border=True):
            gcol, bcol = st.columns([3, 1])
            gcol.markdown(f"**{r['agency']}**")
            if r["growth"] is not None:
                arrow = "\u25b2" if r["growth"] >= 0 else "\u25bc"
                bcol.markdown(f"{arrow} {r['growth']}%")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Broadcasters", r["broadcasters"])
            m2.metric("Active", r["active"])
            m3.metric("Diamonds", f"{r['diamonds']:,}")
            m4.metric("Days", r["days"])

# ================================================================== ASSIGN
elif st.session_state.page == "Assign":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Assign broadcasters")
    st.caption("Pick a month already uploaded, then assign broadcasters to a sub-agency.")

    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    daily_periods = sorted(store.list_periods("daily", business_id), reverse=True)
    all_periods = [("monthly", p) for p in monthly_periods] + [("daily", p) for p in daily_periods]

    if not all_periods:
        st.warning("Upload a report first from **Upload report**.")
        st.stop()

    label_map = {f"{p} ({t})": (t, p) for t, p in all_periods}
    choice = st.selectbox("Roster source", list(label_map.keys()))
    ptype, period = label_map[choice]
    df = period_data(period, ptype)

    only_unassigned = st.checkbox("Show only unassigned", value=True)
    view = df[df["sub_agency"] == "Unassigned"] if only_unassigned else df

    st.dataframe(
        view[["broadcaster_name", "profile_url", "sub_agency", "diamonds_redeemed"]]
            .sort_values("diamonds_redeemed", ascending=False),
        width='stretch', hide_index=True
    )

    st.markdown("##### Assign selected")
    options = view["profile_url"].tolist()
    labels = dict(zip(view["profile_url"], view["broadcaster_name"]))
    selected = st.multiselect("Pick broadcasters (by name)", options, format_func=lambda u: labels.get(u, u))
    agencies = load_agencies(business_id)
    if not agencies:
        st.info("No sub-agencies yet \u2014 add one first under **Create sub-agency**.")
    else:
        target_agency = st.selectbox("Sub-agency", agencies)
        if st.button("\u2714 Assign selected", type="primary", disabled=not selected):
            store.assign_broadcasters(selected, labels, target_agency, business_id, assigned_by=username)
            refresh_caches()
            st.toast(f"Assigned {len(selected)} broadcaster(s) to {target_agency}.", icon="\u2705")
            st.rerun()

# ============================================================ CREATE AGENCY
elif st.session_state.page == "CreateAgency":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Create sub-agency")

    name = st.text_input("Agency name (e.g. Partner X)", key="ca_name")
    contact = st.text_input("Contact person", key="ca_contact")
    phone = st.text_input("Phone", key="ca_phone")

    st.markdown("###### Login access")
    make_login = st.checkbox("Also create a login for this partner", value=True, key="ca_make_login")
    login_email, password = "", ""
    if make_login:
        c1, c2 = st.columns([2, 1])
        with c1:
            login_email = st.text_input("Login email", key="ca_email")
        with c2:
            st.write("")
            if st.button("Generate password"):
                alphabet = string.ascii_letters + string.digits
                st.session_state.ca_password = "".join(pysecrets.choice(alphabet) for _ in range(10))
        password = st.text_input("Password", key="ca_password")

    status = st.selectbox("Status", ["Active", "Inactive"], key="ca_status")
    notes = st.text_area("Notes", key="ca_notes")

    if st.button("Create sub-agency", type="primary", disabled=not name.strip()):
        store.add_agency(name.strip(), business_id)
        msg = f"Created sub-agency {name.strip()}."
        if make_login:
            if not is_valid_email(login_email):
                st.error("Enter a valid login email to also create a login.")
                st.stop()
            if not password.strip():
                st.error("Enter a password (or generate one) to also create a login.")
                st.stop()
            ok, m = store.create_user(
                login_email.strip(), contact.strip() or name.strip(),
                password, "sub_agency", business_id, name.strip(),
                "Active" if status == "Active" else "Disabled",
            )
            if not ok:
                st.error(m)
                st.stop()
            msg += f" Login created for {login_email.strip()}."
        refresh_caches()
        st.success(msg)

    st.markdown("##### Existing sub-agencies")
    for a in load_agencies(business_id):
        st.write(f"\u2022 {a}")

# ============================================================ UPLOAD REPORTS
elif st.session_state.page in ("UploadMonthly", "UploadDaily"):
    ptype = "monthly" if st.session_state.page == "UploadMonthly" else "daily"
    if not is_owner and ptype == "daily":
        st.error("Owner access only.")
        st.stop()
    st.title(f"Upload {ptype} report")
    st.caption("Uploading again for the same period replaces that period's numbers. Other periods are untouched.")

    default_period = dt.date.today().strftime("%Y-%m") if ptype == "monthly" else dt.date.today().isoformat()
    period_key = f"period_{ptype}"
    if period_key not in st.session_state:
        st.session_state[period_key] = default_period
    period = st.text_input(
        "Which period is this for?", key=period_key,
        help="Monthly example: 2026-08. Daily example: 2026-08-18.",
    )

    pattern = r"^\d{4}-\d{2}$" if ptype == "monthly" else r"^\d{4}-\d{2}-\d{2}$"
    valid_period = bool(re.match(pattern, period.strip()))
    if period and not valid_period:
        st.error("Period format looks off. Use YYYY-MM for monthly (e.g. 2026-08) or YYYY-MM-DD for daily.")

    uploaded = st.file_uploader("Tango referral_statistics CSV", type=["csv"], key=f"uploader_{ptype}")

    if uploaded is not None and valid_period:
        try:
            clean_df = utils.load_tango_csv(uploaded)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        history = load_all_raw(business_id)
        history_urls = set(history["profile_url"]) if not history.empty else set()
        assignments_df = load_assignments(business_id)
        assigned_urls = set(assignments_df["profile_url"]) if not assignments_df.empty else set()

        new_count = int((~clean_df["profile_url"].isin(history_urls)).sum())
        existing_count = len(clean_df) - new_count
        unassigned_count = int((~clean_df["profile_url"].isin(assigned_urls)).sum())

        st.markdown("##### Review before saving")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", len(clean_df))
        c2.metric("Recognized", existing_count)
        c3.metric("New", new_count)
        c4.metric("Need assignment", unassigned_count)
        st.caption(f"This updates **{period}** only. Other periods stay untouched.")
        st.dataframe(
            clean_df[["broadcaster_name", "diamonds_redeemed", "streaming_days"]].head(10),
            hide_index=True, width='stretch',
        )

        if st.button("Confirm upload", type="primary"):
            store.save_period(clean_df, period.strip(), ptype, business_id)
            if not is_owner:
                unassigned_here = [u for u in clean_df["profile_url"] if u not in assigned_urls]
                names_map = dict(zip(clean_df["profile_url"], clean_df["broadcaster_name"]))
                store.assign_broadcasters(unassigned_here, names_map, user_agency, business_id, assigned_by=username)
            refresh_caches()
            note = f"Saved {len(clean_df)} broadcasters for {period} ({ptype})."
            if is_owner and unassigned_count > 0:
                note += f" {unassigned_count} still need assignment."
            st.toast(note, icon="\u2705")
            st.rerun()

# =============================================================== USER ACCESS
elif st.session_state.page == "UserAccess":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("User access")

    st.markdown("##### Create user")
    c1, c2 = st.columns(2)
    with c1:
        new_email = st.text_input("Email", key="ua_email")
        new_name = st.text_input("Name", key="ua_name")
    with c2:
        new_role = st.selectbox("Role", ["sub_agency", "owner"], key="ua_role")
        new_agency = None
        if new_role == "sub_agency":
            agencies = load_agencies(business_id)
            new_agency = st.selectbox("Sub-agency", agencies, key="ua_agency") if agencies else None
        new_password = st.text_input("Password", key="ua_password")

    if st.button("Create user", type="primary"):
        if not is_valid_email(new_email):
            st.error("Enter a valid email address.")
        elif not new_password.strip():
            st.error("Password is required.")
        elif new_role == "sub_agency" and not new_agency:
            st.error("Create a sub-agency first, then assign this login to it.")
        else:
            ok, msg = store.create_user(
                new_email.strip(), new_name.strip() or new_email.strip(),
                new_password, new_role, business_id, new_agency or "", "Active",
            )
            if ok:
                refresh_caches()
                st.toast(msg, icon="\u2705")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("##### Existing users")
    users_df = load_business_users(business_id)
    if users_df.empty:
        st.caption("No additional users yet \u2014 you're the only login for this business.")
    else:
        for _, r in users_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                agency_bit = f" \u00b7 {r['sub_agency']}" if r["sub_agency"] else ""
                c1.markdown(f"**{r['name']}**  \n`{r['username']}` \u00b7 {r['role']}{agency_bit}")
                c2.markdown(f"Status: **{r['status']}**")
                with c3:
                    if r["status"] == "Active":
                        if st.button("Disable", key=f"dis_{r['username']}"):
                            store.set_user_status(r["username"], "Disabled")
                            refresh_caches()
                            st.rerun()
                    else:
                        if st.button("Enable", key=f"en_{r['username']}"):
                            store.set_user_status(r["username"], "Active")
                            refresh_caches()
                            st.rerun()
                with st.popover("Reset password"):
                    newpw = st.text_input("New password", key=f"pw_{r['username']}")
                    if st.button("Save", key=f"savepw_{r['username']}"):
                        if newpw.strip():
                            store.reset_user_password(r["username"], newpw.strip())
                            st.success("Password updated.")
                        else:
                            st.error("Enter a new password.")

# =========================================================== DATA MANAGEMENT
elif st.session_state.page == "DataManagement":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Data management")
    ptype = st.radio("Report type", ["monthly", "daily"], horizontal=True, key="dm_ptype")
    all_periods = sorted(store.list_periods(ptype, business_id, exclude_archived=False), reverse=True)
    archived_set = store.get_archived_periods(business_id)

    if not all_periods:
        st.info(f"No {ptype} data stored yet.")
    else:
        for p in all_periods:
            is_archived = (p, ptype) in archived_set
            with st.container(border=True):
                c1, c2 = st.columns([3, 3])
                label = p + (" \u00b7 Archived" if is_archived else "")
                c1.markdown(f"**{label}**")
                with c2:
                    b1, b2, b3 = st.columns(3)
                    if b1.button("View", key=f"view_{ptype}_{p}"):
                        st.session_state[f"viewing_{ptype}"] = p
                    if is_archived:
                        if b2.button("Unarchive", key=f"unarch_{ptype}_{p}"):
                            store.unarchive_period(p, ptype, business_id)
                            refresh_caches()
                            st.rerun()
                    else:
                        if b2.button("Archive", key=f"arch_{ptype}_{p}"):
                            store.archive_period(p, ptype, business_id)
                            refresh_caches()
                            st.rerun()
                    if b3.button("Replace", key=f"replace_{ptype}_{p}"):
                        st.session_state[f"period_{ptype}"] = p
                        st.session_state.page = "UploadMonthly" if ptype == "monthly" else "UploadDaily"
                        st.rerun()
            if st.session_state.get(f"viewing_{ptype}") == p:
                view_df = period_data(p, ptype)
                st.dataframe(
                    view_df[["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"]],
                    hide_index=True, width='stretch',
                )

    st.markdown("---")
    with st.container(border=True):
        st.markdown("##### :red[Danger zone]")
        st.caption("Permanently deletes a period's numbers. Sub-agency assignments are not affected.")
        target = st.selectbox("Period to clear", all_periods, key="dm_clear_target") if all_periods else None
        confirm = st.checkbox(f"I understand this deletes {ptype} data for the selected period", key="dm_confirm")
        if st.button("Clear this period", type="primary", disabled=not (confirm and target)):
            store.clear_period(target, ptype, business_id)
            refresh_caches()
            st.toast(f"Cleared {ptype} data for {target}.", icon="\u2705")
            st.rerun()
