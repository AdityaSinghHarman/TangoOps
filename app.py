import datetime as dt
import re
import base64
import html
import secrets as pysecrets
import string
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit_authenticator as stauth

import utils
import store

st.set_page_config(page_title="TangoOps – Agency Control", layout="wide", page_icon="\u25c8")

# ---------------------------------------------------------------- styling ---
st.markdown("""
<style>
:root{ --brand:#3F6B1E; --brand-soft:#EEF3E7; --ink:#1C1D1A; --card-radius:14px; --border:#E3E3DD; }

/* Login */
.stApp:has(.tango-login-shell){
  background:
    radial-gradient(circle at 12% 12%, rgba(77,124,15,.10), transparent 30rem),
    linear-gradient(135deg,#F7F9F3 0%,#FFFFFF 52%,#F4F7EF 100%);
}
.stApp:has(.tango-login-shell) [data-testid="stHeader"]{ background:transparent; }
.stApp:has(.tango-login-shell) [data-testid="stMainBlockContainer"]{
  max-width:1180px; padding-top:5.5rem; padding-bottom:3rem;
}
.tango-login-hero{ padding:2.1rem 3.5rem 2rem .5rem; }
.tango-login-brand{ display:flex; align-items:center; gap:.75rem; color:#174A19;
  font-size:1.25rem; font-weight:750; letter-spacing:-.02em; margin-bottom:5.5rem; }
.tango-login-mark{ width:2.25rem; height:2.25rem; display:grid; place-items:center;
  color:#fff; background:linear-gradient(145deg,#315E18,#74A843); border-radius:.7rem;
  box-shadow:0 8px 20px rgba(63,107,30,.22); transform:rotate(45deg); }
.tango-login-mark span{ transform:rotate(-45deg); font-size:1.05rem; }
.tango-login-eyebrow{ color:var(--brand); font-size:.76rem; line-height:1;
  font-weight:750; letter-spacing:.12em; text-transform:uppercase; margin-bottom:1rem; }
.tango-login-hero h1{ max-width:640px; color:#172016; font-size:clamp(2.6rem,5vw,4.6rem);
  line-height:1.02; letter-spacing:-.055em; margin:0 0 1.25rem; }
.tango-login-hero p{ max-width:560px; color:#5E685B; font-size:1.05rem;
  line-height:1.7; margin:0; }
.tango-login-proof{ display:flex; gap:1.6rem; flex-wrap:wrap; margin-top:2.25rem;
  color:#42503F; font-size:.88rem; font-weight:600; }
.tango-login-proof span{ display:inline-flex; align-items:center; white-space:nowrap; }
.tango-login-proof span::before{ content:'✓'; display:inline-grid; place-items:center;
  width:1.25rem; height:1.25rem; margin-right:.45rem; color:#39751C;
  background:#E6F2DE; border-radius:50%; font-size:.72rem; font-weight:800; }
.tango-login-panel-head{ margin:0 0 1.5rem; }
.tango-login-panel-head h2{ color:#172016; font-size:1.85rem; line-height:1.2;
  letter-spacing:-.035em; margin:0 0 .45rem; }
.tango-login-panel-head p{ color:#6A7367; font-size:.92rem; margin:0; }
.tango-login-foot{ color:#7B8378; text-align:center; font-size:.76rem; margin-top:1.25rem; }
.stApp:has(.tango-login-shell) div[data-testid="stColumn"]:has(.tango-login-panel-head){
  align-self:center; background:rgba(255,255,255,.94); border:1px solid #DDE4D8;
  border-radius:1.4rem; padding:2.35rem 2.35rem 1.8rem;
  box-shadow:0 24px 70px rgba(36,61,22,.12),0 3px 12px rgba(28,29,26,.04);
}
.stApp:has(.tango-login-shell) div[data-testid="stForm"]{ border:0; padding:0; }
.stApp:has(.tango-login-shell) div[data-testid="stForm"] h2,
.stApp:has(.tango-login-shell) div[data-testid="stForm"] h3{ display:none; }
.stApp:has(.tango-login-shell) div[data-testid="stTextInput"] label{
  color:#293326; font-size:.84rem; font-weight:650;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"]{
  min-height:3rem; background:#FBFCFA; border-color:#D8DFD3; border-radius:.7rem;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"]:focus-within{
  border-color:#54842F; box-shadow:0 0 0 3px rgba(84,132,47,.14);
}
.stApp:has(.tango-login-shell) div[data-testid="stFormSubmitButton"]{ width:100%; }
.stApp:has(.tango-login-shell) div[data-testid="stFormSubmitButton"] button{
  width:100%; min-height:3rem; margin-top:.7rem; color:#fff; font-weight:700;
  background:linear-gradient(135deg,#315E18,#4F812B); border:0; border-radius:.7rem;
  box-shadow:0 8px 18px rgba(49,94,24,.19);
}
.stApp:has(.tango-login-shell) div[data-testid="stFormSubmitButton"] button:hover{
  color:#fff; background:linear-gradient(135deg,#274F12,#416F22);
  box-shadow:0 10px 22px rgba(49,94,24,.25); transform:translateY(-1px);
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"] button{
  width:2.8rem !important; min-width:2.8rem; min-height:2.75rem; margin:0 !important;
  padding:0 !important; color:#52604E !important; background:transparent !important;
  border:0 !important; border-left:1px solid #E1E6DE !important; border-radius:0 !important;
  box-shadow:none !important; transform:none !important;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"] button:hover{
  color:#315E18 !important; background:#F0F5EC !important; box-shadow:none !important;
}
.stApp:has(.tango-login-shell) div[data-testid="stAlert"]{ border-radius:.7rem; }

/* Platform admin */
.stApp:has(.platform-admin-page) [data-testid="stMainBlockContainer"]{ max-width:1440px; padding-top:2.3rem; }
.stApp:has(.platform-admin-page){ background:#F7F9F6; }
.stApp:has(.platform-admin-page) section[data-testid="stSidebar"]{ background:#FFFFFF; border-right:1px solid #E2E7DE; }
.admin-hero{ display:flex; align-items:flex-end; justify-content:space-between; gap:2rem; margin:0 0 1.5rem; }
.admin-kicker{ color:#4D7B2E; font-size:.75rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.65rem; }
.admin-hero h1{ color:#172016; font-size:2.35rem; line-height:1.1; letter-spacing:-.045em; margin:0 0 .45rem; }
.admin-hero p{ color:#667063; font-size:.97rem; margin:0; }
.admin-secure-pill{ flex:none; color:#35631D; background:#EAF3E4; border:1px solid #D4E5C9; border-radius:999px; padding:.55rem .85rem; font-size:.78rem; font-weight:700; }
.admin-section-head{ margin:1.5rem 0 1rem; }
.admin-section-head h2{ color:#1D271B; font-size:1.25rem; margin:0 0 .25rem; }
.admin-section-head p{ color:#70796D; font-size:.86rem; margin:0; }
.agency-status{ display:inline-flex; align-items:center; gap:.35rem; border-radius:999px; padding:.25rem .55rem; font-size:.72rem; font-weight:700; line-height:1; }
.agency-status::before{ content:''; width:.4rem; height:.4rem; border-radius:50%; background:currentColor; }
.agency-status.active{ color:#24722C; background:#E7F4E8; }
.agency-status.disabled{ color:#8A4D1F; background:#F9ECDD; }
.empty-agencies{ text-align:center; padding:3.5rem 1rem; color:#6B7468; }
.empty-agencies-icon{ width:3rem; height:3rem; margin:0 auto 1rem; display:grid; place-items:center; color:#47742B; background:#EAF3E4; border-radius:1rem; font-size:1.3rem; }
.stApp:has(.platform-admin-page) div[data-testid="stVerticalBlockBorderWrapper"]{ background:#FFFFFF; border-color:#E0E5DC; border-radius:1rem; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.stApp:has(.platform-admin-page) .kpi-card{ min-height:118px; margin-bottom:.25rem; border-color:#E0E5DC; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.stApp:has(.platform-admin-page) div[data-baseweb="input"],
.stApp:has(.platform-admin-page) div[data-baseweb="select"] > div{ background:#FFFFFF; border-color:#D9E0D5; }

/* Agency owner business overview */
.stApp:has(.owner-overview-page) [data-testid="stMainBlockContainer"]{ max-width:1500px; padding-top:2.1rem; }
.stApp:has(.owner-overview-page){ background:#F7F9F6; }
.overview-hero{ display:flex; justify-content:space-between; align-items:flex-end; gap:2rem; margin-bottom:1.35rem; }
.overview-hero h1{ color:#172016; font-size:2.25rem; line-height:1.1; letter-spacing:-.045em; margin:0 0 .4rem; }
.overview-hero p{ color:#687165; font-size:.95rem; margin:0; }
.overview-eyebrow{ color:#4D7B2E; font-size:.73rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.55rem; }
.overview-period-pill{ color:#43513E; background:#FFFFFF; border:1px solid #DEE5DA; border-radius:.75rem; padding:.6rem .8rem; font-size:.78rem; font-weight:650; }
.overview-kpi{ min-height:150px; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; padding:1.15rem 1.2rem; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.overview-kpi-top{ display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
.overview-kpi-label{ color:#667063; font-size:.78rem; font-weight:650; }
.overview-kpi-icon{ width:2rem; height:2rem; display:grid; place-items:center; color:#47742B; background:#EAF3E4; border-radius:.65rem; font-size:1rem; }
.overview-kpi-value{ color:#182116; font-size:1.85rem; line-height:1; font-weight:760; letter-spacing:-.035em; }
.overview-kpi-note{ color:#778073; font-size:.73rem; margin-top:.75rem; }
.overview-kpi-note.up{ color:#287331; }.overview-kpi-note.down{ color:#B1453D; }
.overview-section{ margin:1.7rem 0 .8rem; }
.overview-section h2{ color:#1C251A; font-size:1.25rem; margin:0 0 .25rem; }
.overview-section p{ color:#747C70; font-size:.84rem; margin:0; }
.insight-card{ min-height:116px; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; padding:1.05rem 1.1rem; }
.insight-label{ color:#70796C; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; margin-bottom:.65rem; }
.insight-value{ color:#1B2419; font-size:1.35rem; font-weight:750; letter-spacing:-.025em; }
.insight-caption{ color:#727A6F; font-size:.76rem; margin-top:.35rem; }
.stApp:has(.owner-overview-page) div[data-testid="stVerticalBlockBorderWrapper"]{ background:#FFFFFF; border-color:#E0E5DC; border-radius:1rem; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.stApp:has(.owner-overview-page) div[data-baseweb="select"] > div{ background:#FFFFFF; border-color:#D9E0D5; }

/* Option 1 — Executive Command Center */
.command-grid-title{ display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:1.6rem 0 .75rem; }
.command-grid-title h2{ color:#172016; font-size:1.2rem; margin:0; }
.command-grid-title p{ color:#737D70; font-size:.82rem; margin:.2rem 0 0; }
.command-score{ min-height:164px; display:flex; align-items:center; gap:1.15rem; padding:1.2rem;
  background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; }
.command-score-ring{ --score:0; position:relative; flex:none; width:6.25rem; height:6.25rem; border-radius:50%;
  display:grid; place-items:center; background:conic-gradient(#74A843 calc(var(--score)*1%),#E8EDE5 0); }
.command-score-ring::before{ content:''; position:absolute; width:4.75rem; height:4.75rem; border-radius:50%; background:#fff; }
.command-score-value{ position:relative; color:#172016; font-size:1.7rem; font-weight:780; }
.command-score-copy h3{ color:#1C251A; font-size:1rem; margin:0 0 .35rem; }
.command-score-copy p{ color:#6E786B; font-size:.76rem; line-height:1.45; margin:0; }
.command-alert{ min-height:164px; padding:1.2rem; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; }
.command-alert-label{ color:#B05C16; font-size:.7rem; font-weight:750; text-transform:uppercase; letter-spacing:.07em; }
.command-alert-value{ color:#1B2419; font-size:1.8rem; font-weight:780; margin:.65rem 0 .25rem; }
.command-alert-copy{ color:#70796D; font-size:.76rem; line-height:1.45; }
.command-progress{ height:.52rem; overflow:hidden; background:#E8EDE5; border-radius:999px; margin:.8rem 0 .55rem; }
.command-progress span{ display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#315E18,#9ACB31); }
.command-table-badge{ display:inline-flex; align-items:center; padding:.22rem .5rem; border-radius:999px;
  color:#2E6B2A; background:#EAF4E5; font-size:.68rem; font-weight:700; }
.command-footnote{ color:#788176; font-size:.7rem; margin-top:.45rem; }
.stApp:has(.owner-overview-page) div[data-testid="stMetric"]{ background:#FFFFFF; border:1px solid #E0E5DC;
  border-radius:.9rem; padding:.85rem 1rem; }

/* Role-specific Agency Owner and Sub-Agency sidebar */
.owner-sidebar-marker{ display:none; }
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"]{
  background:#FAFBF9; border-right:1px solid #DEE4DA;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
  padding-top:.75rem;
}
.owner-sidebar-brand{ display:flex; align-items:center; gap:.65rem; color:#174A19;
  font-size:1.28rem; font-weight:780; letter-spacing:-.035em; padding:.25rem .2rem .9rem; }
.owner-sidebar-logo{ width:1.9rem; height:1.9rem; display:grid; place-items:center; color:#fff;
  background:#315E18; border-radius:.55rem; transform:rotate(45deg); }
.owner-sidebar-logo span{ transform:rotate(-45deg); font-size:.72rem; }
.owner-workspace{ display:flex; align-items:center; gap:.7rem; padding:.8rem; margin:0 0 .7rem;
  background:#FFFFFF; border:1px solid #DDE3D9; border-radius:.85rem; }
.owner-workspace-avatar{ flex:none; width:2.4rem; height:2.4rem; display:grid; place-items:center;
  color:#315E18; background:#E7F1E1; border-radius:50%; font-weight:750; }
.owner-workspace-copy{ min-width:0; line-height:1.25; }
.owner-workspace-name{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  color:#1B2419; font-size:.85rem; font-weight:700; }
.owner-workspace-role{ color:#737B6F; font-size:.72rem; margin-top:.15rem; }
.sidebar-group-marker{ display:none; }
.sidebar-group-head{ display:flex; align-items:center; justify-content:space-between; gap:.5rem;
  color:#6B7467; font-size:.69rem; font-weight:750; text-transform:uppercase;
  letter-spacing:.09em; margin:.05rem .15rem .45rem; }
.sidebar-due-badge{ color:#A75812; background:#FFF0DD; border:1px solid #F4D7B4;
  border-radius:999px; padding:.17rem .42rem; font-size:.59rem; font-weight:750;
  letter-spacing:0; text-transform:none; }
.sidebar-ok-badge{ color:#34712A; background:#EAF3E4; border:1px solid #D6E7CD;
  border-radius:999px; padding:.17rem .42rem; font-size:.59rem; font-weight:750;
  letter-spacing:0; text-transform:none; }
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.sidebar-group-marker){
  background:#FFFFFF; border-color:#E0E5DC; border-radius:.85rem; margin:.55rem 0;
  box-shadow:0 1px 3px rgba(33,48,27,.025);
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.sidebar-profile-marker){
  background:#FFFFFF; border-color:#DDE3D9; border-radius:.85rem; margin-top:.8rem;
}
.sidebar-profile-marker{ display:none; }
.sidebar-profile{ display:flex; align-items:center; gap:.65rem; margin-bottom:.3rem; }
.sidebar-profile-copy{ min-width:0; line-height:1.25; }
.sidebar-profile-name{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  color:#20281E; font-size:.79rem; font-weight:700; }
.sidebar-profile-role{ color:#737B6F; font-size:.68rem; margin-top:.12rem; }
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button{
  min-height:2.55rem; padding:.45rem .65rem; border-radius:.62rem; font-size:.82rem;
  color:#273124; background:transparent; border:1px solid transparent;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button:hover{
  color:#315E18; background:#F0F5EC; border-color:#E0EADB;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button[kind="primary"],
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  color:#315E18 !important; background:#E9F2E3 !important; border-color:#DCE9D5 !important;
  box-shadow:inset 3px 0 0 #315E18 !important; font-weight:700;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] details{
  background:#FFFFFF; border:1px solid #E0E5DC; border-radius:.85rem; margin:.55rem 0;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] details summary{
  min-height:2.7rem; color:#315E18; font-size:.82rem; font-weight:700;
}
@media (max-width: 800px){
  .overview-hero{ align-items:flex-start; flex-direction:column; gap:.8rem; }
  .overview-hero h1{ font-size:1.9rem; }
  .overview-period-pill{ display:none; }
  .overview-kpi{ min-height:132px; }
}
@media (max-width: 800px){
  .admin-hero{ align-items:flex-start; flex-direction:column; gap:1rem; }
  .admin-hero h1{ font-size:1.95rem; }
  .admin-secure-pill{ display:none; }
}
@media (max-width: 800px){
  .stApp:has(.tango-login-shell) [data-testid="stMainBlockContainer"]{ padding:1.4rem 1rem 2rem; }
  .tango-login-hero{ padding:.5rem .2rem 1.5rem; }
  .tango-login-brand{ margin-bottom:2.5rem; }
  .tango-login-hero h1{ font-size:2.5rem; }
  .tango-login-proof{ margin-top:1.4rem; gap:.75rem 1.1rem; }
  .stApp:has(.tango-login-shell) div[data-testid="stColumn"]:has(.tango-login-panel-head){
    padding:1.65rem 1.25rem 1.25rem; border-radius:1.1rem;
  }
}

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


def overview_kpi_card(label, value, icon, note="", direction=""):
    note_class = f" {direction}" if direction else ""
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_icon = html.escape(str(icon))
    safe_note = html.escape(str(note))
    note_html = f'<div class="overview-kpi-note{note_class}">{safe_note}</div>' if note else ""
    st.markdown(f"""
    <div class="overview-kpi">
      <div class="overview-kpi-top">
        <div class="overview-kpi-label">{safe_label}</div>
        <div class="overview-kpi-icon">{safe_icon}</div>
      </div>
      <div class="overview-kpi-value">{safe_value}</div>
      {note_html}
    </div>
    """, unsafe_allow_html=True)


TABLE_COLUMN_CONFIG = {
    "broadcaster_name": st.column_config.TextColumn("Broadcaster", width="medium"),
    "sub_agency": st.column_config.TextColumn("Sub-Agency", width="medium"),
    "status": st.column_config.TextColumn("Status", width="small"),
    "streaming_days": st.column_config.NumberColumn("Days streamed", format="%d", width="small"),
    "streaming_hours": st.column_config.NumberColumn("Hours streamed", format="%.1f", width="small"),
    "diamonds_redeemed": st.column_config.NumberColumn("Diamonds redeemed", format="localized", width="small"),
    "diamonds_per_day": st.column_config.NumberColumn("Diamonds per day", format="localized", width="small"),
    "growth_pct": st.column_config.NumberColumn("Growth vs previous month", format="%.1f%%", width="medium"),
    "is_new": st.column_config.CheckboxColumn("New broadcaster", width="small"),
    "profile_url": st.column_config.LinkColumn("Profile", display_text="Open profile", width="small"),
}


def table_column_config(columns):
    """Return consistent, user-facing labels without renaming stored data."""
    return {column: TABLE_COLUMN_CONFIG[column] for column in columns if column in TABLE_COLUMN_CONFIG}


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


DIAMONDS_PER_USD = 200


def calculate_sub_agency_earnings(diamonds_redeemed, commission_pct):
    """Return (gross USD value, sub-agency commission) for redeemed diamonds."""
    gross_usd = float(diamonds_redeemed or 0) / DIAMONDS_PER_USD
    commission_usd = None if commission_pct is None else gross_usd * float(commission_pct) / 100
    return gross_usd, commission_usd


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
    creds = {"usernames": {
        boot["username"]: {"name": boot["name"], "email": boot["username"], "password": boot_hash}
    }}
    users_df = load_all_users_df()
    businesses_df = load_businesses_df()
    active_business_ids = set(
        businesses_df[businesses_df["status"] == "Active"]["business_id"]
    ) if not businesses_df.empty else set()
    if not users_df.empty:
        active = users_df[
            (users_df["status"] == "Active") & (users_df["business_id"].isin(active_business_ids))
        ]
        for _, row in active.iterrows():
            creds["usernames"][row["username"]] = {
                "name": row["name"], "email": row["username"], "password": row["password_hash"]
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

# Keep the authentication mechanism intact while presenting it in a branded,
# responsive shell. A rerun removes the shell immediately after cookie/login
# authentication so authenticated pages never inherit login-only styling.
was_authenticated = st.session_state.get("authentication_status") is True
if not was_authenticated:
    st.markdown('<div class="tango-login-shell"></div>', unsafe_allow_html=True)
    hero_col, login_col = st.columns([1.35, 0.85], gap="large", vertical_alignment="center")
    with hero_col:
        st.markdown("""
        <div class="tango-login-hero">
          <div class="tango-login-brand">
            <div class="tango-login-mark"><span>◆</span></div>TangoOps
          </div>
          <div class="tango-login-eyebrow">Agency operations, simplified</div>
          <h1>Turn performance data into confident action.</h1>
          <p>One secure workspace to monitor broadcaster performance, manage
          agency relationships, and keep every report on track.</p>
          <div class="tango-login-proof">
            <span>Role-based access</span><span>Secure reporting</span><span>Live insights</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with login_col:
        st.markdown("""
        <div class="tango-login-panel-head">
          <h2>Welcome back</h2>
          <p>Sign in to continue to your TangoOps workspace.</p>
        </div>
        """, unsafe_allow_html=True)
        authenticator.login(location="main", fields={
            "Form name": "Sign in",
            "Username": "Email address",
            "Password": "Password",
            "Login": "Sign in",
        })
        st.markdown('<div class="tango-login-foot">Protected access · TangoOps Agency Control</div>',
                    unsafe_allow_html=True)

auth_status = st.session_state.get("authentication_status")

if auth_status is True and not was_authenticated:
    st.rerun()

if auth_status is False:
    st.error("We couldn't sign you in. Check your email and password, then try again.")
    st.stop()
elif auth_status is None:
    st.stop()

display_name = st.session_state.get("name", "")
username = st.session_state.get("username", "")


@st.cache_data(ttl=15, show_spinner=False)
def load_profile(uname):
    return store.get_profile(uname)


_profile = load_profile(username)
if _profile and _profile.get("display_name"):
    display_name = _profile["display_name"]
avatar_b64 = _profile.get("avatar_base64") if _profile else None


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

default_page = "Businesses" if is_platform_admin else "Admin"
allowed_pages_by_role = {
    "platform_admin": {"Businesses", "MyProfile"},
    "owner": {
        "Admin", "Statistics", "Broadcasters", "BroadcasterDetail", "Assign",
        "SubAgencies", "CreateAgency", "UploadMonthly", "UploadDaily",
        "UserAccess", "DataManagement", "MyProfile",
    },
    "sub_agency": {"Admin", "Broadcasters", "BroadcasterDetail", "UploadMonthly", "MyProfile"},
}

# Reset navigation when the authenticated identity changes. This prevents a
# sub-agency login from inheriting an owner-only page after sign-out/sign-in.
if st.session_state.get("_navigation_username") != username:
    st.session_state.page = default_page
    st.session_state.selected_profile_url = None
    st.session_state._navigation_username = username
elif st.session_state.get("page") not in allowed_pages_by_role[user_role]:
    st.session_state.page = default_page
    st.session_state.selected_profile_url = None

if "selected_profile_url" not in st.session_state:
    st.session_state.selected_profile_url = None


def nav_button(label, page_key, icon=None):
    if st.button(label, width='stretch', icon=icon,
                 type="primary" if st.session_state.page == page_key else "secondary"):
        st.session_state.page = page_key
        st.rerun()


with st.sidebar:
    if is_owner:
        st.markdown('<div class="owner-sidebar-marker"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="owner-sidebar-brand">
          <div class="owner-sidebar-logo"><span>◆</span></div>TangoOps
        </div>
        """, unsafe_allow_html=True)
        owner_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "AO"
        safe_business_name = html.escape(str(business_name))
        safe_display_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{owner_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_business_name}</div>
            <div class="owner-workspace-role">Business Owner</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        nav_button("Overview", "Admin", ":material/dashboard:")
        nav_button("Statistics", "Statistics", ":material/bar_chart:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-group-head"><span>Manage</span></div>', unsafe_allow_html=True)
            nav_button("Broadcasters", "Broadcasters", ":material/groups:")
            nav_button("Assign broadcasters", "Assign", ":material/person_add:")
            nav_button("Sub-Agency Management", "SubAgencies", ":material/account_tree:")
            nav_button("Create Sub-Agency", "CreateAgency", ":material/domain_add:")

        current_month_key = dt.date.today().strftime("%Y-%m")
        monthly_uploads = store.list_periods("monthly", business_id)
        upload_is_due = current_month_key not in monthly_uploads
        upload_badge_class = "sidebar-due-badge" if upload_is_due else "sidebar-ok-badge"
        upload_badge_text = "Upload due" if upload_is_due else "Up to date"
        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="sidebar-group-head"><span>Reports</span>'
                f'<span class="{upload_badge_class}">{upload_badge_text}</span></div>',
                unsafe_allow_html=True,
            )
            nav_button("Monthly report", "UploadMonthly", ":material/upload_file:")
            nav_button("Daily report", "UploadDaily", ":material/description:")

        admin_expanded = st.session_state.page in ("UserAccess", "DataManagement")
        with st.expander("Administration", expanded=admin_expanded, icon=":material/admin_panel_settings:"):
            nav_button("User access", "UserAccess", ":material/manage_accounts:")
            nav_button("Data management", "DataManagement", ":material/database:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-profile-marker"></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="sidebar-profile">
              <div class="owner-workspace-avatar">{owner_initials}</div>
              <div class="sidebar-profile-copy">
                <div class="sidebar-profile-name">{safe_display_name}</div>
                <div class="sidebar-profile-role">{safe_business_name} · Owner</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            nav_button("My profile", "MyProfile", ":material/account_circle:")
            authenticator.logout("Sign out", "sidebar")

    elif is_sub_agency:
        st.markdown('<div class="owner-sidebar-marker"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="owner-sidebar-brand">
          <div class="owner-sidebar-logo"><span>◆</span></div>TangoOps
        </div>
        """, unsafe_allow_html=True)
        sub_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "SA"
        safe_agency_name = html.escape(str(user_agency))
        safe_business_name = html.escape(str(business_name))
        safe_display_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{sub_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_agency_name}</div>
            <div class="owner-workspace-role">Sub-Agency · {safe_business_name}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        nav_button("Overview", "Admin", ":material/dashboard:")
        nav_button("My broadcasters", "Broadcasters", ":material/groups:")

        current_month_key = dt.date.today().strftime("%Y-%m")
        monthly_uploads = store.list_periods("monthly", business_id)
        upload_is_due = current_month_key not in monthly_uploads
        upload_badge_class = "sidebar-due-badge" if upload_is_due else "sidebar-ok-badge"
        upload_badge_text = "Upload due" if upload_is_due else "Up to date"
        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="sidebar-group-head"><span>Reports</span>'
                f'<span class="{upload_badge_class}">{upload_badge_text}</span></div>',
                unsafe_allow_html=True,
            )
            nav_button("Upload monthly report", "UploadMonthly", ":material/upload_file:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-profile-marker"></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="sidebar-profile">
              <div class="owner-workspace-avatar">{sub_initials}</div>
              <div class="sidebar-profile-copy">
                <div class="sidebar-profile-name">{safe_display_name}</div>
                <div class="sidebar-profile-role">{safe_agency_name} · Sub-Agency</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            nav_button("My profile", "MyProfile", ":material/account_circle:")
            authenticator.logout("Sign out", "sidebar")

    else:
        st.markdown("### \u25c8 TangoOps")
        st.caption("PLATFORM CONTROL")
        if business_name:
            st.caption(business_name)
        st.write("")

    if is_platform_admin:
        nav_button("Platform overview", "Businesses", ":material/admin_panel_settings:")
        st.write("")
        nav_button("My profile", "MyProfile")
        if avatar_b64:
            st.markdown(
                f'<img src="data:image/png;base64,{avatar_b64}" '
                f'style="width:36px;height:36px;border-radius:50%;object-fit:cover;margin-bottom:6px;">',
                unsafe_allow_html=True,
            )
        st.caption(f"Signed in as **{display_name}**")
        st.caption("Platform Administrator")
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
    load_profile.clear()


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
    choice = st.selectbox("Sub-Agency", agencies, key=key)
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
    st.markdown('<div class="platform-admin-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="admin-hero">
      <div>
        <div class="admin-kicker">Platform administration</div>
        <h1>Platform overview</h1>
        <p>Monitor platform health and manage isolated agency accounts, owners, and access.</p>
      </div>
      <div class="admin-secure-pill">● Platform admin access</div>
    </div>
    """, unsafe_allow_html=True)

    businesses = store.get_businesses()
    all_users = load_all_users_df()
    total_agencies = len(businesses)
    active_agencies = int((businesses["status"] == "Active").sum()) if not businesses.empty else 0
    total_owners = int((all_users["role"] == "owner").sum()) if not all_users.empty else 0
    total_sub_agencies = (sum(len(store.get_agencies(bid)) for bid in businesses["business_id"])
                          if not businesses.empty else 0)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        kpi_card("Total agencies", f"{total_agencies:,}")
    with m2:
        kpi_card("Active agencies", f"{active_agencies:,}")
    with m3:
        kpi_card("Owner accounts", f"{total_owners:,}")
    with m4:
        kpi_card("Sub-Agencies", f"{total_sub_agencies:,}")

    # Executive Command Center: platform-wide health derived from live agency data.
    reporting_month = dt.date.today().strftime("%Y-%m")
    agency_health_rows = []
    current_network_diamonds = previous_network_diamonds = 0
    for _, business_row in businesses.iterrows():
        bid = business_row["business_id"]
        raw = load_all_raw(bid)
        monthly = raw[raw["period_type"] == "monthly"].copy() if not raw.empty else pd.DataFrame()
        periods = sorted(monthly["period"].unique()) if not monthly.empty else []
        latest_period = periods[-1] if periods else None
        previous_period = periods[-2] if len(periods) > 1 else None
        current_df = monthly[monthly["period"] == latest_period].copy() if latest_period else pd.DataFrame()
        previous_df = monthly[monthly["period"] == previous_period].copy() if previous_period else pd.DataFrame()
        current_kpis = utils.compute_kpis(current_df)
        previous_kpis = utils.compute_kpis(previous_df) if not previous_df.empty else {}
        health = utils.broadcaster_health_score(current_df, previous_df)
        quality = utils.data_quality_score(current_df)
        current_network_diamonds += current_kpis["diamonds_redeemed"]
        previous_network_diamonds += previous_kpis.get("diamonds_redeemed", 0)
        agency_health_rows.append({
            "Agency": business_row["business_name"],
            "Latest report": latest_period or "Missing",
            "Broadcasters": current_kpis["broadcasters"],
            "Diamonds": current_kpis["diamonds_redeemed"],
            "Health": health,
            "Data quality": quality,
            "Status": ("Healthy" if health >= 75 else "Watch" if health >= 55 else "Needs attention"),
        })
    agency_health = pd.DataFrame(agency_health_rows)
    uploaded_current = int((agency_health["Latest report"] == reporting_month).sum()) if not agency_health.empty else 0
    adoption_pct = round(uploaded_current / max(1, active_agencies) * 100, 1)
    missing_reports = max(0, active_agencies - uploaded_current)
    network_growth = (round((current_network_diamonds - previous_network_diamonds) /
                            previous_network_diamonds * 100, 1)
                      if previous_network_diamonds else 0.0)
    avg_health = round(float(agency_health["Health"].mean()), 1) if not agency_health.empty else 0.0

    st.markdown("""
    <div class="command-grid-title"><div><h2>Platform health overview</h2>
    <p>Live reporting adoption, network performance and account health.</p></div></div>
    """, unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Agency adoption", f"{adoption_pct:.1f}%", f"{uploaded_current} reported this month")
    p2.metric("Missing reports", f"{missing_reports}", "Current reporting month")
    p3.metric("Network growth", f"{network_growth:+.1f}%", "Diamonds vs previous period")
    p4.metric("Average account health", f"{avg_health:.0f}/100", "Explainable operating score")

    if not agency_health.empty:
        left_health, right_health = st.columns([1.45, 1])
        with left_health:
            with st.container(border=True):
                st.markdown("##### Agency health directory")
                st.dataframe(
                    agency_health.sort_values(["Health", "Diamonds"], ascending=[True, False]),
                    hide_index=True, width="stretch",
                    column_config={
                        "Diamonds": st.column_config.NumberColumn("Diamonds", format="localized"),
                        "Health": st.column_config.ProgressColumn("Health", min_value=0, max_value=100, format="%d"),
                        "Data quality": st.column_config.ProgressColumn("Data quality", min_value=0, max_value=100, format="%d"),
                    },
                )
        with right_health:
            status_counts = agency_health["Status"].value_counts()
            health_fig = go.Figure(go.Pie(
                labels=status_counts.index, values=status_counts.values, hole=.7,
                marker=dict(colors=["#5C9D3A", "#E39A32", "#C7544B"]),
                textinfo="label+value", hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            health_fig.update_layout(
                title="Account health distribution", height=310,
                margin=dict(l=10, r=10, t=55, b=10), showlegend=False,
                paper_bgcolor="#FFFFFF", font=dict(family="Inter", color="#4C5548"),
                annotations=[dict(text=f"{len(agency_health)}<br>agencies", x=.5, y=.5,
                                  showarrow=False, font=dict(size=16, color="#172016"))],
            )
            with st.container(border=True):
                st.plotly_chart(health_fig, use_container_width=True, config={"displayModeBar": False})

    recent_platform_activity = store.get_recent_platform_activity(8)
    if not recent_platform_activity.empty:
        with st.expander("Recent platform activity", expanded=False):
            activity_view = recent_platform_activity.rename(columns={
                "business_name": "Agency", "broadcaster_name": "Broadcaster",
                "sub_agency": "Sub-Agency", "assigned_by": "Changed by", "assigned_at": "Time",
            })
            st.dataframe(activity_view[["Agency", "Broadcaster", "Sub-Agency", "Changed by", "Time"]],
                         hide_index=True, width="stretch")

    create_tab = st.expander("＋ Create a new agency", expanded=False)
    directory_tab = st.container()
    with create_tab:
        st.markdown("""
        <div class="admin-section-head">
          <h2>Set up a new agency</h2>
          <p>Create the agency workspace and its first owner account together.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            biz_name = st.text_input("Agency name", key="biz_name", placeholder="e.g. Northstar Talent")
            st.markdown("###### Primary owner")
            c1, c2 = st.columns(2)
            with c1:
                owner_name = st.text_input("Owner name", key="biz_owner_name", placeholder="Full name")
                owner_email = st.text_input("Owner email", key="biz_owner_email", placeholder="owner@agency.com")
            with c2:
                owner_password = st.text_input(
                    "Temporary password", key="biz_owner_password", type="password",
                    help="The owner can use this password for their first sign-in.",
                )
                if st.button("Generate secure password", key="generate_biz_password"):
                    alphabet = string.ascii_letters + string.digits
                    st.session_state.biz_owner_password = "".join(
                        pysecrets.choice(alphabet) for _ in range(12)
                    )
                    st.rerun()

            st.caption("Agency data and user access are isolated from every other agency.")
            if st.button("Create agency", type="primary", disabled=not biz_name.strip(), width="stretch"):
                if not is_valid_email(owner_email):
                    st.error("Enter a valid owner email address.")
                    st.stop()
                if not owner_password.strip():
                    st.error("Enter a temporary password, or generate one.")
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

    with directory_tab:
        st.markdown("""
        <div class="admin-section-head">
          <h2>Agency directory</h2>
          <p>Find an agency, review its access, or update its owner credentials.</p>
        </div>
        """, unsafe_allow_html=True)
        f1, f2 = st.columns([2.2, 1])
        search_agencies = f1.text_input(
            "Search agencies", placeholder="Search by agency name or ID",
            key="platform_agency_search", label_visibility="collapsed",
        )
        status_filter = f2.selectbox(
            "Status", ["All statuses", "Active", "Disabled"],
            key="platform_status_filter", label_visibility="collapsed",
        )
        visible_businesses = businesses.copy()
        if search_agencies.strip() and not visible_businesses.empty:
            needle = search_agencies.strip().lower()
            visible_businesses = visible_businesses[
                visible_businesses["business_name"].astype(str).str.lower().str.contains(needle, regex=False)
                | visible_businesses["business_id"].astype(str).str.lower().str.contains(needle, regex=False)
            ]
        if status_filter != "All statuses" and not visible_businesses.empty:
            visible_businesses = visible_businesses[visible_businesses["status"] == status_filter]
        st.caption(f"Showing {len(visible_businesses)} of {len(businesses)} agencies")
    if visible_businesses.empty:
        st.info("No agencies match your current search and status filters.")
    else:
        for _, b in visible_businesses.iterrows():
            bid = b["business_id"]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.15], vertical_alignment="center")
                owners_df = store.get_users(bid)
                owners_only = owners_df[owners_df["role"] == "owner"] if not owners_df.empty else owners_df
                owner_count = len(owners_only)
                agency_count = len(store.get_agencies(bid))
                c1.markdown(f"### {b['business_name']}")
                c1.markdown(f"`{bid}` &nbsp; · &nbsp; {owner_count} owner account(s) "
                            f"&nbsp; · &nbsp; {agency_count} Sub-Agencies")
                status_class = "active" if b["status"] == "Active" else "disabled"
                c1.markdown(f'<span class="agency-status {status_class}">{b["status"]}</span>',
                            unsafe_allow_html=True)
                with c2:
                    b1, b2 = st.columns(2)
                    if b1.button("Manage", key=f"editbiz_{bid}", width="stretch"):
                        st.session_state["editing_biz"] = None if st.session_state.get("editing_biz") == bid else bid
                        st.rerun()
                    with b2:
                        if b["status"] == "Active":
                            if st.button("Disable", key=f"disbiz_{bid}", width="stretch"):
                                store.set_business_status(bid, "Disabled")
                                refresh_caches()
                                st.toast(f"{b['business_name']} disabled.")
                                st.rerun()
                        else:
                            if st.button("Enable", key=f"enbiz_{bid}", type="primary", width="stretch"):
                                store.set_business_status(bid, "Active")
                                refresh_caches()
                                st.toast(f"{b['business_name']} enabled.", icon="\u2705")
                                st.rerun()

                if st.session_state.get("editing_biz") == bid:
                    st.divider()
                    st.markdown("###### Agency details")
                    new_name = st.text_input("Agency name", value=b["business_name"], key=f"rename_{bid}")
                    if st.button("Save agency name", key=f"savename_{bid}", type="primary"):
                        store.update_business_name(bid, new_name.strip() or b["business_name"])
                        refresh_caches()
                        st.toast("Agency name updated.", icon="\u2705")
                        st.rerun()

                    st.markdown("###### Owner access")
                    if owners_only.empty:
                        st.info("No owner account exists for this agency yet.")
                    else:
                        for _, ow in owners_only.iterrows():
                            oc1, oc2 = st.columns([2, 1], vertical_alignment="center")
                            oc1.markdown(f"**{ow['name']}**  \n`{ow['username']}`")
                            with oc2:
                                with st.popover("Reset password", use_container_width=True):
                                    newpw = st.text_input("New password", type="password",
                                                          key=f"bizpw_{ow['username']}")
                                    if st.button("Save password", key=f"bizpwsave_{ow['username']}",
                                                 type="primary", width="stretch"):
                                        if newpw.strip():
                                            store.reset_user_password(ow["username"], newpw.strip())
                                            st.success("Password updated.")
                                        else:
                                            st.error("Enter a new password.")

# ================================================================ MY PROFILE
elif st.session_state.page == "MyProfile":
    st.title("My profile")
    st.caption("Visible only to you \u2014 change your display name or profile picture any time.")

    col1, col2 = st.columns([1, 3])
    with col1:
        if avatar_b64:
            st.markdown(
                f'<img src="data:image/png;base64,{avatar_b64}" '
                f'style="width:96px;height:96px;border-radius:50%;object-fit:cover;">',
                unsafe_allow_html=True,
            )
        else:
            initials = "".join([p[0].upper() for p in display_name.split()[:2]]) or "?"
            st.markdown(
                f'<div style="width:96px;height:96px;border-radius:50%;background:#EEF3E7;'
                f'color:#3F6B1E;display:flex;align-items:center;justify-content:center;'
                f'font-size:32px;font-weight:700;">{initials}</div>',
                unsafe_allow_html=True,
            )
    with col2:
        st.markdown(f"**{display_name}**")
        st.caption(f"{username} \u00b7 {user_role.replace('_', ' ')}")

    st.markdown("##### Display name")
    new_display_name = st.text_input("Name", value=display_name, key="profile_name")
    if st.button("Save name", type="primary", disabled=not new_display_name.strip()):
        store.upsert_profile(username, display_name=new_display_name.strip())
        refresh_caches()
        st.toast("Name updated.", icon="\u2705")
        st.rerun()

    st.markdown("##### Profile picture")
    pic = st.file_uploader("Upload a picture (PNG or JPG, under 1.5 MB)", type=["png", "jpg", "jpeg"], key="profile_pic")
    if pic is not None:
        if pic.size > 1_500_000:
            st.error("That image is too large \u2014 please use a picture under 1.5 MB.")
        else:
            encoded = base64.b64encode(pic.read()).decode("utf-8")
            if st.button("Save picture", type="primary"):
                store.upsert_profile(username, avatar_base64=encoded)
                refresh_caches()
                st.toast("Profile picture updated.", icon="\u2705")
                st.rerun()

    if avatar_b64:
        if st.button("Remove current picture"):
            store.upsert_profile(username, avatar_base64="")
            refresh_caches()
            st.toast("Profile picture removed.", icon="\u2705")
            st.rerun()

# ==================================================================== ADMIN
elif st.session_state.page == "Admin":
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    overview_title = "Business overview" if is_owner else f"{html.escape(str(user_agency))} overview"
    overview_subtitle = (f"Performance across {html.escape(str(business_name))}'s agency network" if is_owner
                         else "Performance for your assigned broadcaster roster")
    st.markdown(f"""
    <div class="overview-hero">
      <div>
        <div class="overview-eyebrow">{'Agency owner' if is_owner else 'Sub-Agency workspace'}</div>
        <h1>{overview_title}</h1>
        <p>{overview_subtitle}</p>
      </div>
      <div class="overview-period-pill">Live operational overview</div>
    </div>
    """, unsafe_allow_html=True)

    monthly_periods = store.list_periods("monthly", business_id)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet. Go to **Upload report** in the sidebar.")
        st.stop()

    if is_owner:
        filter_month, filter_agency = st.columns(2)
        with filter_month:
            current_period = st.selectbox(
                "Reporting month", sorted(monthly_periods, reverse=True), key="admin_month"
            )
        df_current_all = period_data(current_period, "monthly")
        with filter_agency:
            df_current, agency_choice = agency_filter_widget(df_current_all, "admin_agency")
    else:
        current_period = st.selectbox(
            "Reporting month", sorted(monthly_periods, reverse=True), key="admin_month"
        )
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
    sub_commission_pct = (store.get_agency_commission(business_id, user_agency)
                          if is_sub_agency else None)
    sub_gross_usd, sub_commission_usd = calculate_sub_agency_earnings(
        kpis["diamonds_redeemed"], sub_commission_pct
    )
    retention = utils.retention_rate(df_current, df_previous) if not df_previous.empty else None
    at_risk_df = (utils.at_risk_broadcasters(df_current, df_previous)
                  if not df_previous.empty else df_current.iloc[0:0])
    health_score = utils.broadcaster_health_score(df_current, df_previous)
    health_label = "Excellent" if health_score >= 85 else "Healthy" if health_score >= 70 else "Watch" if health_score >= 55 else "Needs attention"
    diamond_target = utils.performance_target(
        kpis["diamonds_redeemed"], prev_kpis.get("diamonds_redeemed", 0), growth_goal=.08
    )

    def overview_delta(metric):
        if not prev_kpis:
            return "First reporting period", ""
        pct, delta_direction = utils.compare_periods(kpis, prev_kpis, metric)
        arrow = "↑" if delta_direction == "up" else "↓"
        return f"{arrow} {abs(pct):.1f}% vs {previous_period}", delta_direction

    broadcaster_note, broadcaster_direction = overview_delta("broadcasters")
    active_note, active_direction = overview_delta("active")
    diamond_note, diamond_direction = overview_delta("diamonds_redeemed")
    earning_note, earning_direction = overview_delta("my_earnings_usd")
    days_note, days_direction = overview_delta("days_worked")

    score_col, alert_col = st.columns(2)
    with score_col:
        st.markdown(f"""
        <div class="command-score">
          <div class="command-score-ring" style="--score:{health_score}"><div class="command-score-value">{health_score}</div></div>
          <div class="command-score-copy"><h3>Broadcaster health score</h3>
          <p><strong>{health_label}</strong><br>Activity, retention, consistency and performance movement combined into one transparent score.</p></div>
        </div>
        """, unsafe_allow_html=True)
    with alert_col:
        warning_copy = ("Previously productive broadcasters have no streaming activity this month."
                        if len(at_risk_df) else "No previously productive broadcasters have dropped to zero activity.")
        st.markdown(f"""
        <div class="command-alert">
          <div class="command-alert-label">Retention warning</div>
          <div class="command-alert-value">{len(at_risk_df)} broadcaster{'s' if len(at_risk_df) != 1 else ''} at risk</div>
          <div class="command-alert-copy">{warning_copy}</div>
          <div class="command-footnote">Retention: {f'{retention:.1f}%' if retention is not None else 'First reporting period'}</div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        overview_kpi_card("Total broadcasters", f"{kpis['broadcasters']:,}", "♟",
                          broadcaster_note, broadcaster_direction)
    with c2:
        overview_kpi_card("Active broadcasters", f"{kpis['active']:,}", "●",
                          active_note, active_direction)
    with c3:
        overview_kpi_card("Diamonds redeemed", f"{kpis['diamonds_redeemed']:,}", "◇",
                          diamond_note, diamond_direction)
    c4, c5, c6 = st.columns(3)
    with c4:
        if is_owner:
            overview_kpi_card("Agency earnings", f"${kpis['my_earnings_usd']:,.2f}", "$",
                              earning_note, earning_direction)
        elif sub_commission_usd is None:
            overview_kpi_card("Commission earnings", "Not set", "$",
                              "Ask the agency owner to set your commission rate")
        else:
            overview_kpi_card(
                "Commission earnings", f"${sub_commission_usd:,.2f}", "$",
                f"{sub_commission_pct:g}% of ${sub_gross_usd:,.2f} redeemed value",
            )
    with c5:
        overview_kpi_card("Days streamed", f"{kpis['days_worked']:,}", "◷",
                          days_note, days_direction)
    with c6:
        overview_kpi_card("Avg diamonds / broadcaster", f"{avg_dpb:,.1f}", "↗",
                          f"Across {n_agencies} active Sub-Agencies" if is_owner else "Current roster average")

    st.markdown("""
    <div class="overview-section">
      <h2>Automated insights</h2>
      <p>Signals that may need attention this reporting period.</p>
    </div>
    """, unsafe_allow_html=True)
    dpd_df = utils.diamonds_per_day(df_current)
    avg_dpd = round(dpd_df["diamonds_per_day"].mean(), 1) if not dpd_df.empty else 0
    quality_score = utils.data_quality_score(df_current)

    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.markdown(f"""
        <div class="insight-card">
          <div class="insight-label">Retention health</div>
          <div class="insight-value">{f'{retention}%' if retention is not None else '—'}</div>
          <div class="insight-caption">Previously active broadcasters retained</div>
        </div>
        """, unsafe_allow_html=True)
    with i2:
        st.markdown(f"""
        <div class="insight-card">
          <div class="insight-label">Requires attention</div>
          <div class="insight-value">{len(at_risk_df)} at risk</div>
          <div class="insight-caption">Active last period with no streaming days now</div>
        </div>
        """, unsafe_allow_html=True)
    with i3:
        if is_owner:
            st.markdown(f"""
            <div class="insight-card">
              <div class="insight-label">Roster attribution</div>
              <div class="insight-value">{attribution_all['pct_assigned']}% complete</div>
              <div class="insight-caption">Broadcasters assigned to a Sub-Agency</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="insight-card">
              <div class="insight-label">Daily efficiency</div>
              <div class="insight-value">{avg_dpd:,}</div>
              <div class="insight-caption">Average diamonds redeemed per streaming day</div>
            </div>
            """, unsafe_allow_html=True)
    with i4:
        st.markdown(f"""
        <div class="insight-card">
          <div class="insight-label">Data quality</div>
          <div class="insight-value">{quality_score}/100</div>
          <div class="insight-caption">Completeness, valid values and unique profiles</div>
        </div>
        """, unsafe_allow_html=True)

    if len(at_risk_df) > 0:
        with st.expander(f"{len(at_risk_df)} broadcaster(s) earned diamonds last period, streamed 0 days this period"):
            at_risk_columns = (["broadcaster_name", "sub_agency"] if is_owner
                               else ["broadcaster_name"])
            st.dataframe(
                at_risk_df[at_risk_columns].reset_index(drop=True),
                hide_index=True, width='stretch',
                column_config=table_column_config(at_risk_columns),
            )

    # Rule-based monthly summary and follow-up list: useful without a paid AI service.
    movement_text = (f"Diamonds are {abs(float(diamond_note.split()[1].replace('%',''))):.1f}% "
                     f"{'higher' if diamond_direction == 'up' else 'lower'} than {previous_period}"
                     if prev_kpis else "This is the first available reporting period")
    st.info(
        f"**Monthly management summary:** {movement_text}. Health is **{health_label.lower()}** at "
        f"**{health_score}/100**, retention is **{f'{retention:.1f}%' if retention is not None else 'not yet available'}**, "
        f"and **{len(at_risk_df)}** broadcaster(s) currently need retention follow-up."
    )
    follow_up_rows = []
    for _, risk_row in at_risk_df.head(8).iterrows():
        follow_up_rows.append({
            "Priority": "High", "Broadcaster": risk_row["broadcaster_name"],
            "Sub-Agency": risk_row.get("sub_agency", user_agency or "—"),
            "Reason": "Previously productive; no streaming days this month",
            "Recommended action": "Contact and agree a reactivation plan",
        })
    if is_owner and attribution_all["unassigned"] > 0:
        follow_up_rows.append({
            "Priority": "Medium", "Broadcaster": f"{attribution_all['unassigned']} unassigned profiles",
            "Sub-Agency": "Unassigned", "Reason": "Roster attribution is incomplete",
            "Recommended action": "Review and assign broadcasters",
        })
    if not diamond_target["ahead"]:
        follow_up_rows.append({
            "Priority": "Medium", "Broadcaster": "Selected roster", "Sub-Agency": scope_agency or "All",
            "Reason": f"{diamond_target['remaining']:,.0f} diamonds below monthly target",
            "Recommended action": "Review declining broadcasters and target pacing",
        })
    if follow_up_rows:
        with st.expander(f"Follow-up task list ({len(follow_up_rows)})", expanded=False):
            st.dataframe(pd.DataFrame(follow_up_rows), hide_index=True, width="stretch")
    else:
        st.success("No urgent follow-up tasks for the selected reporting period.")

    st.markdown("""
    <div class="command-grid-title"><div><h2>Target and financial outlook</h2>
    <p>Current progress against an 8% improvement target based on the previous reporting period.</p></div></div>
    """, unsafe_allow_html=True)
    outlook_left, outlook_right = st.columns([1, 1.45])
    progress_width = min(100, max(0, diamond_target["progress_pct"]))
    with outlook_left:
        with st.container(border=True):
            st.markdown("##### Monthly performance target")
            st.metric("Diamonds redeemed", f"{kpis['diamonds_redeemed']:,.0f}",
                      f"Target {diamond_target['target']:,.0f}")
            st.markdown(
                f'<div class="command-progress"><span style="width:{progress_width}%"></span></div>',
                unsafe_allow_html=True,
            )
            target_message = (f"Ahead of target by {kpis['diamonds_redeemed'] - diamond_target['target']:,.0f} diamonds."
                              if diamond_target["ahead"] else
                              f"{diamond_target['remaining']:,.0f} diamonds remaining to reach target.")
            st.caption(f"{diamond_target['progress_pct']:.1f}% achieved · {target_message}")
            if is_sub_agency:
                st.divider()
                st.markdown("##### Commission summary")
                pc1, pc2 = st.columns(2)
                pc1.metric("Gross redeemed value", f"${sub_gross_usd:,.2f}")
                pc2.metric("Commission earned", "Not set" if sub_commission_usd is None else f"${sub_commission_usd:,.2f}")
                statement = df_current[["broadcaster_name", "diamonds_redeemed", "streaming_days"]].copy()
                statement["gross_value_usd"] = statement["diamonds_redeemed"] / DIAMONDS_PER_USD
                statement["commission_pct"] = sub_commission_pct
                statement["commission_usd"] = (statement["gross_value_usd"] * sub_commission_pct / 100
                                                if sub_commission_pct is not None else None)
                st.download_button(
                    "Download commission statement", statement.to_csv(index=False).encode("utf-8"),
                    file_name=f"commission_statement_{user_agency}_{current_period}.csv",
                    mime="text/csv", width="stretch",
                )
    with outlook_right:
        if is_owner:
            comparison_rows = []
            agency_details = store.get_agency_details(business_id)
            rates = {row["agency_name"]: (None if pd.isna(row["commission_pct"]) else float(row["commission_pct"]))
                     for _, row in agency_details.iterrows()}
            for sub_name in load_agencies(business_id):
                sub_df = utils.filter_by_agency(df_current_all, sub_name)
                sub_kpis = utils.compute_kpis(sub_df)
                gross, due = calculate_sub_agency_earnings(sub_kpis["diamonds_redeemed"], rates.get(sub_name))
                comparison_rows.append({"Sub-Agency": sub_name, "Diamonds": sub_kpis["diamonds_redeemed"],
                                        "Active": sub_kpis["active"], "Gross value": gross,
                                        "Commission due": due or 0})
            comparison = pd.DataFrame(comparison_rows)
            if comparison.empty:
                st.info("Create and assign a Sub-Agency to unlock performance comparison.")
            else:
                comparison = comparison.sort_values("Diamonds", ascending=True)
                compare_fig = go.Figure(go.Bar(
                    x=comparison["Diamonds"], y=comparison["Sub-Agency"], orientation="h",
                    marker=dict(color="#3F6B1E"), text=comparison["Diamonds"], texttemplate="%{text:,.0f}",
                    textposition="outside", hovertemplate="%{y}<br>%{x:,.0f} diamonds<extra></extra>",
                ))
                compare_fig.update_layout(
                    title="Sub-Agency performance", height=285, margin=dict(l=10, r=45, t=50, b=20),
                    xaxis=dict(showgrid=True, gridcolor="#E8ECE5", title=None),
                    yaxis=dict(title=None), paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                    font=dict(family="Inter", color="#4C5548"), showlegend=False,
                )
                with st.container(border=True):
                    st.plotly_chart(compare_fig, use_container_width=True, config={"displayModeBar": False})
                    fc1, fc2 = st.columns(2)
                    fc1.metric("Forecast commission", f"${comparison['Commission due'].sum():,.2f}")
                    fc2.metric("Redeemed value", f"${comparison['Gross value'].sum():,.2f}")
        else:
            roster_view = utils.add_growth_status(df_current, df_previous)
            roster_columns = ["broadcaster_name", "status", "diamonds_redeemed", "streaming_days", "growth_pct"]
            with st.container(border=True):
                st.markdown("##### Assigned broadcaster performance")
                st.dataframe(
                    roster_view[roster_columns].sort_values("diamonds_redeemed", ascending=False).head(8),
                    hide_index=True, width="stretch", column_config=table_column_config(roster_columns),
                )

    st.markdown("""
    <div class="overview-section">
      <h2>Performance trend</h2>
      <p>Diamonds redeemed and active broadcaster movement over time.</p>
    </div>
    """, unsafe_allow_html=True)
    trend_periods = sorted(monthly_periods)[-6:]
    if len(trend_periods) > 1:
        trend_diamonds, trend_active = [], []
        for trend_period in trend_periods:
            trend_df = period_data(trend_period, "monthly")
            trend_df = utils.filter_by_agency(trend_df, scope_agency)
            trend_kpis = utils.compute_kpis(trend_df)
            trend_diamonds.append(trend_kpis["diamonds_redeemed"])
            trend_active.append(trend_kpis["active"])

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            name="Diamonds redeemed", x=trend_periods, y=trend_diamonds,
            mode="lines+markers", line=dict(color="#3F6B1E", width=3),
            marker=dict(size=8, color="#3F6B1E"), fill="tozeroy",
            fillcolor="rgba(63,107,30,.09)", hovertemplate="%{x}<br>%{y:,.0f} diamonds<extra></extra>",
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            name="Active broadcasters", x=trend_periods, y=trend_active,
            mode="lines+markers", line=dict(color="#E2812C", width=2.5),
            marker=dict(size=7, color="#E2812C"),
            hovertemplate="%{x}<br>%{y:,.0f} active<extra></extra>",
        ), secondary_y=True)
        fig.update_layout(
            height=390, margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.04, x=0),
            font=dict(family="Inter", color="#4C5548"),
        )
        fig.update_xaxes(showgrid=False, title=None)
        fig.update_yaxes(title_text="Diamonds", gridcolor="#E8ECE5", zeroline=False, secondary_y=False)
        fig.update_yaxes(title_text="Active broadcasters", showgrid=False, zeroline=False, secondary_y=True)
        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Upload a second month to unlock the performance trend.")

    st.markdown("""
    <div class="overview-section">
      <h2>Top performers</h2>
      <p>Broadcasters leading the selected period by diamonds redeemed.</p>
    </div>
    """, unsafe_allow_html=True)
    top5 = utils.leaderboard(df_current, 5)
    if top5.empty:
        st.info("No broadcaster performance data is available for this selection yet.")
    else:
        cols = ["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"] if is_owner \
            else ["broadcaster_name", "diamonds_redeemed", "streaming_days"]
        with st.container(border=True):
            st.dataframe(
                top5[cols], hide_index=True, width='stretch',
                column_config=table_column_config(cols),
            )

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
            width='stretch', hide_index=True,
            column_config=table_column_config(show_cols),
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
        agency_pick = st.selectbox("Sub-Agency", ["All"] + load_agencies(business_id) + ["Unassigned"], key="bl_agency") \
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
        column_config=table_column_config(show_cols),
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
    st.title("Sub-Agency Management")
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="sa_month")
    df = period_data(current_period, "monthly")
    prev_period = previous_period_of(current_period, "monthly")
    df_prev = period_data(prev_period, "monthly") if prev_period else pd.DataFrame()

    agencies = load_agencies(business_id)
    agency_details = store.get_agency_details(business_id)
    commission_by_agency = {
        row["agency_name"]: (None if pd.isna(row["commission_pct"]) else float(row["commission_pct"]))
        for _, row in agency_details.iterrows()
    }
    rows = []
    for a in agencies + ["Unassigned"]:
        sub = utils.filter_by_agency(df, a)
        sub_prev = utils.filter_by_agency(df_prev, a) if not df_prev.empty else pd.DataFrame()
        k = utils.compute_kpis(sub)
        pk = utils.compute_kpis(sub_prev) if not sub_prev.empty else {}
        pct, _ = utils.compare_periods(k, pk, "diamonds_redeemed") if pk else (None, None)
        commission_pct = commission_by_agency.get(a)
        gross_usd, commission_due = calculate_sub_agency_earnings(k["diamonds_redeemed"], commission_pct)
        rows.append(dict(
            agency=a, broadcasters=k["broadcasters"], active=k["active"],
            diamonds=k["diamonds_redeemed"], days=k["days_worked"], growth=pct,
            commission_pct=commission_pct, gross_usd=gross_usd, commission_due=commission_due,
        ))
    summary = pd.DataFrame(rows)

    sort_choice = st.selectbox(
        "Sort by", ["Diamonds", "Growth", "Active broadcasters", "Days streamed", "Broadcaster count"], key="sa_sort"
    )
    sort_map = {"Diamonds": "diamonds", "Growth": "growth", "Active broadcasters": "active",
                "Days streamed": "days", "Broadcaster count": "broadcasters"}
    summary = summary.sort_values(sort_map[sort_choice], ascending=False, na_position="last")

    for _, r in summary.iterrows():
        with st.container(border=True):
            gcol, bcol = st.columns([3, 1], vertical_alignment="center")
            gcol.markdown(f"**{r['agency']}**")
            if r["growth"] is not None:
                arrow = "\u25b2" if r["growth"] >= 0 else "\u25bc"
                bcol.markdown(f"{arrow} {r['growth']}%")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Broadcasters", r["broadcasters"])
            m2.metric("Active", r["active"])
            m3.metric("Diamonds", f"{r['diamonds']:,}")
            m4.metric("Days", r["days"])
            commission_value = r["commission_due"]
            m5.metric(
                "Commission due",
                "—" if pd.isna(commission_value) else f"${commission_value:,.2f}",
                help=("Redeemed diamonds ÷ 200 × commission percentage" if r["agency"] != "Unassigned"
                      else "Unassigned broadcasters do not have a Sub-Agency commission."),
            )

            if r["agency"] != "Unassigned":
                rate_value = r["commission_pct"]
                rate_text = "Not set" if pd.isna(rate_value) else f"{rate_value:g}%"
                st.caption(
                    f"Commission rate: **{rate_text}** · Redeemed value: **${r['gross_usd']:,.2f}** "
                    f"(diamonds ÷ {DIAMONDS_PER_USD})"
                )
                with st.popover("Update commission", use_container_width=False):
                    new_rate = st.number_input(
                        "Commission percentage", min_value=1.0, max_value=20.0,
                        value=float(rate_value) if not pd.isna(rate_value) else 5.0,
                        step=0.1, format="%.2f", key=f"commission_{r['agency']}",
                    )
                    example_gross, example_due = calculate_sub_agency_earnings(20_000, new_rate)
                    st.caption(
                        f"Example: 20,000 diamonds = ${example_gross:,.2f}; "
                        f"{new_rate:g}% commission = ${example_due:,.2f}."
                    )
                    if st.button("Save commission", type="primary", key=f"save_commission_{r['agency']}"):
                        store.update_agency_commission(business_id, r["agency"], new_rate)
                        refresh_caches()
                        st.toast(f"Commission updated to {new_rate:g}%.", icon="\u2705")
                        st.rerun()

# ================================================================== ASSIGN
elif st.session_state.page == "Assign":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Assign broadcasters")
    st.caption("Pick a month already uploaded, then assign broadcasters to a Sub-Agency.")

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

    assignment_columns = ["broadcaster_name", "profile_url", "sub_agency", "diamonds_redeemed"]
    st.dataframe(
        view[assignment_columns].sort_values("diamonds_redeemed", ascending=False),
        width='stretch', hide_index=True,
        column_config=table_column_config(assignment_columns),
    )

    st.markdown("##### Assign selected")
    options = view["profile_url"].tolist()
    labels = dict(zip(view["profile_url"], view["broadcaster_name"]))
    selected = st.multiselect("Pick broadcasters (by name)", options, format_func=lambda u: labels.get(u, u))
    agencies = load_agencies(business_id)
    if not agencies:
        st.info("No Sub-Agencies yet \u2014 add one first under **Create Sub-Agency**.")
    else:
        target_agency = st.selectbox("Sub-Agency", agencies)
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
    st.title("Create Sub-Agency")

    name = st.text_input("Agency name (e.g. Partner X)", key="ca_name")
    contact = st.text_input("Contact person", key="ca_contact")
    phone = st.text_input("Phone", key="ca_phone")
    commission_pct = st.number_input(
        "Commission percentage", min_value=1.0, max_value=20.0, value=5.0,
        step=0.1, format="%.2f", key="ca_commission_pct",
        help="The percentage of this Sub-Agency's redeemed diamond value that they receive.",
    )
    example_gross, example_commission = calculate_sub_agency_earnings(20_000, commission_pct)
    st.info(
        f"Calculation example: **20,000 diamonds ÷ {DIAMONDS_PER_USD} = USD {example_gross:,.2f}** "
        f"redeemed value. At **{commission_pct:g}%**, the Sub-Agency earns "
        f"**USD {example_commission:,.2f}**."
    )

    st.markdown("###### Login access")
    make_login = st.checkbox("Also create a login for this partner", value=True, key="ca_make_login")
    login_email, password = "", ""
    if make_login:
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        with c1:
            login_email = st.text_input("Login email", key="ca_email")
        with c2:
            if st.button("Generate password", width="stretch"):
                alphabet = string.ascii_letters + string.digits
                st.session_state.ca_password = "".join(pysecrets.choice(alphabet) for _ in range(10))
        password = st.text_input("Password", key="ca_password")

    status = st.selectbox("Status", ["Active", "Inactive"], key="ca_status")
    notes = st.text_area("Notes", key="ca_notes")

    if st.button("Create Sub-Agency", type="primary", disabled=not name.strip()):
        if name.strip() in load_agencies(business_id):
            st.error("A Sub-Agency with this name already exists. Update its commission under Sub-Agency Management.")
            st.stop()
        if make_login:
            if not is_valid_email(login_email):
                st.error("Enter a valid login email to also create a login.")
                st.stop()
            if not password.strip():
                st.error("Enter a password (or generate one) to also create a login.")
                st.stop()
            if store.username_taken(login_email.strip()):
                st.error("That login email is already registered on this platform.")
                st.stop()

        store.add_agency(name.strip(), business_id, commission_pct)
        msg = f"Created Sub-Agency {name.strip()} with a {commission_pct:g}% commission."
        if make_login:
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

    st.markdown("##### Existing Sub-Agencies")
    existing_agencies = store.get_agency_details(business_id)
    if existing_agencies.empty:
        st.caption("No Sub-Agencies created yet.")
    else:
        for _, agency_row in existing_agencies.iterrows():
            existing_rate = agency_row["commission_pct"]
            rate_label = "Not set" if pd.isna(existing_rate) else f"{float(existing_rate):g}%"
            st.write(f"\u2022 **{agency_row['agency_name']}** · Commission: **{rate_label}**")

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
        preview_columns = ["broadcaster_name", "diamonds_redeemed", "streaming_days"]
        st.dataframe(
            clean_df[preview_columns].head(10), hide_index=True, width='stretch',
            column_config=table_column_config(preview_columns),
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
            new_agency = st.selectbox("Sub-Agency", agencies, key="ua_agency") if agencies else None
        new_password = st.text_input("Password", key="ua_password")

    if st.button("Create user", type="primary"):
        if not is_valid_email(new_email):
            st.error("Enter a valid email address.")
        elif not new_password.strip():
            st.error("Password is required.")
        elif new_role == "sub_agency" and not new_agency:
            st.error("Create a Sub-Agency first, then assign this login to it.")
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
        st.caption("No additional users yet \u2014 you're the only login for this agency.")
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
                period_columns = ["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"]
                st.dataframe(
                    view_df[period_columns],
                    hide_index=True, width='stretch',
                    column_config=table_column_config(period_columns),
                )

    st.markdown("---")
    with st.container(border=True):
        st.markdown("##### :red[Danger zone]")
        st.caption("Permanently deletes a period's numbers. Sub-Agency assignments are not affected.")
        target = st.selectbox("Period to clear", all_periods, key="dm_clear_target") if all_periods else None
        confirm = st.checkbox(f"I understand this deletes {ptype} data for the selected period", key="dm_confirm")
        if st.button("Clear this period", type="primary", disabled=not (confirm and target)):
            store.clear_period(target, ptype, business_id)
            refresh_caches()
            st.toast(f"Cleared {ptype} data for {target}.", icon="\u2705")
            st.rerun()
