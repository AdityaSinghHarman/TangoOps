import datetime as dt
import re
import base64
import html
import secrets as pysecrets
import string
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit_authenticator as stauth
from PIL import Image

import utils
import store

ASSET_DIR = Path(__file__).resolve().parent / "assets"
BRAND_ICON_PATH = ASSET_DIR / "streamoperiq-app-icon-transparent.png"
BRAND_FAVICON_PATH = BRAND_ICON_PATH
BRAND_TOKENS_CSS = (ASSET_DIR / "streamoperiq-tokens.css").read_text(encoding="utf-8")


def image_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


BRAND_ICON_URI = image_data_uri(BRAND_ICON_PATH)

SO_BRAND = "#211A4A"
SO_VIOLET = "#7C3AED"
SO_PERIWINKLE = "#8B5CF6"
SO_CYAN = "#22D3EE"
SO_COBALT = "#2563EB"
SO_TEXT = "#111827"
SO_MUTED = "#475569"
SO_SURFACE = "#FFFFFF"
SO_BORDER = "#E4E7F2"
SO_SUCCESS = "#059669"
SO_WARNING = "#D97706"
SO_DANGER = "#DC2626"
SO_GRID = SO_BORDER
SO_BRAND_FILL = "rgba(124,58,237,.09)"
SO_CHART_COLORS = [SO_BRAND, SO_VIOLET, SO_PERIWINKLE, SO_CYAN, SO_COBALT, SO_SUCCESS, SO_WARNING]

st.set_page_config(
    page_title="StreamOperiq",
    layout="wide",
    page_icon=Image.open(BRAND_FAVICON_PATH),
)

# ---------------------------------------------------------------- styling ---
st.markdown(f"<style>{BRAND_TOKENS_CSS}</style>", unsafe_allow_html=True)
st.markdown("""
<style>
:root{
  --brand:var(--so-brand); --brand-soft:#F1EDFF; --ink:var(--so-text);
  --card-radius:var(--so-radius-card); --border:var(--so-border);
}

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
.overview-kpi{ min-height:150px; height:100%; display:flex; flex-direction:column; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; padding:1.15rem 1.2rem; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.overview-kpi-top{ display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
.overview-kpi-label{ color:#667063; font-size:.78rem; font-weight:650; }
.overview-kpi-icon{ width:2rem; height:2rem; display:grid; place-items:center; color:#47742B; background:#EAF3E4; border-radius:.65rem; font-size:1rem; }
.overview-kpi-value{ color:#182116; font-size:1.85rem; line-height:1; font-weight:760; letter-spacing:-.035em; }
.overview-kpi-note{ color:#778073; font-size:.73rem; margin-top:auto; padding-top:.75rem; }
.overview-kpi-note.up{ color:#287331; }.overview-kpi-note.down{ color:#B1453D; }
.overview-section{ margin:1.7rem 0 .8rem; }
.overview-section h2{ color:#1C251A; font-size:1.25rem; margin:0 0 .25rem; }
.overview-section p{ color:#747C70; font-size:.84rem; margin:0; }
.insight-card{ min-height:116px; height:100%; display:flex; flex-direction:column; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; padding:1.05rem 1.1rem; }
.insight-label{ color:#70796C; font-size:.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; margin-bottom:.65rem; }
.insight-value{ color:#1B2419; font-size:1.35rem; font-weight:750; letter-spacing:-.025em; }
.insight-caption{ color:#727A6F; font-size:.76rem; margin-top:auto; padding-top:.35rem; }
.stApp:has(.owner-overview-page) div[data-testid="stVerticalBlockBorderWrapper"]{ background:#FFFFFF; border-color:#E0E5DC; border-radius:1rem; box-shadow:0 2px 8px rgba(30,45,23,.025); }
.stApp:has(.owner-overview-page) div[data-baseweb="select"] > div{ background:#FFFFFF; border-color:#D9E0D5; }

/* Option 1 — Executive Command Center */
.command-grid-title{ display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:1.6rem 0 .75rem; }
.command-grid-title h2{ color:#172016; font-size:1.2rem; margin:0; }
.command-grid-title p{ color:#737D70; font-size:.82rem; margin:.2rem 0 0; }
.command-score{ min-height:164px; height:100%; display:flex; align-items:center; gap:1.15rem; padding:1.2rem;
  background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; }
.command-score-ring{ --score:0; position:relative; flex:none; width:6.25rem; height:6.25rem; border-radius:50%;
  display:grid; place-items:center; background:conic-gradient(#74A843 calc(var(--score)*1%),#E8EDE5 0); }
.command-score-ring::before{ content:''; position:absolute; width:4.75rem; height:4.75rem; border-radius:50%; background:#fff; }
.command-score-value{ position:relative; color:#172016; font-size:1.7rem; font-weight:780; }
.command-score-copy h3{ color:#1C251A; font-size:1rem; margin:0 0 .35rem; }
.command-score-copy p{ color:#6E786B; font-size:.76rem; line-height:1.45; margin:0; }
.command-alert{ min-height:164px; height:100%; display:flex; flex-direction:column; padding:1.2rem; background:#FFFFFF; border:1px solid #E0E5DC; border-radius:1rem; }
.command-alert-label{ color:#B05C16; font-size:.7rem; font-weight:750; text-transform:uppercase; letter-spacing:.07em; }
.command-alert-value{ color:#1B2419; font-size:1.8rem; font-weight:780; margin:.65rem 0 .25rem; }
.command-alert-copy{ color:#70796D; font-size:.76rem; line-height:1.45; }
.command-progress{ height:.52rem; overflow:hidden; background:#E8EDE5; border-radius:999px; margin:.8rem 0 .55rem; }
.command-progress span{ display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#315E18,#9ACB31); }
.command-table-badge{ display:inline-flex; align-items:center; padding:.22rem .5rem; border-radius:999px;
  color:#2E6B2A; background:#EAF4E5; font-size:.68rem; font-weight:700; }
.command-footnote{ color:#788176; font-size:.7rem; margin-top:auto; padding-top:.45rem; }
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
button:focus-visible, a:focus-visible, input:focus-visible, [role="button"]:focus-visible{
  outline:3px solid rgba(63,107,30,.35) !important; outline-offset:2px;
}
@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{ scroll-behavior:auto !important; transition:none !important; animation:none !important; }
  .kpi-card:hover{ transform:none; }
}

h1, h2, h3 { letter-spacing:-0.02em; }

/* StreamOperiq brand layer — approved tokens are the source of truth. */
.stApp{ background:var(--so-background); color:var(--so-text); font-family:var(--so-font); }
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{ color:var(--so-brand); }
.stApp p,.stApp label{ color:var(--so-text); }
.stApp [data-testid="stCaptionContainer"]{ color:var(--so-text-muted); }
.stApp section[data-testid="stSidebar"]{
  background:var(--so-surface); border-right:1px solid var(--so-border);
}
.stApp div[data-testid="stVerticalBlockBorderWrapper"],
.stApp div[data-testid="stMetric"],.stApp div[data-testid="stDataFrame"]{
  background:var(--so-surface); border-color:var(--so-border);
}
.stApp .stButton>button,.stApp [data-testid="stFormSubmitButton"] button{
  border-radius:var(--so-radius-control); font-weight:600;
}
.stApp [data-testid="stBaseButton-primary"],
.stApp .stButton>button[kind="primary"],
.stApp [data-testid="stFormSubmitButton"] button{
  color:white !important; background:var(--so-brand) !important;
  border-color:var(--so-brand) !important; box-shadow:none !important;
}
.stApp [data-testid="stBaseButton-primary"]:hover,
.stApp .stButton>button[kind="primary"]:hover,
.stApp [data-testid="stFormSubmitButton"] button:hover{
  color:white !important; background:var(--so-violet) !important;
  border-color:var(--so-violet) !important;
}
.stApp [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:not(:disabled) :is(p,span),
.stApp [data-testid="stMainBlockContainer"] .stButton>button[kind="primary"]:not(:disabled) :is(p,span),
.stApp [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] button:not(:disabled) :is(p,span){
  color:#FFFFFF !important;
}
.stApp [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:disabled,
.stApp [data-testid="stMainBlockContainer"] .stButton>button[kind="primary"]:disabled,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] button:disabled{
  color:#7E7898 !important; background:#E9E7F3 !important;
  border-color:#D9D5E8 !important; opacity:1 !important;
  box-shadow:none !important; cursor:not-allowed !important;
}
.stApp [data-testid="stMainBlockContainer"] [data-testid="stBaseButton-primary"]:disabled :is(p,span),
.stApp [data-testid="stMainBlockContainer"] .stButton>button[kind="primary"]:disabled :is(p,span),
.stApp [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] button:disabled :is(p,span){
  color:#7E7898 !important;
}
.stApp div[data-baseweb="input"],.stApp div[data-baseweb="select"]>div,
.stApp textarea{ background:var(--so-surface); border-color:var(--so-border); }
.stApp div[data-baseweb="input"]:focus-within,
.stApp div[data-baseweb="select"]>div:focus-within,.stApp textarea:focus{
  border-color:var(--so-violet) !important; box-shadow:0 0 0 3px rgba(124,58,237,.14) !important;
}
button:focus-visible,a:focus-visible,input:focus-visible,[role="button"]:focus-visible{
  outline-color:var(--so-periwinkle) !important;
}

.stApp:has(.tango-login-shell){
  background:radial-gradient(circle at 12% 12%,rgba(124,58,237,.10),transparent 30rem),
    linear-gradient(135deg,var(--so-background) 0%,var(--so-surface) 55%,#F0F5FF 100%);
}
.tango-login-brand{ display:flex; align-items:center; gap:.8rem; color:var(--so-brand); margin-bottom:4.8rem; }
.tango-login-brand img{ display:block; width:4.25rem; height:4.25rem; object-fit:contain; }
.streamoperiq-wordmark{ font-size:2.25rem; line-height:1; font-weight:750; letter-spacing:-.055em; white-space:nowrap; }
.streamoperiq-wordmark .gradient-letter{
  color:transparent; background:var(--so-ai-gradient); background-clip:text; -webkit-background-clip:text;
}
.tango-login-eyebrow{ color:var(--so-violet); }
.tango-login-hero h1,.tango-login-panel-head h2{ color:var(--so-brand); }
.tango-login-hero p,.tango-login-panel-head p,.tango-login-foot{ color:var(--so-text-muted); }
.tango-login-proof{ color:var(--so-text); }
.tango-login-proof span::before{ color:var(--so-violet); background:#F1EDFF; }
.stApp:has(.tango-login-shell) div[data-testid="stColumn"]:has(.tango-login-panel-head){
  background:rgba(255,255,255,.96); border-color:var(--so-border);
  box-shadow:0 24px 70px rgba(33,26,74,.10),0 3px 12px rgba(17,24,39,.04);
}
.stApp:has(.tango-login-shell) div[data-testid="stTextInput"] label{ color:var(--so-text); }
.stApp:has(.tango-login-shell) div[data-baseweb="input"]{
  background:var(--so-surface); border-color:var(--so-border); border-radius:var(--so-radius-control);
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"] button{
  color:var(--so-text-muted) !important; border-left-color:var(--so-border) !important;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"] button:hover{
  color:var(--so-violet) !important; background:#F5F2FF !important;
}
.stApp:has(.tango-login-shell) [data-testid="InputInstructions"]{
  display:none !important;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"]{
  overflow:hidden;
}
.stApp:has(.tango-login-shell) div[data-baseweb="input"] button{
  align-self:stretch !important; flex:0 0 3rem !important;
  width:3rem !important; min-width:3rem !important; min-height:100% !important;
  display:inline-flex !important; align-items:center !important; justify-content:center !important;
}
.stApp:has(.tango-login-shell) [data-testid="stFormSubmitButton"] button:disabled{
  color:#7E7898 !important; background:#E9E7F3 !important;
  border-color:#D9D5E8 !important; opacity:1 !important;
  box-shadow:none !important; cursor:not-allowed !important;
}
.stApp:has(.tango-login-shell) [data-testid="stFormSubmitButton"] button:not(:disabled){
  color:#FFFFFF !important; background:var(--so-brand) !important;
  border-color:var(--so-brand) !important;
}

/* Password controls: consistent visibility toggle and no overlapping
   Enter-to-submit helper text in login, popovers, or administration forms. */
.stApp div[data-testid="stTextInput"]:has(input[type="password"]) [data-testid="InputInstructions"]{
  display:none !important;
}
.stApp div[data-baseweb="input"]:has(input[type="password"]){
  overflow:hidden;
}
.stApp div[data-baseweb="input"]:has(input[type="password"]) button{
  align-self:stretch !important; flex:0 0 3rem !important;
  width:3rem !important; min-width:3rem !important; min-height:100% !important;
  margin:0 !important; padding:0 !important;
  display:inline-flex !important; align-items:center !important; justify-content:center !important;
  color:var(--so-text-muted) !important; background:var(--so-surface) !important;
  border:0 !important; border-left:1px solid var(--so-border) !important;
  border-radius:0 !important; box-shadow:none !important;
}
.stApp div[data-baseweb="input"]:has(input[type="password"]) button:hover{
  color:var(--so-violet) !important; background:#F5F2FF !important;
}

.stApp:has(.platform-admin-page),.stApp:has(.owner-overview-page){ background:var(--so-background); }
.stApp:has(.platform-admin-page) section[data-testid="stSidebar"],
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"]{
  background:var(--so-surface); border-color:var(--so-border);
}
.admin-kicker,.overview-eyebrow{ color:var(--so-violet); }
.admin-hero h1,.overview-hero h1,.admin-section-head h2,.overview-section h2,
.command-grid-title h2{ color:var(--so-brand); }
.admin-hero p,.overview-hero p,.admin-section-head p,.overview-section p,
.command-grid-title p{ color:var(--so-text-muted); }
.admin-secure-pill{ color:var(--so-brand); background:#F1EDFF; border-color:#DDD4FE; }
.agency-status.active,.sidebar-ok-badge{ color:var(--so-success); background:#ECFDF5; border-color:#A7F3D0; }
.agency-status.disabled,.sidebar-due-badge{ color:var(--so-warning); background:#FFF7ED; border-color:#FED7AA; }
.empty-agencies{ color:var(--so-text-muted); }
.empty-agencies-icon,.overview-kpi-icon{ color:var(--so-violet); background:#F1EDFF; }
.overview-period-pill,.overview-kpi,.insight-card,.command-score,.command-alert,
.owner-workspace{ background:var(--so-surface); border-color:var(--so-border); }
.overview-kpi-label,.overview-kpi-note,.insight-label,.insight-caption,
.command-score-copy p,.command-alert-copy,.command-footnote{ color:var(--so-text-muted); }
.overview-kpi-value,.insight-value,.command-score-value,.command-score-copy h3,
.command-alert-value,.owner-workspace-name,.sidebar-profile-name{ color:var(--so-brand); }
.overview-kpi-note.up{ color:var(--so-success); }.overview-kpi-note.down{ color:var(--so-danger); }
.command-alert-label{ color:var(--so-warning); }
.command-score-ring{ background:conic-gradient(var(--so-violet) calc(var(--score)*1%),#ECEEFA 0); }
.command-progress{ background:#ECEEFA; }
.command-progress span{ background:var(--so-ai-gradient); }
.command-table-badge{ color:var(--so-cobalt); background:#EFF6FF; }

.owner-sidebar-brand{ color:var(--so-brand); }
.owner-sidebar-brand img{ width:2.15rem; height:2.15rem; border-radius:.65rem; object-fit:cover; }
.owner-workspace-avatar{ color:var(--so-brand); background:#F1EDFF; }
.owner-workspace-role,.sidebar-profile-role,.sidebar-group-head{ color:var(--so-text-muted); }
.owner-workspace-business{ color:var(--so-text-muted); font-size:.72rem; margin-top:.12rem; }
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button{ color:var(--so-text); }
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button:hover{
  color:var(--so-brand); background:#F5F2FF; border-color:#DDD4FE;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] .stButton>button[kind="primary"],
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  color:var(--so-brand) !important; background:#F1EDFF !important; border-color:#DDD4FE !important;
  box-shadow:inset 3px 0 0 var(--so-violet) !important;
}
.stApp:has(.owner-sidebar-marker) section[data-testid="stSidebar"] details summary{ color:var(--so-brand); }
.kpi-card{ background:var(--so-surface); border-color:var(--so-border); }
.kpi-card:hover{ box-shadow:0 6px 20px rgba(33,26,74,.07); }
.kpi-card.dark{ background:var(--so-brand); }
section[data-testid="stSidebar"] .stButton>button:hover{ background:#F5F2FF; border-color:var(--so-border); }
section[data-testid="stSidebar"] .stButton>button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  background:#F1EDFF !important; color:var(--so-brand) !important;
  border-color:#DDD4FE !important;
}

@media (max-width:800px){
  .tango-login-brand img{ width:3.5rem; height:3.5rem; }
  .streamoperiq-wordmark{ font-size:1.85rem; }
  .tango-login-brand{ margin-bottom:2rem; }
  .owner-sidebar-brand img{ width:1.9rem; height:1.9rem; }
}

/* Shared dashboard alignment and density */
.stApp [data-testid="stMainBlockContainer"]{ max-width:1320px; padding:2rem 1.5rem 3rem; }
.stApp [data-testid="stMainBlockContainer"] > div{ width:100%; }
.stApp [data-testid="stMainBlockContainer"] h1{
  margin:0 0 .45rem; font-size:clamp(2rem,3vw,2.45rem); line-height:1.12;
}
.stApp [data-testid="stMainBlockContainer"] h2{ margin:0 0 .4rem; line-height:1.25; }
.stApp [data-testid="stMainBlockContainer"] h3,
.stApp [data-testid="stMainBlockContainer"] h4,
.stApp [data-testid="stMainBlockContainer"] h5,
.stApp [data-testid="stMainBlockContainer"] h6{ margin-top:.25rem; margin-bottom:.35rem; line-height:1.3; }
.stApp [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"]{ line-height:1.45; }
.stApp [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"]{ gap:.8rem; }
.overview-hero{ margin-bottom:1.15rem; align-items:flex-start; }
.overview-section,.command-grid-title{ margin-top:1.35rem; margin-bottom:.7rem; }
.stApp [data-testid="stHorizontalBlock"]{ align-items:stretch; gap:.85rem; }
@media (min-width:901px){
  .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{ min-width:0; }
  .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > [data-testid="stVerticalBlock"]{ height:100%; }
}
.stApp div[data-testid="stMetric"]{
  height:100%; min-height:112px; padding:1rem 1.05rem;
  border:1px solid var(--so-border); border-radius:var(--so-radius-card);
}
.stApp div[data-testid="stMetric"] [data-testid="stMetricLabel"]{ min-height:1.5rem; line-height:1.3; }
.stApp div[data-testid="stMetric"] [data-testid="stMetricValue"]{ line-height:1.1; }
.stApp div[data-testid="stVerticalBlockBorderWrapper"]{
  height:100%; border-color:var(--so-border); border-radius:var(--so-radius-card);
}
.stApp [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"]{
  min-height:1.5rem; display:flex; align-items:flex-end; margin-bottom:.25rem;
}
.stApp [data-testid="stMainBlockContainer"] div[data-baseweb="input"],
.stApp [data-testid="stMainBlockContainer"] div[data-baseweb="select"] > div,
.stApp [data-testid="stMainBlockContainer"] textarea{
  min-height:2.75rem;
}
.stApp [data-testid="stMainBlockContainer"] .stButton > button,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stDownloadButton"] button,
.stApp [data-testid="stMainBlockContainer"] [data-testid="stPopover"] button{
  min-height:2.75rem;
  display:inline-flex; align-items:center; justify-content:center; line-height:1.2;
}
.stApp [data-testid="stMainBlockContainer"] div[data-testid="stForm"] [data-testid="stHorizontalBlock"]{
  align-items:flex-end;
}
.stApp [data-testid="stMainBlockContainer"] [data-testid="stAlert"]{ margin:.25rem 0; border-radius:var(--so-radius-control); }
.stApp [data-testid="stMainBlockContainer"] [data-testid="stExpander"]{ border-color:var(--so-border); border-radius:var(--so-radius-control); }
.stApp [data-testid="stDataFrame"],.stApp [data-testid="stPlotlyChart"]{ width:100%; }
.stApp [data-testid="stPlotlyChart"] > div{ width:100% !important; }
.stApp [data-testid="stDataFrame"]{ overflow:hidden; border:1px solid var(--so-border); border-radius:var(--so-radius-control); }
.stApp [data-testid="stPlotlyChart"]{ overflow:hidden; border-radius:var(--so-radius-control); }
.stApp [data-testid="stMainBlockContainer"] hr{ margin:1rem 0; border-color:var(--so-border); }
.dashboard-section-nav{ margin:.2rem 0 .7rem; }
.stApp div[data-testid="stSegmentedControl"]{ margin:.2rem 0 .9rem; }
.stApp div[data-testid="stSegmentedControl"] [role="radiogroup"]{
  width:100%; padding:.28rem; background:var(--so-surface); border:1px solid var(--so-border);
  border-radius:.8rem; gap:.25rem;
}
.stApp div[data-testid="stSegmentedControl"] label{ flex:1; justify-content:center; min-height:2.55rem; }
.stApp div[data-testid="stSegmentedControl"] label:has(input:checked){
  color:var(--so-brand); background:#F1EDFF; border-radius:.6rem;
}

/* Broadcaster payouts */
.payout-calc-strip{
  display:flex; align-items:center; gap:.75rem; padding:.85rem 1rem; margin:.15rem 0 .2rem;
  color:var(--so-brand); background:#F5F2FF; border:1px solid #DDD4FE;
  border-radius:var(--so-radius-control); font-size:.84rem; line-height:1.5;
}
.payout-calc-strip svg{ flex:0 0 1.25rem; width:1.25rem; height:1.25rem; color:var(--so-violet); }
.payout-kpi{
  min-height:132px; height:100%; padding:1rem 1.05rem; background:var(--so-surface);
  border:1px solid var(--so-border); border-radius:var(--so-radius-card);
}
.payout-kpi-head{ display:flex; align-items:center; gap:.65rem; color:var(--so-text-muted); font-size:.76rem; font-weight:650; }
.payout-kpi-icon{ width:2rem; height:2rem; display:grid; place-items:center; color:var(--so-violet); background:#F1EDFF; border-radius:.65rem; }
.payout-kpi-icon svg{ width:1.05rem; height:1.05rem; }
.payout-kpi-value{ margin-top:.85rem; color:var(--so-brand); font-size:1.7rem; line-height:1; font-weight:760; letter-spacing:-.035em; font-variant-numeric:tabular-nums; }
.payout-kpi-note{ margin-top:.55rem; color:var(--so-text-muted); font-size:.72rem; }
.payout-section-head{ margin:.55rem 0 .15rem; }
.payout-section-head h2{ margin:0 0 .25rem !important; font-size:1.2rem; }
.payout-section-head p{ margin:0; color:var(--so-text-muted); font-size:.82rem; }
.payout-status-key{ display:flex; flex-wrap:wrap; gap:.45rem; margin:.15rem 0 .45rem; }
.payout-status-key span{ padding:.25rem .55rem; border:1px solid var(--so-border); border-radius:999px; font-size:.7rem; color:var(--so-text-muted); background:var(--so-surface); }
.payout-status-key .paid{ color:var(--so-success); background:#ECFDF5; border-color:#A7F3D0; }
.payout-status-key .missing{ color:var(--so-warning); background:#FFF7ED; border-color:#FED7AA; }
@media (max-width:900px){
  .stApp [data-testid="stMainBlockContainer"]{ padding:1.25rem 1rem 2.5rem; }
  .stApp [data-testid="stMainBlockContainer"] h1{ font-size:1.9rem; }
  .overview-hero{ gap:.8rem; }
  .overview-period-pill{ display:none; }
  .stApp [data-testid="stHorizontalBlock"]{ flex-wrap:wrap; }
  .stApp [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 100% !important; width:100% !important;
  }
  .stApp div[data-testid="stSegmentedControl"] [role="radiogroup"]{ overflow-x:auto; justify-content:flex-start; }
  .stApp div[data-testid="stSegmentedControl"] label{ flex:0 0 auto; padding-inline:.75rem; }
  .payout-kpi{ min-height:116px; }
}
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


PAYOUT_ICONS = {
    "diamond": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m3 8 4-5h10l4 5-9 13L3 8Z"/><path d="m3 8 9 4 9-4M7 3l5 9 5-9M12 12v9"/></svg>',
    "wallet": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 6.5h14a2 2 0 0 1 2 2v10H4a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2h12"/><path d="M15 11h7v4h-7a2 2 0 1 1 0-4Z"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-7M22 20V7"/><path d="M2 20h22"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "calculator": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h2M14 11h2M8 16h2M14 16h2"/></svg>',
}


def payout_kpi_card(label, value, icon, note):
    st.markdown(
        f'<div class="payout-kpi"><div class="payout-kpi-head">'
        f'<span class="payout-kpi-icon">{PAYOUT_ICONS[icon]}</span>{html.escape(label)}</div>'
        f'<div class="payout-kpi-value">{html.escape(value)}</div>'
        f'<div class="payout-kpi-note">{html.escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


TABLE_COLUMN_CONFIG = {
    "broadcaster_name": st.column_config.TextColumn("Broadcaster", width="medium"),
    "sub_agency": st.column_config.TextColumn("Sub-Agency", width="medium"),
    "status": st.column_config.TextColumn("Status", width="small"),
    "streaming_days": st.column_config.NumberColumn("Days streamed", format="%d", width="small"),
    "streaming_hours": st.column_config.NumberColumn("Hours streamed", format="%.1f", width="small"),
    "diamonds_redeemed": st.column_config.NumberColumn("Diamonds redeemed", format="localized", width="small"),
    "diamonds_earned": st.column_config.NumberColumn("Diamonds earned", format="localized", width="small"),
    "usd_earned": st.column_config.NumberColumn("Creator revenue", format="$%.2f", width="small"),
    "usd_redeemed": st.column_config.NumberColumn("Redeemed value", format="$%.2f", width="small"),
    "my_earnings_usd": st.column_config.NumberColumn("Agency revenue", format="$%.2f", width="small"),
    "diamonds_per_day": st.column_config.NumberColumn("Diamonds per day", format="localized", width="small"),
    "growth_pct": st.column_config.NumberColumn("Growth vs previous month", format="%.1f%%", width="medium"),
    "is_new": st.column_config.CheckboxColumn("New broadcaster", width="small"),
    "profile_url": st.column_config.LinkColumn("Web profile", display_text="Open profile", width="medium"),
}


def table_column_config(columns):
    """Return consistent, user-facing labels without renaming stored data."""
    return {column: TABLE_COLUMN_CONFIG[column] for column in columns if column in TABLE_COLUMN_CONFIG}


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


def generate_secure_password(length: int = 16) -> str:
    """Generate a password that always satisfies the StreamOperiq policy."""
    characters = [
        pysecrets.choice(string.ascii_lowercase),
        pysecrets.choice(string.ascii_uppercase),
        pysecrets.choice(string.digits),
        pysecrets.choice("!@#$%^&*()-_=+"),
    ]
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    characters.extend(pysecrets.choice(alphabet) for _ in range(max(length, 12) - len(characters)))
    pysecrets.SystemRandom().shuffle(characters)
    return "".join(characters)


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


@st.cache_data(ttl=30, show_spinner=False)
def load_agency_counts_by_business():
    return store.get_agency_counts_by_business()


@st.cache_data(ttl=60, show_spinner=False)
def load_database_role_posture():
    # Underlying role privileges only ever change via a manual DB admin
    # action, so a short cache here is a safe trade for removing this
    # round trip from every single Businesses-page rerun.
    return store.get_database_role_posture()


@st.cache_data(ttl=30, show_spinner=False)
def load_all_memberships_df():
    return store.get_all_memberships()


@st.cache_data(ttl=30, show_spinner=False)
def load_ai_features_enabled(biz_id):
    """Phase 4b, first slice: the health-score/at-risk/retention insights
    are real, already-built statistical functions (utils.py) that used to
    show unconditionally regardless of plan. Section 04: Essential = off,
    Growth and above = on (basic/advanced/custom all count as enabled here -
    the specific AI tier distinction between them is future scope, not this
    slice)."""
    value = store.has_feature(biz_id, "ai_features")
    return value not in (None, "off")


@st.cache_data(ttl=30, show_spinner=False)
def load_broadcaster_dashboard_access(biz_id):
    """Phase 4b, second slice: the Statistics ("Broadcaster Dashboard") page
    is a whole-page gate, not per-panel like ai_features. Section 04:
    Essential = off, Growth/Pioneer = readonly, Scale = full, Network =
    full_custom. This slice only distinguishes off vs not-off - the
    readonly/full/full_custom distinction is future scope."""
    value = store.has_feature(biz_id, "broadcaster_dashboard_access")
    return value if value not in (None, "off") else "off"


@st.cache_data(ttl=30, show_spinner=False)
def load_pdf_export_enabled(biz_id):
    """Phase 4b, third slice: Section 04's `exports` feature has no `off`
    tier - every plan includes CSV ('csv'). The differentiator is PDF
    ('csv_pdf', Growth+) and scheduled export ('csv_pdf_scheduled',
    Network only - the scheduling mechanism itself doesn't exist yet and
    is out of scope for this slice, same as the dashboard-access tier
    split). This only checks whether PDF is available at all."""
    value = store.has_feature(biz_id, "exports")
    return value in ("csv_pdf", "csv_pdf_scheduled")


@st.cache_data(ttl=15, show_spinner=False)
def load_subscription(biz_id):
    # Pre-existing bug fix: this must be defined before the Phase 7
    # restricted-state block below uses it — that block was moved earlier
    # in the file by commit fc05f1f without moving this definition with
    # it, causing a NameError on every page load for any business_id user
    # (everyone except Platform Admin) on both dev and prod.
    return store.get_subscription(biz_id)


def poster_studio_enabled() -> bool:
    """App-level feature flag (Section 54), not tied to a tenant's plan —
    AI Poster Studio is a new, isolated feature rather than a billed
    entitlement yet. Defaults on; set [features] ai_poster_studio = false
    in secrets to disable without a deploy."""
    try:
        return bool(st.secrets.get("features", {}).get("ai_poster_studio", True))
    except Exception:
        return True


@st.cache_data(ttl=30, show_spinner=False)
def build_credentials():
    # Perf fix: stauth.Hasher().hash() runs bcrypt, which is deliberately
    # slow (~100s of ms). This function used to run uncached on every single
    # script rerun for every user interaction - caching it means the
    # bootstrap password is only re-hashed when this cache actually expires
    # or is cleared, not on every click. refresh_caches() below clears this
    # alongside load_all_users_df/load_businesses_df so a newly created or
    # edited login can sign in immediately rather than waiting out the TTL.
    boot = st.secrets["bootstrap_admin"]
    boot_hash = stauth.Hasher().hash(boot["password"])
    boot_username = str(boot["username"]).strip().lower()
    creds = {"usernames": {
        boot_username: {"name": boot["name"], "email": boot_username, "password": boot_hash}
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
            # A tenant login must never replace or impersonate the bootstrap
            # Platform Admin identity, including case-only email variations.
            normalized_username = str(row["username"]).strip().lower()
            if normalized_username == boot_username:
                continue
            # A copied or newly provisioned Dev account may intentionally have
            # no password until the Platform Admin assigns one. Never pass a
            # null or malformed value to bcrypt: the authentication library
            # otherwise raises an exception instead of rejecting the login.
            password_hash = row.get("password_hash")
            if not isinstance(password_hash, str) or not re.fullmatch(
                r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", password_hash.strip()
            ):
                continue
            creds["usernames"][normalized_username] = {
                "name": row["name"], "email": normalized_username,
                "password": password_hash.strip(),
            }
    return creds, boot_username


credentials, bootstrap_username = build_credentials()


def is_bootstrap_identity(value: str) -> bool:
    """Return True when a tenant login collides with the reserved admin identity."""
    return bool(value) and value.strip().lower() == str(bootstrap_username).strip().lower()
authenticator = stauth.Authenticate(
    credentials,
    st.secrets["cookie"]["name"],
    st.secrets["cookie"]["key"],
    min(max(int(st.secrets["cookie"].get("expiry_days", 7)), 1), 7),
    auto_hash=False,
)

# Keep the authentication mechanism intact while presenting it in a branded,
# responsive shell. A rerun removes the shell immediately after cookie/login
# authentication so authenticated pages never inherit login-only styling.
was_authenticated = st.session_state.get("authentication_status") is True
if not was_authenticated:
    # Make the next successful sign-in a fresh identity transition even when
    # the same account signs out and back in within one browser tab.
    st.session_state.pop("_navigation_username", None)
    st.markdown('<div class="tango-login-shell"></div>', unsafe_allow_html=True)
    hero_col, login_col = st.columns([1.35, 0.85], gap="large", vertical_alignment="center")
    with hero_col:
        st.markdown(f"""
        <div class="tango-login-hero">
          <div class="tango-login-brand">
            <img src="{BRAND_ICON_URI}" alt="">
            <div class="streamoperiq-wordmark"><span class="gradient-letter">S</span>treamOperi<span class="gradient-letter">q</span></div>
          </div>
          <div class="tango-login-eyebrow">Streaming Operations + Intelligence</div>
          <h1>Intelligence behind every creator operation.</h1>
          <p>A multi-platform operations and performance intelligence platform
          for creator agencies and live-streaming networks.</p>
          <div class="tango-login-proof">
            <span>Multi-platform operations</span><span>Secure reporting</span><span>Performance intelligence</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with login_col:
        st.markdown("""
        <div class="tango-login-panel-head">
          <h2>Welcome back</h2>
          <p>Sign in to continue to your StreamOperiq workspace.</p>
        </div>
        """, unsafe_allow_html=True)
        authenticator.login(location="main", fields={
            "Form name": "Sign in",
            "Username": "Email address",
            "Password": "Password",
            "Login": "Sign in",
        })
        st.markdown('<div class="tango-login-foot">Protected access · StreamOperiq</div>',
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
username = str(st.session_state.get("username", "") or "").strip().lower()


@st.cache_data(ttl=15, show_spinner=False)
def load_profile(uname):
    return store.get_profile(uname)


_profile = load_profile(username)
if _profile and _profile.get("display_name"):
    display_name = _profile["display_name"]
avatar_b64 = _profile.get("avatar_base64") if _profile else None


def current_user_context():
    """Returns (role, business_id, sub_agency, profile_url).

    profile_url is set only for role='broadcaster' - it scopes a Broadcaster
    login to exactly one profile_url instead of a whole roster the way
    sub_agency scopes a Recruiter. None for every other role.

    Resolves through `memberships` first — the authoritative source added so
    a login is no longer hardwired to a single business_id/role pair on its
    `users` row (SaaS Phase 2). Falls back to reading `users` directly when
    this login has zero active membership rows (expected only for an account
    that predates scripts/backfill_memberships.py), and also when the
    `memberships` query itself fails outright — e.g. code deployed before
    scripts/run_migrations.py has created the table, or before
    database/restricted_role_setup.sql has granted it. Either way this is a
    zero-downtime safety net for deploy ordering, not a normal or permanent
    path.

    Also enforces `memberships.expires_at` — NULL for every normal role
    (never expires), set only for a time-boxed grant like Trial Viewer
    (Section 15 of the SaaS blueprint). An expired row is treated exactly
    like an inactive one: excluded here, which surfaces as the same
    "session no longer valid" message every other denied login gets. There
    is deliberately no separate "your trial has ended" message — that would
    tell an expired viewer their access was time-limited rather than simply
    revoked, which isn't information worth giving away.
    """
    if username == bootstrap_username:
        return "platform_admin", None, None, None

    businesses_df = load_businesses_df()
    active_business_ids = set(
        businesses_df[businesses_df["status"] == "Active"]["business_id"]
    ) if not businesses_df.empty else set()

    try:
        memberships_df = load_all_memberships_df()
    except Exception:
        memberships_df = pd.DataFrame()
    if not memberships_df.empty:
        normalized_member_usernames = memberships_df["username"].astype(str).str.strip().str.lower()
        not_expired = (
            memberships_df["expires_at"].isna()
            | (memberships_df["expires_at"] > dt.datetime.utcnow())
        )
        member_rows = memberships_df[
            (normalized_member_usernames == username)
            & (memberships_df["status"] == "Active")
            & (memberships_df["business_id"].isin(active_business_ids))
            & not_expired
        ]
        if not member_rows.empty:
            # A login holds exactly one active membership today; switching
            # between multiple is future scope (not built), so the most
            # recently created row is simply the default.
            r = member_rows.sort_values("created_at", ascending=False).iloc[0]
            if r["role"] not in ("owner", "agency_manager", "sub_agency", "auditor", "trial_viewer", "broadcaster"):
                return None, None, None, None
            return (
                r["role"], r["business_id"],
                (r["sub_agency"] if r["role"] == "sub_agency" else None),
                (r["profile_url"] if r["role"] == "broadcaster" else None),
            )

    # Broadcaster logins are always created directly in memberships (Phase
    # 3b onward) and never predate scripts/backfill_memberships.py, so this
    # fallback - which reads the legacy users table, with no profile_url
    # column at all - can never resolve one. Not a gap: nothing broadcaster
    # ever needs this path.
    users_df = load_all_users_df()
    if users_df.empty:
        return None, None, None, None
    normalized_usernames = users_df["username"].astype(str).str.strip().str.lower()
    row = users_df[normalized_usernames == username]
    if row.empty:
        return None, None, None, None
    r = row.iloc[0]
    if r["role"] not in ("owner", "agency_manager", "sub_agency", "auditor") or r["status"] != "Active":
        return None, None, None, None
    if r["business_id"] not in active_business_ids:
        return None, None, None, None
    return r["role"], r["business_id"], (r["sub_agency"] if r["role"] == "sub_agency" else None), None


user_role, user_business_id, user_agency, user_profile_url = current_user_context()
if user_role is None:
    st.error("This login session is no longer valid or does not have an active StreamOperiq role.")
    st.warning("For security, no platform or agency data has been loaded. Sign out, then sign in with an active account.")
    authenticator.logout("Sign out and return to login", "main")
    st.stop()
is_platform_admin = user_role == "platform_admin"
is_owner = user_role == "owner"
is_manager = user_role == "agency_manager"
is_sub_agency = user_role == "sub_agency"
is_auditor = user_role == "auditor"
is_trial_viewer = user_role == "trial_viewer"
is_broadcaster = user_role == "broadcaster"
# Agency Manager sees everything Owner sees except billing/plan (not built yet)
# and a handful of Owner-exclusive actions (Section 03 of the SaaS blueprint):
# creating sub-agencies, editing commission rates, payouts, and data archival.
# Used specifically for pages/actions Manager can DO but Auditor/Trial Viewer
# (zero write rights) cannot - Assign, Upload, User Access.
is_owner_or_manager = is_owner or is_manager
# Auditor and Trial Viewer both see the same full-tenant view as Owner/Manager
# on every page that is pure viewing (dashboard, Statistics, Broadcasters,
# BroadcasterDetail) - just never anything with a write action. Broader than
# is_owner_or_manager on purpose: use this one, not that one, for view-only
# "full tenant" checks.
can_view_full_tenant = is_owner or is_manager or is_auditor or is_trial_viewer
# Trial Viewer is read-only like Auditor, but additionally has no export at
# all (Section 03/15) - narrower than Auditor on purpose. Gates every
# st.download_button the app offers.
can_export = not is_trial_viewer
if is_trial_viewer:
    # st.dataframe() has its own built-in toolbar (search/download/fullscreen
    # icons) independent of the explicit st.download_button calls gated by
    # can_export above - without this, Trial Viewer could still export via
    # that icon regardless. Hides it globally for this session only.
    # Targets both toolbar test-id variants seen across recent Streamlit
    # versions; verify visually in dev that the download icon is actually
    # gone, not just assumed gone from this selector.
    st.markdown(
        '<style>[data-testid="stElementToolbar"], '
        '[data-testid="stDataFrameToolbar"] { display: none !important; }</style>',
        unsafe_allow_html=True,
    )
business_id = user_business_id

# Phase 7: subscriptions.status is advanced by an external scheduled job
# (scripts/run_lifecycle_checks.py), not by the app itself - this banner
# just reads whatever that job last wrote and shows it, on every page, to
# everyone logged into this tenant.
#
# Phase 7 follow-up (restricted-state enforcement): is_restricted gates
# exactly the four actions Section 07 names as blocked while restricted -
# create (Sub-Agency), invite (Create User), upload (CSV), export
# (CSV/PDF) - decided narrowly on purpose (user, 2026-08-22): other write
# actions (assign broadcasters, mark payouts paid, edit commission rates,
# archive/clear periods, disable/enable/reset a user's password) aren't
# named in the spec and stay unblocked, since some of them (like
# disabling a compromised login) are arguably security-relevant
# regardless of billing status.
is_restricted = False
if business_id:
    _tenant_subscription = load_subscription(business_id)
    if _tenant_subscription is not None:
        if _tenant_subscription["status"] == "grace":
            st.warning(
                f"Payment overdue since {_tenant_subscription['current_period_end']}. "
                "Please arrange payment soon to avoid a move to restricted access.",
                icon="⚠️",
            )
        elif _tenant_subscription["status"] == "restricted":
            is_restricted = True
            st.error(
                f"This account is marked restricted due to non-payment "
                f"(since {_tenant_subscription['current_period_end']}). "
                "Creating Sub-Agencies or users, uploading reports, and "
                "exporting data are unavailable until payment is recorded. "
                "Contact StreamOperiq to restore full access.",
                icon="🔒",
            )
can_export = can_export and not is_restricted

login_audit_key = f"_login_audited_{username}"
if not st.session_state.get(login_audit_key):
    store.log_security_event(
        "login_success", username, user_role, business_id,
        "account", username,
    )
    st.session_state[login_audit_key] = True

business_name = ""
if business_id:
    biz_row = load_businesses_df()
    biz_row = biz_row[biz_row["business_id"] == business_id]
    business_name = biz_row.iloc[0]["business_name"] if not biz_row.empty else ""

default_page = "Businesses" if is_platform_admin else "BroadcasterDetail" if is_broadcaster else "Admin"
allowed_pages_by_role = {
    "platform_admin": {"Businesses", "MyProfile"},
    "owner": {
        "Admin", "Statistics", "Broadcasters", "BroadcasterDetail", "Assign",
        "SubAgencies", "CreateAgency", "UploadMonthly", "UploadDaily",
        "UserAccess", "DataManagement", "MyProfile", "Payouts", "PosterStudio",
        "RewardOverview", "RewardPlans", "RecruiterRewards",
    },
    # Everything Owner has except SubAgencies (has a live commission-rate edit
    # control Manager's permission set excludes — kept Owner-only rather than
    # risk a leak), CreateAgency, DataManagement, and Payouts — none of which
    # are in agency_manager's permission set (Section 03/store.py seed data).
    "agency_manager": {
        "Admin", "Statistics", "Broadcasters", "BroadcasterDetail", "Assign",
        "UploadMonthly", "UploadDaily", "UserAccess", "MyProfile", "PosterStudio",
    },
    # Read-only, full-tenant view (Section 03): no Assign/Upload/UserAccess -
    # nothing Auditor can act on, only look at. AuditLog is Auditor's one page
    # Owner/Manager don't have a dedicated nav link for (they see the same
    # data embedded in Data Management instead).
    "auditor": {"Admin", "Statistics", "Broadcasters", "BroadcasterDetail", "AuditLog", "MyProfile"},
    # Same visual surface as Owner (Section 15) - dashboards and broadcaster
    # data - minus AuditLog (not part of Trial Viewer's scope) and with every
    # export gated off separately via can_export, not by page access.
    "trial_viewer": {"Admin", "Statistics", "Broadcasters", "BroadcasterDetail", "MyProfile"},
    "sub_agency": {"Admin", "Broadcasters", "BroadcasterDetail", "UploadMonthly", "MyProfile",
                   "RecruiterRewards"},
    # Own performance only (Section 03) - no roster, no dashboard, nothing
    # else. BroadcasterDetail is locked to their own profile_url (see that
    # page's own handling below), not a page they navigate to freely.
    "broadcaster": {"BroadcasterDetail", "MyProfile"},
}

# Reset navigation when the authenticated identity changes. This prevents a
# sub-agency login from inheriting an owner-only page after sign-out/sign-in.
if st.session_state.get("_navigation_username") != username:
    # A Markdown heading clicked in a previous session can leave its anchor in
    # the browser URL. Sending a native page-info update rebuilds the URL from
    # the app's query string and clears that stale fragment in the top window.
    st.query_params.clear()
    st.session_state.page = default_page
    # A Broadcaster always views their own profile_url, never a chosen one -
    # every other role starts with nothing selected until they pick one.
    st.session_state.selected_profile_url = user_profile_url if is_broadcaster else None
    st.session_state._navigation_username = username
elif st.session_state.get("page") not in allowed_pages_by_role[user_role]:
    st.session_state.page = default_page
    st.session_state.selected_profile_url = None

# Reflects the logged-in agency in the URL (e.g. ?agency=north-talent) so a
# bookmarked/shared link shows which tenant it's for. Cosmetic only - this
# is always DERIVED from the already-authenticated business_id, never read
# back to decide which tenant's data loads, so it can't be used to bypass
# tenant isolation by editing the URL. Streamlit Cloud's shared single URL
# doesn't support real per-tenant subdomains/paths (e.g. streamoperiq.com/
# north-talent) without a custom domain + reverse proxy in front, which is
# a separate infrastructure project, not a code change.
if business_id and business_name:
    _agency_slug = re.sub(r"[^a-z0-9]+", "-", business_name.strip().lower()).strip("-") or "agency"
    if st.query_params.get("agency") != _agency_slug:
        st.query_params["agency"] = _agency_slug
elif "agency" in st.query_params:
    del st.query_params["agency"]

if "selected_profile_url" not in st.session_state:
    st.session_state.selected_profile_url = None


def nav_button(label, page_key, icon=None):
    # Bug caught in Phase 3b dev testing: the sidebar's outer gate covers both
    # Owner and Manager, but not every button inside it is in every role's
    # allowed_pages_by_role set. Rather than gate each call site individually
    # (easy to miss one), nav_button itself won't render a link the current
    # role can't actually use - the page-level redirect already blocked the
    # destination, this just stops offering a link that silently bounces back.
    if page_key not in allowed_pages_by_role.get(user_role, set()):
        return
    if st.button(label, width='stretch', icon=icon,
                 type="primary" if st.session_state.page == page_key else "secondary"):
        st.session_state.page = page_key
        st.rerun()


def dashboard_section_control(key, options):
    """Render compact in-page navigation and hide non-selected dashboard panels."""
    selected = st.segmented_control(
        "Dashboard section", options, default=options[0], key=key,
        label_visibility="collapsed", width="stretch",
    )
    selected = selected or options[0]
    hidden_selectors = [
        f".st-key-{key}_{option.lower().replace(' ', '_').replace('&', 'and')}"
        for option in options if option != selected
    ]
    if hidden_selectors:
        st.markdown(
            f"<style>{','.join(hidden_selectors)}{{display:none !important;}}</style>",
            unsafe_allow_html=True,
        )
    return selected


def dashboard_panel(key, section):
    """Create a keyed panel whose visibility is controlled by dashboard_section_control."""
    normalized = section.lower().replace(" ", "_").replace("&", "and")
    return st.container(key=f"{key}_{normalized}")


def render_sidebar_brand():
    st.markdown(f"""
    <div class="owner-sidebar-brand">
      <img src="{BRAND_ICON_URI}" alt="" aria-hidden="true"><span>StreamOperiq</span>
    </div>
    """, unsafe_allow_html=True)


with st.sidebar:
    if can_view_full_tenant:
        st.markdown('<div class="owner-sidebar-marker"></div>', unsafe_allow_html=True)
        render_sidebar_brand()
        owner_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "AO"
        safe_business_name = html.escape(str(business_name))
        safe_display_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{owner_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_display_name}</div>
            <div class="owner-workspace-business">{safe_business_name}</div>
            <div class="owner-workspace-role">Business Owner</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-group-head"><span>Dashboards</span></div>', unsafe_allow_html=True)
            nav_button("My Dashboard", "Admin", ":material/dashboard:")
            nav_button("Broadcaster Dashboard", "Statistics", ":material/monitoring:")
            nav_button("Recruiter Dashboard", "SubAgencies", ":material/hub:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-group-head"><span>Rewards</span></div>', unsafe_allow_html=True)
            nav_button("Reward Overview", "RewardOverview", ":material/summarize:")
            nav_button("Broadcaster Rewards", "Payouts", ":material/redeem:")
            nav_button("Recruiter Rewards", "RecruiterRewards", ":material/military_tech:")
            nav_button("Reward Plans", "RewardPlans", ":material/rule_folder:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-group-head"><span>Manage</span></div>', unsafe_allow_html=True)
            nav_button("Broadcasters", "Broadcasters", ":material/groups:")
            nav_button("Assign Broadcasters", "Assign", ":material/person_add:")
            nav_button("Create Sub-Agency", "CreateAgency", ":material/domain_add:")

        if poster_studio_enabled():
            with st.container(border=True):
                st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div class="sidebar-group-head"><span>Creative</span></div>', unsafe_allow_html=True)
                nav_button("AI Poster Studio", "PosterStudio", ":material/palette:")

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
            nav_button("Monthly Report", "UploadMonthly", ":material/upload_file:")
            nav_button("Daily Report", "UploadDaily", ":material/description:")

        admin_expanded = st.session_state.page in ("UserAccess", "DataManagement", "AuditLog")
        with st.expander("Administration", expanded=admin_expanded, icon=":material/admin_panel_settings:"):
            nav_button("User Access", "UserAccess", ":material/manage_accounts:")
            nav_button("Data Management", "DataManagement", ":material/database:")
            nav_button("Audit Log", "AuditLog", ":material/history:")

        nav_button("My Profile", "MyProfile", ":material/account_circle:")
        authenticator.logout("Sign Out", "sidebar")

    elif is_sub_agency:
        st.markdown('<div class="owner-sidebar-marker"></div>', unsafe_allow_html=True)
        render_sidebar_brand()
        sub_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "SA"
        safe_agency_name = html.escape(str(user_agency))
        safe_business_name = html.escape(str(business_name))
        safe_display_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{sub_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_display_name}</div>
            <div class="owner-workspace-business">{safe_agency_name}</div>
            <div class="owner-workspace-role">Sub-Agency · {safe_business_name}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        nav_button("Overview", "Admin", ":material/dashboard:")
        nav_button("My Broadcasters", "Broadcasters", ":material/groups:")

        with st.container(border=True):
            st.markdown('<div class="sidebar-group-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-group-head"><span>Rewards</span></div>', unsafe_allow_html=True)
            nav_button("My Rewards", "RecruiterRewards", ":material/military_tech:")

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
            nav_button("Upload Monthly Report", "UploadMonthly", ":material/upload_file:")

        nav_button("My Profile", "MyProfile", ":material/account_circle:")
        authenticator.logout("Sign Out", "sidebar")

    elif is_broadcaster:
        render_sidebar_brand()
        broadcaster_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "BC"
        safe_business_name = html.escape(str(business_name))
        safe_display_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{broadcaster_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_display_name}</div>
            <div class="owner-workspace-business">{safe_business_name}</div>
            <div class="owner-workspace-role">Broadcaster</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        nav_button("My Performance", "BroadcasterDetail", ":material/monitoring:")
        nav_button("My Profile", "MyProfile", ":material/account_circle:")
        authenticator.logout("Sign Out", "sidebar")

    else:
        render_sidebar_brand()
        st.caption("PLATFORM CONTROL")
        if business_name:
            st.caption(business_name)
        st.write("")

    if is_platform_admin:
        admin_initials = "".join(part[0].upper() for part in display_name.split()[:2]) or "PA"
        safe_admin_name = html.escape(str(display_name))
        st.markdown(f"""
        <div class="owner-workspace">
          <div class="owner-workspace-avatar">{admin_initials}</div>
          <div class="owner-workspace-copy">
            <div class="owner-workspace-name">{safe_admin_name}</div>
            <div class="owner-workspace-business">StreamOperiq</div>
            <div class="owner-workspace-role">Platform Administrator</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        nav_button("Platform Overview", "Businesses", ":material/admin_panel_settings:")
        st.write("")
        nav_button("My Profile", "MyProfile", ":material/account_circle:")
        authenticator.logout("Sign Out", "sidebar")

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


@st.cache_data(ttl=15, show_spinner=False)
def load_agency_details(biz_id):
    return store.get_agency_details(biz_id)


@st.cache_data(ttl=15, show_spinner=False)
def load_security_audit(biz_id, limit=200):
    return store.get_security_audit(biz_id, limit=limit)


@st.cache_data(ttl=30, show_spinner=False)
def load_recent_platform_activity(limit=8):
    return store.get_recent_platform_activity(limit)


@st.cache_data(ttl=30, show_spinner=False)
def load_business_users(biz_id):
    return store.get_users(biz_id)


@st.cache_data(ttl=30, show_spinner=False)
def load_business_memberships(biz_id):
    return store.get_business_memberships(biz_id)


@st.cache_data(ttl=60, show_spinner=False)
def load_plans():
    return store.get_plans()


@st.cache_data(ttl=15, show_spinner=False)
def load_billing_events(biz_id):
    return store.get_billing_events(biz_id)


INTERNAL_USER_ROLES = ("owner", "agency_manager", "auditor", "trial_viewer")


def check_membership_limit(business_id, new_role):
    """Phase 5, first slice: internal_user_limit and recruiter_logins are
    hard caps - a new membership is blocked outright if it would exceed
    the tenant's plan limit (Section 15), unlike broadcaster_limit which
    stays a soft, overage-priced cap (Section 04/08) not enforced here -
    see PHASE_LOG.md for the reasoning). Returns an error message string
    if blocked, None if the invite is allowed."""
    if new_role == "sub_agency":
        feature_key, counted_roles, label = "recruiter_logins", ("sub_agency",), "recruiter login"
    else:
        feature_key, counted_roles, label = "internal_user_limit", INTERNAL_USER_ROLES, "internal user"
    limit = store.has_feature(business_id, feature_key)
    if limit in (None, -1):
        return None
    memberships_df = load_business_memberships(business_id)
    current = int((
        memberships_df["role"].isin(counted_roles) & (memberships_df["status"] == "Active")
    ).sum())
    if current >= limit:
        return (
            f"This plan allows {limit} {label}{'s' if limit != 1 else ''} - you already have "
            f"{current}. Upgrade the plan or free up a seat before adding another."
        )
    return None


@st.cache_data(ttl=30, show_spinner=False)
def load_payout_rules(biz_id):
    return store.get_payout_rules(biz_id)


@st.cache_data(ttl=30, show_spinner=False)
def load_effective_payout_rules(biz_id, period):
    return store.get_effective_payout_rules(biz_id, period)


@st.cache_data(ttl=30, show_spinner=False)
def load_payout_statuses(biz_id, period):
    return store.get_payout_statuses(biz_id, period)


# ---------------- Reward Plan Management System loaders ----------------
# Fully additive - none of these touch broadcaster_payout_rules/status or
# agencies.commission_pct above. See store.py's "Reward Plan Management
# System" section for the schema and CRUD this UI calls into.

@st.cache_data(ttl=15, show_spinner=False)
def load_reward_plans(biz_id, recipient_type=None, status=None):
    return store.get_reward_plans(biz_id, recipient_type, status)


@st.cache_data(ttl=15, show_spinner=False)
def load_plan_versions(biz_id, plan_id):
    return store.get_plan_versions(biz_id, plan_id)


@st.cache_data(ttl=15, show_spinner=False)
def load_plan_milestones(biz_id, plan_version_id):
    return store.get_plan_milestones(biz_id, plan_version_id)


@st.cache_data(ttl=15, show_spinner=False)
def load_broadcaster_assignments(biz_id, profile_url=None):
    return store.get_broadcaster_assignments(biz_id, profile_url)


@st.cache_data(ttl=15, show_spinner=False)
def load_effective_broadcaster_assignments(biz_id, period):
    return store.get_effective_broadcaster_assignments(biz_id, period)


@st.cache_data(ttl=15, show_spinner=False)
def load_recruiter_assignments(biz_id, agency_name=None):
    return store.get_recruiter_assignments(biz_id, agency_name)


@st.cache_data(ttl=15, show_spinner=False)
def load_effective_recruiter_assignments(biz_id, period):
    return store.get_effective_recruiter_assignments(biz_id, period)


@st.cache_data(ttl=15, show_spinner=False)
def load_recruiter_overrides(biz_id, agency_name=None):
    return store.get_recruiter_broadcaster_overrides(biz_id, agency_name)


@st.cache_data(ttl=15, show_spinner=False)
def load_manual_milestone_events(biz_id, status=None):
    return store.get_manual_milestone_events(biz_id, status)


@st.cache_data(ttl=15, show_spinner=False)
def load_reward_calculations(biz_id, recipient_type=None, period=None, status=None, plan_id=None):
    return store.get_reward_calculations(biz_id, recipient_type=recipient_type, period=period,
                                          status=status, plan_id=plan_id)


@st.cache_data(ttl=15, show_spinner=False)
def load_reward_adjustments(biz_id, calc_id=None):
    return store.get_reward_adjustments(biz_id, calc_id)


@st.cache_data(ttl=60, show_spinner=False)
def load_reward_plan_adoption_counts():
    return store.get_reward_plan_adoption_counts()


def refresh_reward_plan_caches():
    load_reward_plans.clear()
    load_plan_versions.clear()
    load_plan_milestones.clear()
    load_broadcaster_assignments.clear()
    load_effective_broadcaster_assignments.clear()
    load_recruiter_assignments.clear()
    load_effective_recruiter_assignments.clear()
    load_recruiter_overrides.clear()
    load_manual_milestone_events.clear()
    load_reward_calculations.clear()
    load_reward_adjustments.clear()
    load_reward_plan_adoption_counts.clear()


def refresh_caches():
    build_credentials.clear()
    load_all_raw.clear()
    load_assignments.clear()
    load_agencies.clear()
    load_all_users_df.clear()
    load_businesses_df.clear()
    load_agency_counts_by_business.clear()
    load_agency_details.clear()
    load_business_users.clear()
    load_business_memberships.clear()
    load_profile.clear()
    load_payout_rules.clear()
    load_effective_payout_rules.clear()
    load_payout_statuses.clear()
    load_subscription.clear()
    load_billing_events.clear()
    refresh_reward_plan_caches()


def refresh_profile_cache():
    # Perf fix: a display-name/avatar change only touches the profiles
    # table, but every call site used to call the full refresh_caches()
    # (13 caches, including the full broadcaster roster - load_all_raw -
    # and assignments/agencies), forcing an expensive unrelated re-fetch on
    # the next page for a change that only ever needs load_profile cleared.
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
    if not can_view_full_tenant:
        return utils.filter_by_agency(df, user_agency), user_agency
    agencies = ["All", "Agency Direct"] + load_agencies(business_id)
    choice = st.selectbox("Recruitment source", agencies, key=key)
    return utils.filter_by_agency(df, choice), choice


def previous_period_of(period, period_type):
    periods = sorted(set(store.list_periods(period_type, business_id) + [period]), reverse=True)
    idx = periods.index(period)
    remaining = periods[idx + 1:]
    return remaining[0] if remaining else None


# ---------------- Reward Plan Management System: calculation engine ----------------
# Fully additive - reads broadcaster/recruiter roster data the same way the
# existing Payouts/SubAgencies pages already do, but writes only to the new
# reward_calculations table via store's CRUD layer. Never touches
# broadcaster_payout_rules/status or agencies.commission_pct.

def _already_awarded_milestone_keys(biz_id, recipient_type, recipient_id, plan_id, frequency, period,
                                     related_profile_url=None):
    """milestone_keys already recorded (not Rejected/Cancelled) for this
    recipient+plan - scoped the way `frequency` requires: lifetime looks
    across every period ever calculated, monthly/period looks at this
    period only. This is the engine-side defense-in-depth check layered on
    top of reward_calculations' DB partial unique indexes (store.SCHEMA)."""
    calcs = load_reward_calculations(biz_id, recipient_type=recipient_type, plan_id=plan_id)
    if calcs.empty:
        return set()
    calcs = calcs[calcs["recipient_id"] == recipient_id]
    if related_profile_url is not None:
        calcs = calcs[calcs["related_profile_url"] == related_profile_url]
    calcs = calcs[~calcs["status"].isin(["Rejected", "Cancelled"])]
    if frequency in ("monthly_once", "period_once"):
        calcs = calcs[calcs["period"] == period]
    return set(calcs["milestone_key"].dropna().tolist())


def _plan_config_for_period(biz_id, plan_id, period):
    """Resolve (plan row, effective version row, milestone list) for a plan
    at a given reporting period, or None if the plan has no version
    effective yet."""
    plan = store.get_reward_plan(biz_id, plan_id)
    if plan is None or plan["status"] == "draft":
        return None
    version = store.get_effective_plan_version(biz_id, plan_id, period)
    if version is None:
        return None
    milestones_df = load_plan_milestones(biz_id, int(version["id"]))
    milestones = milestones_df.to_dict("records") if not milestones_df.empty else []
    return plan, version, milestones


def recalculate_broadcaster_rewards_for_period(biz_id, period, actor_username):
    """Evaluate every broadcaster's effective reward-plan assignment for one
    reporting period and insert any newly-earned reward_calculations rows.
    Never marks anything Approved/Paid - every row lands at 'Awaiting
    Approval' (or 'Not Eligible' when nothing is earned yet), per the
    approval-before-payment workflow. Safe to call repeatedly - duplicate
    inserts are absorbed by the DB's partial unique indexes and the
    already-awarded check above."""
    assignments = store.get_effective_broadcaster_assignments(biz_id, period)
    if assignments.empty:
        return 0
    roster = load_all_raw(biz_id)
    roster = roster[(roster["period"] == period) & (roster["period_type"] == "monthly")]
    performance_by_profile = {
        row["profile_url"]: row for _, row in roster.iterrows()
    } if not roster.empty else {}

    inserted = 0
    for _, assignment in assignments.iterrows():
        profile_url = assignment["profile_url"]
        plan_id = int(assignment["plan_id"])
        resolved = _plan_config_for_period(biz_id, plan_id, period)
        if resolved is None:
            continue
        plan, version, milestones = resolved
        performance = performance_by_profile.get(profile_url)
        diamonds_redeemed = float(performance["diamonds_redeemed"]) if performance is not None else 0.0
        config = dict(version["config"] or {})

        if plan["reward_method"] == "percentage_cash":
            result = utils.calculate_percentage_reward(
                diamonds_redeemed, config.get("agency_pct", 0), config.get("payout_pct", 0),
                config.get("min_diamonds", 0), config.get("max_monthly_payout"),
            )
            if not result["eligible"] or result["broadcaster_reward"] <= 0:
                continue
            new_id = store.insert_reward_calculation(
                biz_id, "broadcaster", profile_url, None, plan_id, int(version["id"]),
                None, None, version["frequency"], period, plan["reward_method"],
                {"diamonds_redeemed": diamonds_redeemed}, config,
                result["broadcaster_reward"], "cash", config.get("currency", "USD"),
                result["agency_earnings"], result["net_earnings"], None, "Awaiting Approval",
            )
        elif plan["reward_method"] in ("fixed_cash", "fixed_coins"):
            unit = "cash" if plan["reward_method"] == "fixed_cash" else "coins"
            result = utils.calculate_fixed_reward(config.get("fixed_amount", 0), unit)
            if result["amount"] <= 0:
                continue
            new_id = store.insert_reward_calculation(
                biz_id, "broadcaster", profile_url, None, plan_id, int(version["id"]),
                None, None, version["frequency"], period, plan["reward_method"],
                {"diamonds_redeemed": diamonds_redeemed}, config,
                result["amount"], unit, config.get("currency") if unit == "cash" else None,
                None, None, None, "Awaiting Approval",
            )
        else:  # diamond_milestone_*, custom_milestone_*, hybrid
            already = _already_awarded_milestone_keys(
                biz_id, "broadcaster", profile_url, plan_id, version["frequency"], period,
            )
            basis = "diamonds_earned" if config.get("milestone_basis") == "diamonds_earned" else "diamonds_redeemed"
            performance_value = float(performance[basis]) if performance is not None else 0.0
            result = utils.calculate_milestone_reward(
                performance_value, milestones, version["tier_calculation_mode"],
                version["frequency"], already,
            )
            for awarded in result["awarded"]:
                new_id = store.insert_reward_calculation(
                    biz_id, "broadcaster", profile_url, None, plan_id, int(version["id"]),
                    next((m["id"] for m in milestones if m["milestone_key"] == awarded["milestone_key"]), None),
                    awarded["milestone_key"], version["frequency"], period, plan["reward_method"],
                    {basis: performance_value}, config,
                    awarded["reward_value"], awarded["unit"], None, None, None, None,
                    "Awaiting Approval",
                )
                if new_id:
                    inserted += 1
            continue
        if new_id:
            inserted += 1
    if inserted:
        load_reward_calculations.clear()
    return inserted


def recalculate_recruiter_rewards_for_period(biz_id, period, actor_username):
    """Evaluate every recruiter's configured milestones against their
    recruited broadcasters for one reporting period. Manual-only trigger
    types (signup_completed/first_live_completed) only fire when a
    confirmed manual_milestone_events row already exists for that
    broadcaster - this function never creates one itself."""
    assignments_df = load_assignments(biz_id)
    if assignments_df.empty:
        return 0
    roster = load_all_raw(biz_id)
    roster = roster[(roster["period"] == period) & (roster["period_type"] == "monthly")]
    performance_by_profile = {row["profile_url"]: row for _, row in roster.iterrows()} if not roster.empty else {}
    manual_events = load_manual_milestone_events(biz_id, status="Approved")

    inserted = 0
    for _, row in assignments_df.iterrows():
        agency_name, profile_url = row["sub_agency"], row["profile_url"]
        if agency_name == "Agency Direct":
            continue
        resolved_plan = store.get_effective_recruiter_plan(biz_id, agency_name, profile_url, period)
        if resolved_plan is None:
            continue
        plan_id = resolved_plan["plan_id"]
        resolved = _plan_config_for_period(biz_id, plan_id, period)
        if resolved is None:
            continue
        plan, version, milestones = resolved
        performance = performance_by_profile.get(profile_url)
        performance_dict = {
            "diamonds_earned": float(performance["diamonds_earned"]) if performance is not None else 0.0,
            "diamonds_redeemed": float(performance["diamonds_redeemed"]) if performance is not None else 0.0,
            "streaming_days": float(performance["streaming_days"]) if performance is not None else 0.0,
            "streaming_hours": float(performance["streaming_hours"]) if performance is not None else 0.0,
        }

        if plan["reward_method"] == "percentage_cash":
            config = dict(version["config"] or {})
            result = utils.calculate_percentage_reward(
                performance_dict["diamonds_redeemed"], config.get("agency_pct", 0),
                config.get("payout_pct", 0), config.get("min_diamonds", 0),
                config.get("max_monthly_payout"),
            )
            if not result["eligible"] or result["broadcaster_reward"] <= 0:
                continue
            new_id = store.insert_reward_calculation(
                biz_id, "recruiter", agency_name, profile_url, plan_id, int(version["id"]),
                None, None, version["frequency"], period, plan["reward_method"],
                performance_dict, config, result["broadcaster_reward"], "cash",
                config.get("currency", "USD"), result["agency_earnings"], result["net_earnings"],
                None, "Awaiting Approval",
            )
            if new_id:
                inserted += 1
            continue

        already = _already_awarded_milestone_keys(
            biz_id, "recruiter", agency_name, plan_id, None, period, related_profile_url=profile_url,
        )
        already_paid_total = 0.0
        prior_calcs = load_reward_calculations(biz_id, recipient_type="recruiter", plan_id=plan_id)
        if not prior_calcs.empty:
            mine = prior_calcs[
                (prior_calcs["recipient_id"] == agency_name)
                & (prior_calcs["related_profile_url"] == profile_url)
                & (~prior_calcs["status"].isin(["Rejected", "Cancelled"]))
            ]
            already_paid_total = float(mine["calculated_amount"].sum()) if not mine.empty else 0.0

        for milestone in milestones:
            manual_event = None
            if milestone["trigger_type"] in utils.MANUAL_ONLY_TRIGGER_TYPES and not manual_events.empty:
                match = manual_events[
                    (manual_events["recipient_type"] == "recruiter")
                    & (manual_events["recipient_id"] == agency_name)
                    & (manual_events["related_profile_url"] == profile_url)
                    & (manual_events["trigger_type"] == milestone["trigger_type"])
                ]
                manual_event = match.iloc[0].to_dict() if not match.empty else None
            result = utils.calculate_recruiter_milestone_reward(
                performance_dict, milestone, manual_event,
                already if milestone.get("frequency") not in (None, "monthly_once", "period_once") else set(),
                already_paid_total,
            )
            if not result["eligible"] or result["reward_value"] <= 0:
                continue
            status = "Awaiting Approval" if not result["requires_manual_approval"] else "Awaiting Approval"
            trigger_event_id = int(manual_event["id"]) if manual_event else None
            new_id = store.insert_reward_calculation(
                biz_id, "recruiter", agency_name, profile_url, plan_id, int(version["id"]),
                milestone["id"], milestone["milestone_key"], milestone.get("frequency"), period,
                plan["reward_method"], performance_dict, dict(version["config"] or {}),
                result["reward_value"], result["unit"], None, None, None, trigger_event_id, status,
            )
            if new_id:
                inserted += 1
    if inserted:
        load_reward_calculations.clear()
    return inserted


# ============================================================== BUSINESSES
if st.session_state.page == "Businesses":
    if not is_platform_admin:
        st.error("Platform admin access only.")
        st.stop()
    password_reset_notice = st.session_state.pop("_password_reset_notice", None)
    if password_reset_notice:
        st.toast(password_reset_notice, icon="\u2705")
    st.markdown('<div class="platform-admin-page"></div>', unsafe_allow_html=True)
    database_posture = load_database_role_posture()
    database_is_restricted = not any(
        database_posture[key]
        for key in ("superuser", "create_database", "create_role", "replication", "bypass_rls")
    )
    if not database_is_restricted:
        # Fail closed without exposing role names, privileges, or other
        # infrastructure details in the browser.
        st.error("The platform security configuration requires administrator attention.")
        st.stop()
    st.markdown(f"""
    <div class="admin-hero">
      <div>
        <div class="admin-kicker">Platform administration</div>
        <h1>Platform Overview</h1>
        <p>Monitor platform health and manage isolated agency accounts, owners, and access.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    businesses = load_businesses_df()
    all_users = load_all_users_df()
    agency_counts = load_agency_counts_by_business()
    total_agencies = len(businesses)
    active_agencies = int((businesses["status"] == "Active").sum()) if not businesses.empty else 0
    total_owners = int((all_users["role"] == "owner").sum()) if not all_users.empty else 0
    total_sub_agencies = sum(agency_counts.values())

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
    <div class="command-grid-title"><div><h2>Platform Health Overview</h2>
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
                st.markdown("##### Agency Health Directory")
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
                marker=dict(colors=[SO_SUCCESS, SO_WARNING, SO_DANGER]),
                textinfo="label+value", hovertemplate="%{label}: %{value}<extra></extra>",
            ))
            health_fig.update_layout(
                title="Account health distribution", height=310,
                margin=dict(l=10, r=10, t=55, b=10), showlegend=False,
                paper_bgcolor=SO_SURFACE, font=dict(family="Inter", color=SO_MUTED),
                annotations=[dict(text=f"{len(agency_health)}<br>agencies", x=.5, y=.5,
                                  showarrow=False, font=dict(size=16, color=SO_TEXT))],
            )
            with st.container(border=True):
                st.plotly_chart(health_fig, use_container_width=True, config={"displayModeBar": False})

    recent_platform_activity = load_recent_platform_activity(8)
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
          <h2>Set Up a New Agency</h2>
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
                if st.button("Generate Secure Password", key="generate_biz_password"):
                    st.session_state.biz_owner_password = generate_secure_password()
                    st.rerun()

            st.caption("Agency data and user access are isolated from every other agency.")
            if st.button("Create Agency", type="primary", disabled=not biz_name.strip(), width="stretch"):
                if not is_valid_email(owner_email):
                    st.error("Enter a valid owner email address.")
                    st.stop()
                if is_bootstrap_identity(owner_email):
                    st.error("That email is reserved for the Platform Administrator. Use a different owner email.")
                    st.stop()
                if not owner_password.strip():
                    st.error("Enter a temporary password, or generate one.")
                    st.stop()
                password_error = store.password_policy_error(owner_password)
                if password_error:
                    st.error(password_error)
                    st.stop()
                new_business_id = store.create_business(biz_name.strip())
                ok, msg = store.create_user(
                    owner_email.strip(), owner_name.strip() or owner_email.strip(),
                    owner_password, "owner", new_business_id,
                )
                if not ok:
                    st.error(msg)
                    st.stop()
                store.log_security_event(
                    "business_created", username, user_role, new_business_id,
                    "business", new_business_id, f"Owner account: {owner_email.strip().lower()}",
                )
                refresh_caches()
                st.toast(f"Created {biz_name.strip()} with owner login {owner_email.strip()}.", icon="\u2705")
                st.rerun()

    with directory_tab:
        st.markdown("""
        <div class="admin-section-head">
          <h2>Agency Directory</h2>
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
                agency_count = agency_counts.get(bid, 0)
                # Use HTML instead of a Markdown heading so agency names never
                # become clickable URL anchors that can leak into another login.
                safe_directory_name = html.escape(str(b["business_name"]))
                c1.markdown(
                    f'<div style="font-size:1.45rem;font-weight:700;line-height:1.3;'
                    f'letter-spacing:-.02em;margin-bottom:.3rem">{safe_directory_name}</div>',
                    unsafe_allow_html=True,
                )
                owner_label = "owner account" if owner_count == 1 else "owner accounts"
                sub_agency_label = "Sub-Agency" if agency_count == 1 else "Sub-Agencies"
                c1.markdown(f"`{bid}` &nbsp; · &nbsp; {owner_count} {owner_label} "
                            f"&nbsp; · &nbsp; {agency_count} {sub_agency_label}")
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
                                store.log_security_event("business_disabled", username, user_role, bid,
                                                         "business", bid)
                                refresh_caches()
                                st.toast(f"{b['business_name']} disabled.")
                                st.rerun()
                        else:
                            if st.button("Enable", key=f"enbiz_{bid}", type="primary", width="stretch"):
                                store.set_business_status(bid, "Active")
                                store.log_security_event("business_enabled", username, user_role, bid,
                                                         "business", bid)
                                refresh_caches()
                                st.toast(f"{b['business_name']} enabled.", icon="\u2705")
                                st.rerun()

                if st.session_state.get("editing_biz") == bid:
                    st.divider()
                    st.markdown("###### Agency Details")
                    new_name = st.text_input("Agency name", value=b["business_name"], key=f"rename_{bid}")
                    if st.button("Save Agency Name", key=f"savename_{bid}", type="primary"):
                        store.update_business_name(bid, new_name.strip() or b["business_name"])
                        refresh_caches()
                        st.toast("Agency name updated.", icon="\u2705")
                        st.rerun()

                    st.markdown("###### Owner Access")
                    if owners_only.empty:
                        st.info("No owner account exists for this agency yet.")
                    else:
                        for _, ow in owners_only.iterrows():
                            oc1, oc2 = st.columns([2, 1], vertical_alignment="center")
                            oc1.markdown(f"**{ow['name']}**  \n`{ow['username']}`")
                            with oc2:
                                with st.popover("Reset Password", use_container_width=True):
                                    newpw = st.text_input("New password", type="password",
                                                          key=f"bizpw_{ow['username']}")
                                    if st.button("Save Password", key=f"bizpwsave_{ow['username']}",
                                                 type="primary", width="stretch"):
                                        if newpw.strip():
                                            ok, message = store.reset_user_password(ow["username"], newpw.strip())
                                            if ok:
                                                store.log_security_event(
                                                    "password_reset", username, user_role, bid,
                                                    "account", ow["username"],
                                                )
                                                refresh_caches()
                                                st.session_state["_password_reset_notice"] = message
                                                st.rerun()
                                            else:
                                                st.error(message)
                                        else:
                                            st.error("Enter a new password.")

                    st.markdown("###### Plan & Billing")
                    plans_df = load_plans()
                    subscription = load_subscription(bid)
                    current_plan_code = subscription["plan_code"] if subscription is not None else "essential"
                    current_plan_name = (
                        plans_df.loc[plans_df["code"] == current_plan_code, "name"].iloc[0]
                        if not plans_df.empty and current_plan_code in plans_df["code"].values
                        else current_plan_code
                    )
                    if subscription is None:
                        st.caption(
                            f"No payment recorded yet - defaulting to **{current_plan_name}** "
                            "(the most restrictive plan) until one is."
                        )
                    else:
                        period_text = (
                            f"{subscription['current_period_start']} to {subscription['current_period_end']}"
                            if subscription["current_period_start"] is not None else "not set"
                        )
                        st.caption(
                            f"Plan: **{current_plan_name}** &nbsp;·&nbsp; Status: **{subscription['status']}** "
                            f"&nbsp;·&nbsp; Billing cycle: **{subscription['billing_cycle']}** "
                            f"&nbsp;·&nbsp; Current period: {period_text}"
                        )

                    with st.popover("Record Payment", use_container_width=True):
                        plan_options = plans_df["code"].tolist()
                        pay_plan = st.selectbox(
                            "Plan", plan_options, key=f"pay_plan_{bid}",
                            index=plan_options.index(current_plan_code) if current_plan_code in plan_options else 0,
                            format_func=lambda code: plans_df.loc[plans_df["code"] == code, "name"].iloc[0],
                        )
                        plan_row = plans_df.loc[plans_df["code"] == pay_plan].iloc[0]
                        cycle_options = ["annual"] if plan_row["billing_mode"] == "one_time_annual" else ["monthly", "annual"]
                        pay_cycle = st.selectbox("Billing cycle", cycle_options, key=f"pay_cycle_{bid}")
                        default_amount = float(
                            plan_row["price_annual"] if pay_cycle == "annual" else (plan_row["price_monthly"] or 0)
                        )
                        pay_amount = st.number_input(
                            "Amount received (INR)", min_value=0.0, value=default_amount, step=100.0,
                            key=f"pay_amount_{bid}",
                        )
                        pay_method = st.selectbox(
                            "Method", ["bank_transfer", "upi", "cash"], key=f"pay_method_{bid}",
                            format_func=lambda m: {"bank_transfer": "Bank Transfer (NEFT/RTGS)",
                                                    "upi": "UPI", "cash": "Cash"}[m],
                        )
                        pay_reference = st.text_input(
                            "Reference (UTR / UPI transaction ID)", key=f"pay_reference_{bid}",
                        )
                        if st.button("Confirm Payment Recorded", key=f"pay_confirm_{bid}", type="primary"):
                            store.record_payment(
                                bid, pay_plan, pay_cycle, pay_amount, pay_method,
                                pay_reference.strip(), username,
                            )
                            store.log_security_event(
                                "payment_recorded", username, user_role, bid,
                                "subscription", pay_plan,
                                f"amount={pay_amount} method={pay_method} cycle={pay_cycle}",
                            )
                            refresh_caches()
                            st.toast("Payment recorded and subscription updated.", icon="✅")
                            st.rerun()

                    billing_events = load_billing_events(bid)
                    if not billing_events.empty:
                        payment_method_labels = {
                            "bank_transfer": "Bank Transfer", "upi": "UPI",
                            "cash": "Cash", "gateway": "Gateway",
                        }
                        with st.expander(f"Payment history ({len(billing_events)})", expanded=False):
                            for _, ev in billing_events.iterrows():
                                method_label = payment_method_labels.get(ev["method"], ev["method"])
                                st.markdown(
                                    f"**₹{ev['amount']:,.2f}** via {method_label} "
                                    f"&nbsp;·&nbsp; {ev['created_at']} &nbsp;·&nbsp; recorded by `{ev['recorded_by']}`"
                                    + (f" &nbsp;·&nbsp; ref: {html.escape(str(ev['reference_note']))}"
                                       if ev["reference_note"] else "")
                                )

    st.markdown("### Reward Plan Adoption")
    st.caption(
        "Plan usage counts across every agency - never reward amounts or recipient statements, "
        "which stay confidential to each Agency Owner and are not queried here at all."
    )
    adoption_counts = load_reward_plan_adoption_counts()
    if adoption_counts.empty:
        st.info("No agency has created a reward plan yet.")
    else:
        adoption_view = adoption_counts.merge(
            businesses[["business_id", "business_name"]], on="business_id", how="left",
        )
        st.dataframe(
            adoption_view[["business_name", "recipient_type", "reward_method", "status", "plan_count"]],
            hide_index=True, width="stretch",
            column_config={
                "business_name": "Agency", "recipient_type": "Recipient type", "reward_method": "Method",
                "status": "Status", "plan_count": st.column_config.NumberColumn("Plans"),
            },
        )

# ================================================================ MY PROFILE
elif st.session_state.page == "MyProfile":
    st.title("My Profile")
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
                f'<div style="width:96px;height:96px;border-radius:50%;background:#F1EDFF;'
                f'color:{SO_BRAND};display:flex;align-items:center;justify-content:center;'
                f'font-size:32px;font-weight:700;">{initials}</div>',
                unsafe_allow_html=True,
            )
    with col2:
        st.markdown(f"**{display_name}**")
        st.caption(f"{username} \u00b7 {user_role.replace('_', ' ')}")

    st.markdown("##### Display Name")
    new_display_name = st.text_input("Name", value=display_name, key="profile_name")
    if st.button("Save name", type="primary", disabled=not new_display_name.strip()):
        store.upsert_profile(username, display_name=new_display_name.strip())
        refresh_profile_cache()
        st.toast("Name updated.", icon="\u2705")
        st.rerun()

    st.markdown("##### Profile Picture")
    pic = st.file_uploader("Upload a picture (PNG or JPG, under 1.5 MB)", type=["png", "jpg", "jpeg"], key="profile_pic")
    if pic is not None:
        if pic.size > 1_500_000:
            st.error("That image is too large \u2014 please use a picture under 1.5 MB.")
        else:
            encoded = base64.b64encode(pic.read()).decode("utf-8")
            if st.button("Save picture", type="primary"):
                store.upsert_profile(username, avatar_base64=encoded)
                refresh_profile_cache()
                st.toast("Profile picture updated.", icon="\u2705")
                st.rerun()

    if avatar_b64:
        if st.button("Remove current picture"):
            store.upsert_profile(username, avatar_base64="")
            refresh_profile_cache()
            st.toast("Profile picture removed.", icon="\u2705")
            st.rerun()

# ============================================================ POSTER STUDIO
elif st.session_state.page == "PosterStudio":
    if user_role not in ("owner", "agency_manager"):
        st.error("Owner or Agency Manager access only.")
    elif not poster_studio_enabled():
        st.info("AI Poster Studio is currently disabled for this environment.")
    else:
        try:
            from poster.ui import render as render_poster_studio
            render_poster_studio(
                username=username, user_role=user_role,
                business_id=business_id, business_name=business_name,
            )
        except Exception as e:
            # Isolated by design (Section 70): a failure here must never take
            # down the rest of the dashboard.
            print(f"poster_studio: page failed to load — {type(e).__name__}: {e}")
            st.error("AI Poster Studio is temporarily unavailable. Please try again shortly.")

# ==================================================================== ADMIN
elif st.session_state.page == "Admin":
    ai_enabled = load_ai_features_enabled(business_id)
    pdf_export_enabled = load_pdf_export_enabled(business_id)
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    overview_title = "My Dashboard" if can_view_full_tenant else f"{html.escape(str(user_agency))} overview"
    overview_subtitle = (f"Performance across {html.escape(str(business_name))}'s agency network" if can_view_full_tenant
                         else "Performance for your assigned broadcaster roster")
    st.markdown(f"""
    <div class="overview-hero">
      <div>
        <div class="overview-eyebrow">{'Agency owner' if can_view_full_tenant else 'Sub-Agency workspace'}</div>
        <h1>{overview_title}</h1>
        <p>{overview_subtitle}</p>
      </div>
      <div class="overview-period-pill">Live operational overview</div>
    </div>
    """, unsafe_allow_html=True)
    dashboard_section_control("my_dashboard", ["Overview", "Performance", "Financials", "Insights"])

    monthly_periods = store.list_periods("monthly", business_id)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet. Go to **Upload report** in the sidebar.")
        st.stop()

    if can_view_full_tenant:
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
    scope_agency = agency_choice if can_view_full_tenant else user_agency
    if not df_previous.empty:
        df_previous = utils.filter_by_agency(df_previous, scope_agency)

    if can_view_full_tenant:
        attribution_all = utils.attribution_completeness(df_current_all)

    kpis = utils.compute_kpis(df_current)
    prev_kpis = utils.compute_kpis(df_previous) if not df_previous.empty else {}
    n_agencies = max(1, len(load_agencies(business_id))) if can_view_full_tenant else 1
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

    my_overview_panel = dashboard_panel("my_dashboard", "Overview")
    my_overview_panel.__enter__()
    if ai_enabled:
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
    else:
        st.info(
            "**AI-driven health score and retention alerts are a Growth-plan feature and above.** "
            "Upgrade to see a broadcaster health score and early retention warnings here."
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        overview_kpi_card("Total broadcasters", f"{kpis['broadcasters']:,}", "♟",
                          broadcaster_note, broadcaster_direction)
    with c2:
        overview_kpi_card("Active broadcasters", f"{kpis['active']:,}", "●",
                          active_note, active_direction)
    with c3:
        overview_kpi_card("Diamonds redeemed", f"{kpis['diamonds_redeemed']:,}", "◇",
                          diamond_note, diamond_direction)
    with c4:
        if can_view_full_tenant:
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
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        overview_kpi_card("Days streamed", f"{kpis['days_worked']:,}", "◷",
                          days_note, days_direction)
    with c6:
        overview_kpi_card("Average diamonds per broadcaster", f"{avg_dpb:,.1f}", "↗",
                          f"Across {n_agencies} active Sub-Agencies" if can_view_full_tenant else "Current roster average")
    with c7:
        overview_kpi_card("New broadcasters", f"{int(df_current['is_new'].sum()):,}", "+",
                          "Added in the selected month")
    with c8:
        overview_kpi_card("Streaming hours", f"{float(df_current['streaming_hours'].sum()):,.1f}", "◴",
                          "Total hours in the selected month")
    my_overview_panel.__exit__(None, None, None)

    my_financials_panel = dashboard_panel("my_dashboard", "Financials")
    my_financials_panel.__enter__()
    if can_view_full_tenant:
        direct_df = df_current_all[df_current_all["sub_agency"] == "Agency Direct"]
        partner_df = df_current_all[df_current_all["sub_agency"] != "Agency Direct"]
        direct_kpis = utils.compute_kpis(direct_df)
        partner_kpis = utils.compute_kpis(partner_df)
        commission_rates = {
            row["agency_name"]: (0.0 if pd.isna(row["commission_pct"]) else float(row["commission_pct"]))
            for _, row in load_agency_details(business_id).iterrows()
        }
        partner_commission_due = 0.0
        for partner_name, partner_rows in partner_df.groupby("sub_agency"):
            _, commission_due = calculate_sub_agency_earnings(
                partner_rows["diamonds_redeemed"].sum(), commission_rates.get(partner_name, 0.0)
            )
            partner_commission_due += float(commission_due or 0)
        direct_earnings = float(direct_kpis["my_earnings_usd"])
        partner_gross_earnings = float(partner_kpis["my_earnings_usd"])
        partner_net_earnings = partner_gross_earnings - partner_commission_due
        total_net_earnings = direct_earnings + partner_net_earnings

        st.markdown("""
        <div class="overview-section">
          <h2>Recruitment and Earnings Mix</h2>
          <p>See what the Agency generated through its own hires versus third-party Sub-Agencies.</p>
        </div>
        """, unsafe_allow_html=True)
        mix1, mix2, mix3, mix4 = st.columns(4)
        mix1.metric("Agency direct hires", f"{direct_kpis['broadcasters']:,}",
                    f"${direct_earnings:,.2f} Agency earnings")
        mix2.metric("Sub-Agency hires", f"{partner_kpis['broadcasters']:,}",
                    f"${partner_gross_earnings:,.2f} gross Agency earnings")
        mix3.metric("Sub-Agency commission", f"${partner_commission_due:,.2f}",
                    "Calculated from each saved commission rate")
        mix4.metric("Estimated net earnings", f"${total_net_earnings:,.2f}",
                    f"${partner_net_earnings:,.2f} retained from Sub-Agencies")

        mix_chart = go.Figure(go.Bar(
            x=["Agency Direct", "Sub-Agencies"],
            y=[direct_earnings, partner_net_earnings],
            marker_color=[SO_BRAND, SO_VIOLET],
            text=[f"${direct_earnings:,.2f}", f"${partner_net_earnings:,.2f}"],
            textposition="outside",
            hovertemplate="%{x}<br>Net Agency earnings: $%{y:,.2f}<extra></extra>",
        ))
        mix_chart.update_layout(
            title="Net Agency earnings by recruitment source", height=300,
            margin=dict(l=20, r=20, t=55, b=20), showlegend=False,
            yaxis=dict(title=None, gridcolor=SO_GRID, tickprefix="$"),
            xaxis=dict(title=None), paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
            font=dict(family="Inter", color=SO_MUTED),
        )
        with st.container(border=True):
            st.plotly_chart(mix_chart, use_container_width=True, config={"displayModeBar": False})
            st.caption(
                "Agency Direct uses My Earnings (USD) from the uploaded Tango report. "
                "Sub-Agency net deducts commission (redeemed diamonds ÷ 200 × saved rate) "
                "from the Agency's My Earnings (USD)."
            )
    elif is_sub_agency:
        st.markdown("### Commission Summary")
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Redeemed value", f"${sub_gross_usd:,.2f}")
        fc2.metric("Commission rate", "Not set" if sub_commission_pct is None else f"{sub_commission_pct:g}%")
        fc3.metric("Commission earned", "Not set" if sub_commission_usd is None else f"${sub_commission_usd:,.2f}")
    my_financials_panel.__exit__(None, None, None)

    my_insights_panel = dashboard_panel("my_dashboard", "Insights")
    my_insights_panel.__enter__()
    if not ai_enabled:
        st.info(
            "**Automated Insights is a Growth-plan feature and above.** "
            "Upgrade to unlock retention health, at-risk alerts, and an automated "
            "monthly management summary here."
        )
    else:
        st.markdown("""
        <div class="overview-section">
          <h2>Automated Insights</h2>
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
            if can_view_full_tenant:
                st.markdown(f"""
                <div class="insight-card">
                  <div class="insight-label">Sub-Agency share</div>
                  <div class="insight-value">{attribution_all['pct_assigned']}%</div>
                  <div class="insight-caption">Roster assigned to third-party Sub-Agencies</div>
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

        at_risk_label = "broadcaster" if len(at_risk_df) == 1 else "broadcasters"
        if len(at_risk_df) > 0:
            with st.expander(f"{len(at_risk_df)} {at_risk_label} earned diamonds last period and streamed 0 days this period"):
                at_risk_columns = (["broadcaster_name", "sub_agency"] if can_view_full_tenant
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
            f"and **{len(at_risk_df)}** {at_risk_label} currently need retention follow-up."
        )
        follow_up_rows = []
        for _, risk_row in at_risk_df.head(8).iterrows():
            follow_up_rows.append({
                "Priority": "High", "Broadcaster": risk_row["broadcaster_name"],
                "Sub-Agency": risk_row.get("sub_agency", user_agency or "—"),
                "Reason": "Previously productive; no streaming days this month",
                "Recommended action": "Contact and agree a reactivation plan",
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
    my_insights_panel.__exit__(None, None, None)

    my_performance_panel = dashboard_panel("my_dashboard", "Performance")
    my_performance_panel.__enter__()
    st.markdown("""
    <div class="command-grid-title"><div><h2>Target and Financial Outlook</h2>
    <p>Current progress against an 8% improvement target based on the previous reporting period.</p></div></div>
    """, unsafe_allow_html=True)
    outlook_left, outlook_right = st.columns([1, 1.45])
    progress_width = min(100, max(0, diamond_target["progress_pct"]))
    with outlook_left:
        with st.container(border=True):
            st.markdown("##### Monthly Performance Target")
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
                st.markdown("##### Commission Summary")
                pc1, pc2 = st.columns(2)
                pc1.metric("Gross redeemed value", f"${sub_gross_usd:,.2f}")
                pc2.metric("Commission earned", "Not set" if sub_commission_usd is None else f"${sub_commission_usd:,.2f}")
                statement = df_current[["broadcaster_name", "diamonds_redeemed", "streaming_days"]].copy()
                statement["gross_value_usd"] = statement["diamonds_redeemed"] / DIAMONDS_PER_USD
                statement["commission_pct"] = sub_commission_pct
                statement["commission_usd"] = (statement["gross_value_usd"] * sub_commission_pct / 100
                                                if sub_commission_pct is not None else None)
                if can_export:
                    st.download_button(
                        "Download commission statement", utils.safe_csv_bytes(statement),
                        file_name=f"commission_statement_{user_agency}_{current_period}.csv",
                        mime="text/csv", width="stretch",
                    )
                    if pdf_export_enabled:
                        st.download_button(
                            "Download commission statement (PDF)",
                            utils.safe_pdf_bytes(
                                statement, "Commission Statement",
                                f"{html.escape(str(user_agency))} — {current_period}",
                            ),
                            file_name=f"commission_statement_{user_agency}_{current_period}.pdf",
                            mime="application/pdf", width="stretch",
                        )
    with outlook_right:
        if can_view_full_tenant:
            comparison_rows = []
            agency_details = load_agency_details(business_id)
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
                    marker=dict(color=SO_BRAND), text=comparison["Diamonds"], texttemplate="%{text:,.0f}",
                    textposition="outside", hovertemplate="%{y}<br>%{x:,.0f} diamonds<extra></extra>",
                ))
                compare_fig.update_layout(
                    title="Sub-Agency performance", height=285, margin=dict(l=10, r=45, t=50, b=20),
                    xaxis=dict(showgrid=True, gridcolor=SO_GRID, title=None),
                    yaxis=dict(title=None), paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                    font=dict(family="Inter", color=SO_MUTED), showlegend=False,
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
                st.markdown("##### Assigned Broadcaster Performance")
                st.dataframe(
                    roster_view[roster_columns].sort_values("diamonds_redeemed", ascending=False).head(8),
                    hide_index=True, width="stretch", column_config=table_column_config(roster_columns),
                )

    st.markdown("""
    <div class="overview-section">
      <h2>Performance Trend</h2>
      <p>Diamonds redeemed and active broadcaster movement over time.</p>
    </div>
    """, unsafe_allow_html=True)
    trend_periods = sorted(monthly_periods)[-6:]
    if len(trend_periods) > 1:
        trend_diamonds, trend_active, trend_agency_revenue, trend_creator_revenue = [], [], [], []
        for trend_period in trend_periods:
            trend_df = period_data(trend_period, "monthly")
            trend_df = utils.filter_by_agency(trend_df, scope_agency)
            trend_kpis = utils.compute_kpis(trend_df)
            trend_diamonds.append(trend_kpis["diamonds_redeemed"])
            trend_active.append(trend_kpis["active"])
            trend_agency_revenue.append(trend_kpis["my_earnings_usd"])
            trend_creator_revenue.append(float(trend_df["usd_earned"].sum()))

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(
            name="Diamonds redeemed", x=trend_periods, y=trend_diamonds,
            mode="lines+markers", line=dict(color=SO_BRAND, width=3),
            marker=dict(size=8, color=SO_BRAND), fill="tozeroy",
            fillcolor=SO_BRAND_FILL, hovertemplate="%{x}<br>%{y:,.0f} diamonds<extra></extra>",
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            name="Active broadcasters", x=trend_periods, y=trend_active,
            mode="lines+markers", line=dict(color=SO_CYAN, width=2.5),
            marker=dict(size=7, color=SO_CYAN),
            hovertemplate="%{x}<br>%{y:,.0f} active<extra></extra>",
        ), secondary_y=True)
        fig.update_layout(
            height=390, margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE, hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.04, x=0),
            font=dict(family="Inter", color=SO_MUTED),
        )
        fig.update_xaxes(showgrid=False, title=None)
        fig.update_yaxes(title_text="Diamonds", gridcolor=SO_GRID, zeroline=False, secondary_y=False)
        fig.update_yaxes(title_text="Active broadcasters", showgrid=False, zeroline=False, secondary_y=True)
        with st.container(border=True):
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        financial_left, lifecycle_right = st.columns(2)
        financial_fig = go.Figure()
        financial_fig.add_trace(go.Scatter(
            name="Agency revenue", x=trend_periods, y=trend_agency_revenue,
            mode="lines+markers", line=dict(color=SO_BRAND, width=3),
            hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
        ))
        financial_fig.add_trace(go.Scatter(
            name="Creator revenue", x=trend_periods, y=trend_creator_revenue,
            mode="lines+markers", line=dict(color=SO_CYAN, width=2.5),
            hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
        ))
        financial_fig.update_layout(
            title="Monthly revenue trend", height=330, margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE, hovermode="x unified",
            yaxis=dict(tickprefix="$", gridcolor=SO_GRID),
            legend=dict(orientation="h", y=1.05),
        )
        with financial_left:
            with st.container(border=True):
                st.plotly_chart(financial_fig, use_container_width=True, config={"displayModeBar": False})
        lifecycle_df = utils.add_growth_status(df_current, df_previous)
        lifecycle_counts = lifecycle_df["status"].value_counts()
        lifecycle_fig = go.Figure(go.Bar(
            x=lifecycle_counts.index, y=lifecycle_counts.values,
            marker_color=SO_PERIWINKLE, text=lifecycle_counts.values, textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
        ))
        lifecycle_fig.update_layout(title="Broadcaster lifecycle", height=330,
                                    margin=dict(l=20, r=20, t=50, b=35), showlegend=False,
                                    paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                    yaxis=dict(gridcolor=SO_GRID, title="Broadcasters"), xaxis=dict(title=None))
        with lifecycle_right:
            with st.container(border=True):
                st.plotly_chart(lifecycle_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Upload a second month to unlock the performance trend.")

    st.markdown("""
    <div class="overview-section">
      <h2>Top Performers</h2>
      <p>Broadcasters leading the selected period by diamonds redeemed.</p>
    </div>
    """, unsafe_allow_html=True)
    top5 = utils.leaderboard(df_current, 5)
    if top5.empty:
        st.info("No broadcaster performance data is available for this selection yet.")
    else:
        cols = ["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"] if can_view_full_tenant \
            else ["broadcaster_name", "diamonds_redeemed", "streaming_days"]
        with st.container(border=True):
            st.dataframe(
                top5[cols], hide_index=True, width='stretch',
                column_config=table_column_config(cols),
            )
    my_performance_panel.__exit__(None, None, None)

# ================================================================ STATISTICS
elif st.session_state.page == "Statistics":
    if not can_view_full_tenant:
        st.error("Owner, Agency Manager, or Auditor access only.")
        st.stop()
    pdf_export_enabled = load_pdf_export_enabled(business_id)
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="overview-hero"><div><div class="overview-eyebrow">Agency analytics</div>
    <h1>Broadcaster Dashboard</h1><p>Search, segment, and compare every broadcaster in the agency roster.</p>
    </div><div class="overview-period-pill">Broadcaster intelligence</div></div>
    """, unsafe_allow_html=True)
    if load_broadcaster_dashboard_access(business_id) == "off":
        st.info(
            "**The Broadcaster Dashboard is a Growth-plan feature and above.** "
            "Upgrade to unlock roster-wide analytics, retention health, and "
            "performance comparisons here."
        )
        st.stop()
    dashboard_section_control("broadcaster_dashboard", ["Overview", "Performance", "Retention", "Directory"])
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Reporting month", monthly_periods, key="stats_month")
    df_all = period_data(current_period, "monthly")
    prev_period = previous_period_of(current_period, "monthly")
    df_prev_all = period_data(prev_period, "monthly") if prev_period else pd.DataFrame()
    if df_all.empty:
        st.info("No broadcasters in this reporting month.")
        st.stop()

    analytics = utils.diamonds_per_day(utils.add_growth_status(df_all, df_prev_all))
    at_risk_all = utils.at_risk_broadcasters(df_all, df_prev_all) if not df_prev_all.empty else df_all.iloc[0:0]
    total = analytics["profile_url"].nunique()
    active = int((analytics["streaming_days"] > 0).sum())
    inactive = total - active
    new_count = int(analytics["is_new"].sum())
    reactivated = int((analytics["status"] == "Reactivated").sum())
    avg_hours = float(analytics["streaming_hours"].mean()) if total else 0
    avg_creator_revenue = float(analytics["usd_earned"].mean()) if total else 0

    broadcaster_overview_panel = dashboard_panel("broadcaster_dashboard", "Overview")
    broadcaster_overview_panel.__enter__()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total broadcasters", f"{total:,}")
    k2.metric("Active", f"{active:,}", f"{active / max(1, total) * 100:.1f}% of roster")
    k3.metric("Inactive", f"{inactive:,}")
    k4.metric("New this month", f"{new_count:,}")
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Reactivated", f"{reactivated:,}")
    k6.metric("At risk", f"{len(at_risk_all):,}")
    k7.metric("Average streaming hours", f"{avg_hours:,.1f}")
    k8.metric("Average creator revenue", f"${avg_creator_revenue:,.2f}")
    broadcaster_overview_panel.__exit__(None, None, None)

    broadcaster_retention_panel = dashboard_panel("broadcaster_dashboard", "Retention")
    broadcaster_retention_panel.__enter__()
    st.markdown("### Retention and Broadcaster Health")
    retention_value = utils.retention_rate(df_all, df_prev_all) if not df_prev_all.empty else None
    health_value = utils.broadcaster_health_score(df_all, df_prev_all)
    rh1, rh2, rh3 = st.columns(3)
    rh1.metric("Retention rate", f"{retention_value:.1f}%" if retention_value is not None else "First period")
    rh2.metric("At-risk broadcasters", f"{len(at_risk_all):,}")
    rh3.metric("Roster health", f"{health_value}/100")
    if at_risk_all.empty:
        st.success("No previously productive broadcasters have dropped to zero activity.")
    else:
        risk_cols = ["broadcaster_name", "sub_agency", "diamonds_redeemed", "streaming_days"]
        st.dataframe(at_risk_all[risk_cols], hide_index=True, width="stretch",
                     column_config=table_column_config(risk_cols))
    broadcaster_retention_panel.__exit__(None, None, None)

    with st.expander("Search and filters", expanded=False, icon=":material/filter_alt:"):
        f1, f2, f3 = st.columns([1.4, 1, 1])
        search = f1.text_input("Search broadcaster", placeholder="Name or profile URL", key="bd_search")
        source_options = ["All", "Agency Direct"] + load_agencies(business_id)
        source = f2.selectbox("Recruitment source", source_options, key="bd_source")
        available_statuses = sorted(analytics["status"].dropna().unique().tolist())
        statuses = f3.multiselect("Broadcaster status", available_statuses, key="bd_status")
        f4, f5, f6 = st.columns(3)
        new_filter = f4.selectbox("New broadcaster", ["All", "New only", "Existing only"], key="bd_new")
        min_hours = f5.number_input("Minimum streaming hours", min_value=0.0, value=0.0, step=1.0, key="bd_hours")
        min_revenue = f6.number_input("Minimum creator revenue", min_value=0.0, value=0.0, step=10.0, key="bd_revenue")

    view = analytics.copy()
    if search.strip():
        needle = search.strip()
        view = view[
            view["broadcaster_name"].str.contains(needle, case=False, na=False)
            | view["profile_url"].str.contains(needle, case=False, na=False)
        ]
    if source != "All":
        view = utils.filter_by_agency(view, source)
    if statuses:
        view = view[view["status"].isin(statuses)]
    if new_filter == "New only":
        view = view[view["is_new"]]
    elif new_filter == "Existing only":
        view = view[~view["is_new"]]
    view = view[(view["streaming_hours"] >= min_hours) & (view["usd_earned"] >= min_revenue)]

    broadcaster_performance_panel = dashboard_panel("broadcaster_dashboard", "Performance")
    broadcaster_performance_panel.__enter__()
    chart_left, chart_right = st.columns(2)
    with chart_left:
        top_revenue = view.nlargest(10, "usd_earned").sort_values("usd_earned")
        revenue_fig = go.Figure(go.Bar(
            x=top_revenue["usd_earned"], y=top_revenue["broadcaster_name"], orientation="h",
            marker_color=SO_BRAND, text=top_revenue["usd_earned"], texttemplate="$%{text:,.0f}",
            textposition="outside", hovertemplate="%{y}<br>$%{x:,.2f}<extra></extra>",
        ))
        revenue_fig.update_layout(title="Top broadcasters by creator revenue", height=350,
                                  margin=dict(l=10, r=55, t=50, b=20), showlegend=False,
                                  paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                  xaxis=dict(gridcolor=SO_GRID, tickprefix="$"), yaxis=dict(title=None))
        with st.container(border=True):
            st.plotly_chart(revenue_fig, use_container_width=True, config={"displayModeBar": False})
    with chart_right:
        status_counts = view["status"].value_counts()
        status_fig = go.Figure(go.Bar(
            x=status_counts.index, y=status_counts.values, marker_color=SO_PERIWINKLE,
            text=status_counts.values, textposition="outside",
            hovertemplate="%{x}: %{y}<extra></extra>",
        ))
        status_fig.update_layout(title="Broadcaster activity distribution", height=350,
                                 margin=dict(l=20, r=20, t=50, b=35), showlegend=False,
                                 paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                 yaxis=dict(gridcolor=SO_GRID, title="Broadcasters"), xaxis=dict(title=None))
        with st.container(border=True):
            st.plotly_chart(status_fig, use_container_width=True, config={"displayModeBar": False})

    distribution_left, relationship_right = st.columns(2)
    source_revenue = view.groupby("sub_agency", as_index=False)["usd_earned"].sum()
    source_revenue = source_revenue.sort_values("usd_earned")
    distribution_fig = go.Figure(go.Bar(
        x=source_revenue["usd_earned"], y=source_revenue["sub_agency"], orientation="h",
        marker_color=SO_COBALT, text=source_revenue["usd_earned"], texttemplate="$%{text:,.0f}",
        textposition="outside", hovertemplate="%{y}<br>$%{x:,.2f}<extra></extra>",
    ))
    distribution_fig.update_layout(title="Creator revenue distribution by source", height=340,
                                   margin=dict(l=10, r=55, t=50, b=20), showlegend=False,
                                   paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                   xaxis=dict(gridcolor=SO_GRID, tickprefix="$"), yaxis=dict(title=None))
    with distribution_left:
        with st.container(border=True):
            st.plotly_chart(distribution_fig, use_container_width=True, config={"displayModeBar": False})
    relationship_fig = go.Figure(go.Scatter(
        x=view["streaming_hours"], y=view["usd_earned"], mode="markers",
        text=view["broadcaster_name"], marker=dict(size=10, color=view["diamonds_redeemed"],
                                                   colorscale=[[0, SO_PERIWINKLE], [1, SO_CYAN]], showscale=True,
                                                   colorbar=dict(title="Diamonds")),
        hovertemplate="%{text}<br>%{x:.1f} hours<br>$%{y:,.2f}<extra></extra>",
    ))
    relationship_fig.update_layout(title="Streaming hours and creator revenue", height=340,
                                   margin=dict(l=20, r=20, t=50, b=35),
                                   xaxis=dict(title="Streaming hours", gridcolor=SO_GRID),
                                   yaxis=dict(title="Creator revenue", tickprefix="$", gridcolor=SO_GRID),
                                   paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE)
    with relationship_right:
        with st.container(border=True):
            st.plotly_chart(relationship_fig, use_container_width=True, config={"displayModeBar": False})
    broadcaster_performance_panel.__exit__(None, None, None)

    broadcaster_directory_panel = dashboard_panel("broadcaster_dashboard", "Directory")
    broadcaster_directory_panel.__enter__()
    result_label = "result" if len(view) == 1 else "results"
    st.markdown(f"### Broadcaster Report · {len(view):,} {result_label}")
    show_cols = ["broadcaster_name", "profile_url", "sub_agency", "status", "is_new",
                 "streaming_days", "streaming_hours", "diamonds_earned", "diamonds_redeemed",
                 "usd_earned", "my_earnings_usd", "diamonds_per_day", "growth_pct"]
    st.dataframe(view[show_cols].sort_values("usd_earned", ascending=False), width="stretch",
                 hide_index=True, column_config=table_column_config(show_cols))
    if can_export:
        st.download_button(
            "Download broadcaster report", utils.safe_csv_bytes(view[show_cols]),
            file_name=f"broadcaster_dashboard_{current_period}.csv", mime="text/csv",
        )
        if pdf_export_enabled and len(view) <= utils.MAX_PDF_ROWS:
            st.download_button(
                "Download broadcaster report (PDF)",
                utils.safe_pdf_bytes(
                    view[show_cols], "Broadcaster Report",
                    f"{html.escape(str(business_name))} — {current_period}",
                ),
                file_name=f"broadcaster_dashboard_{current_period}.pdf", mime="application/pdf",
            )
    broadcaster_directory_panel.__exit__(None, None, None)

# =============================================================== AUDIT LOG
elif st.session_state.page == "AuditLog":
    if not can_view_full_tenant:
        st.error("Owner, Agency Manager, or Auditor access only.")
        st.stop()
    st.title("Audit Log")
    st.caption(
        "Recent sign-ins and security-sensitive changes in this agency workspace. "
        "Read-only - the same activity Owner sees embedded in Data Management, "
        "surfaced here as its own page for Auditor, which doesn't have access "
        "to Data Management's write actions."
    )
    audit_df = load_security_audit(business_id, limit=200)
    if audit_df.empty:
        st.info("No security activity has been recorded yet.")
    else:
        st.dataframe(audit_df, hide_index=True, width="stretch")

# ================================================================== PAYOUTS
elif st.session_state.page == "RewardOverview":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="overview-hero"><div><div class="overview-eyebrow">Reward plan system</div>
    <h1>Reward Overview</h1><p>A consolidated view of every configurable reward plan calculation - separate
    from the existing broadcaster percentage payout and recruiter commission systems, which are unaffected.</p>
    </div><div class="overview-period-pill">Configurable reward plans</div></div>
    """, unsafe_allow_html=True)

    reward_overview_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not reward_overview_periods:
        st.info("Upload a monthly report, then create and assign a reward plan under **Reward Plans** to begin.")
        st.stop()
    reward_overview_period = st.selectbox("Reporting month", reward_overview_periods, key="reward_overview_month")

    all_calcs = load_reward_calculations(business_id)
    if not all_calcs.empty:
        all_calcs = all_calcs.copy()
        all_calcs["effective_amount"] = all_calcs["adjusted_amount"].fillna(all_calcs["calculated_amount"])
    period_calcs = (
        all_calcs[all_calcs["period"] == reward_overview_period] if not all_calcs.empty else all_calcs
    )

    def _sum_unit(df, unit, statuses=None):
        if df is None or df.empty:
            return 0.0
        subset = df[df["unit"] == unit]
        if statuses:
            subset = subset[subset["status"].isin(statuses)]
        return round(float(subset["effective_amount"].sum()), 2)

    due_statuses = ["Awaiting Approval", "Milestone Reached", "Approved"]
    cash_due = _sum_unit(all_calcs, "cash", due_statuses)
    coins_due = _sum_unit(all_calcs, "coins", due_statuses)
    cash_approved = _sum_unit(all_calcs, "cash", ["Approved"])
    coins_approved = _sum_unit(all_calcs, "coins", ["Approved"])
    cash_paid = _sum_unit(all_calcs, "cash", ["Paid"])
    coins_paid = _sum_unit(all_calcs, "coins", ["Paid"])
    pending_count = int((all_calcs["status"] == "Awaiting Approval").sum()) if not all_calcs.empty else 0
    milestones_this_month = int(
        (period_calcs["milestone_id"].notna() & ~period_calcs["status"].isin(["Rejected", "Cancelled"])).sum()
    ) if not period_calcs.empty else 0

    roster = load_all_raw(business_id)
    roster_period = (
        roster[(roster["period"] == reward_overview_period) & (roster["period_type"] == "monthly")]
        if not roster.empty else roster
    )
    all_profiles = set(roster_period["profile_url"]) if not roster_period.empty else set()
    effective_broadcaster_plans = load_effective_broadcaster_assignments(business_id, reward_overview_period)
    plan_assigned_profiles = (
        set(effective_broadcaster_plans["profile_url"]) if not effective_broadcaster_plans.empty else set()
    )
    broadcasters_without_plan = len(all_profiles - plan_assigned_profiles)

    all_agencies = set(load_agencies(business_id))
    effective_recruiter_plans = load_effective_recruiter_assignments(business_id, reward_overview_period)
    recruiter_assigned = (
        set(effective_recruiter_plans["agency_name"]) if not effective_recruiter_plans.empty else set()
    )
    recruiters_without_plan = len(all_agencies - recruiter_assigned)

    st.markdown("#### Cash rewards")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total cash due", f"${cash_due:,.2f}")
    c2.metric("Approved cash", f"${cash_approved:,.2f}")
    c3.metric("Paid cash", f"${cash_paid:,.2f}")

    st.markdown("#### Coin rewards")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total coins due", f"{coins_due:,.0f}")
    k2.metric("Approved coins", f"{coins_approved:,.0f}")
    k3.metric("Paid coins", f"{coins_paid:,.0f}")
    st.caption("Cash and coin rewards are never combined into one total.")

    st.markdown("#### Plan coverage")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Pending approvals", pending_count)
    p2.metric("Milestones reached this month", milestones_this_month)
    p3.metric("Broadcasters without a plan", broadcasters_without_plan)
    p4.metric("Recruiters without a plan", recruiters_without_plan)

    if not all_calcs.empty:
        st.markdown("#### Rewards by plan")
        st.dataframe(
            all_calcs.groupby(["plan_name", "unit"], as_index=False)["effective_amount"].sum(),
            hide_index=True, width="stretch",
            column_config={"plan_name": "Plan", "unit": "Unit",
                           "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f")},
        )
        st.markdown("#### Rewards by recipient type")
        st.dataframe(
            all_calcs.groupby(["recipient_type", "unit"], as_index=False)["effective_amount"].sum(),
            hide_index=True, width="stretch",
            column_config={"recipient_type": "Recipient type", "unit": "Unit",
                           "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f")},
        )
        broadcaster_calcs = all_calcs[all_calcs["recipient_type"] == "broadcaster"].copy()
        assignments_for_source = load_assignments(business_id)
        if not broadcaster_calcs.empty and not assignments_for_source.empty:
            source_map = dict(zip(assignments_for_source["profile_url"], assignments_for_source["sub_agency"]))
            broadcaster_calcs["recruitment_source"] = broadcaster_calcs["recipient_id"].map(source_map).fillna("Agency Direct")
            st.markdown("#### Rewards by recruitment source")
            st.dataframe(
                broadcaster_calcs.groupby(["recruitment_source", "unit"], as_index=False)["effective_amount"].sum(),
                hide_index=True, width="stretch",
                column_config={"recruitment_source": "Recruitment source", "unit": "Unit",
                               "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f")},
            )
        st.markdown("#### Agency earnings (percentage-method reward plans only)")
        pct_calcs = all_calcs[all_calcs["agency_earnings"].notna()]
        gross = float(pct_calcs["agency_earnings"].sum()) if not pct_calcs.empty else 0.0
        net = float(pct_calcs["net_earnings"].sum()) if not pct_calcs.empty else 0.0
        g1, g2, g3 = st.columns(3)
        g1.metric("Agency gross earnings", f"${gross:,.2f}")
        g2.metric("Reward cost (cash)", f"${(cash_paid + cash_approved):,.2f}")
        g3.metric("Net agency earnings", f"${net:,.2f}")
        st.caption(
            "Agency earnings apply only to 'Percentage/Cash' reward plans - fixed and milestone "
            "plans have no agency-earnings concept, matching the existing Payouts page's formula."
        )
    else:
        st.info("No reward-plan rewards have been calculated yet. Create a plan and assign it under **Reward Plans**.")

elif st.session_state.page == "Payouts":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    pdf_export_enabled = load_pdf_export_enabled(business_id)

    payout_notice = st.session_state.pop("_payout_notice", None)
    if payout_notice:
        st.toast(payout_notice, icon="✅")

    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="overview-hero"><div><div class="overview-eyebrow">Broadcaster rewards</div>
    <h1>Broadcaster Rewards</h1><p>Manage monthly broadcaster rewards and calculate amounts from approved reports.</p>
    </div><div class="overview-period-pill">Monthly reward control</div></div>
    """, unsafe_allow_html=True)
    dashboard_section_control(
        "payout_dashboard",
        ["Monthly Summary", "Reward Rules", "Statements", "History", "Plan-Based Rewards"],
    )

    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.info("Upload and confirm a monthly report to calculate broadcaster payouts.")
        st.stop()

    current_period = st.selectbox("Reporting month", monthly_periods, key="payout_month")
    payout_source = period_data(current_period, "monthly")
    if payout_source.empty:
        st.info("No broadcaster data is available for this reporting month.")
        st.stop()

    payout_source["profile_url"] = payout_source["profile_url"].fillna("").astype(str).str.strip()
    payout_source["broadcaster_name"] = payout_source["broadcaster_name"].fillna("Unnamed broadcaster")
    payout_source["sub_agency"] = payout_source["sub_agency"].fillna("Agency Direct")
    payout_source = payout_source[payout_source["profile_url"] != ""]
    payout_rows = (
        payout_source.groupby("profile_url", as_index=False)
        .agg(
            broadcaster_name=("broadcaster_name", "last"),
            sub_agency=("sub_agency", "last"),
            diamonds_redeemed=("diamonds_redeemed", "sum"),
        )
    )
    payout_rows["redeemed_value"] = payout_rows["diamonds_redeemed"] / DIAMONDS_PER_USD

    effective_rules = load_effective_payout_rules(business_id, current_period)
    if not effective_rules.empty:
        payout_rows = payout_rows.merge(
            effective_rules[["profile_url", "effective_from", "agency_rate_pct", "payout_rate_pct"]],
            on="profile_url", how="left",
        )
    else:
        payout_rows["effective_from"] = None
        payout_rows["agency_rate_pct"] = None
        payout_rows["payout_rate_pct"] = None
    for numeric_column in ("agency_rate_pct", "payout_rate_pct"):
        payout_rows[numeric_column] = pd.to_numeric(payout_rows[numeric_column], errors="coerce")
    payout_rows["agency_earnings"] = (
        payout_rows["redeemed_value"] * payout_rows["agency_rate_pct"] / 100
    )
    payout_rows["amount_payable"] = (
        payout_rows["redeemed_value"] * payout_rows["payout_rate_pct"] / 100
    )
    payout_rows["net_earnings"] = payout_rows["agency_earnings"] - payout_rows["amount_payable"]

    payout_statuses = load_payout_statuses(business_id, current_period)
    if not payout_statuses.empty:
        payout_rows = payout_rows.merge(
            payout_statuses[["profile_url", "status", "paid_at", "paid_by"]],
            on="profile_url", how="left",
        )
    else:
        payout_rows["status"] = None
        payout_rows["paid_at"] = None
        payout_rows["paid_by"] = None
    payout_rows["status"] = payout_rows["status"].fillna("Pending")
    missing_rule = payout_rows["payout_rate_pct"].isna()
    payout_rows.loc[missing_rule, "status"] = "Rate Missing"

    total_redeemed = float(payout_rows["redeemed_value"].sum())
    total_payout = float(payout_rows["amount_payable"].fillna(0).sum())
    total_net = float(payout_rows["net_earnings"].fillna(0).sum())
    pending_count = int((payout_rows["status"] == "Pending").sum())

    payout_summary_panel = dashboard_panel("payout_dashboard", "Monthly Summary")
    payout_summary_panel.__enter__()
    pk1, pk2, pk3, pk4 = st.columns(4)
    with pk1:
        payout_kpi_card("Redeemed Value", f"${total_redeemed:,.2f}", "diamond", f"{current_period} approved report")
    with pk2:
        payout_kpi_card("Broadcaster Rewards", f"${total_payout:,.2f}", "wallet", "Calculated from saved rates")
    with pk3:
        payout_kpi_card("Net Agency Earnings", f"${total_net:,.2f}", "chart", "After broadcaster payouts")
    with pk4:
        payout_kpi_card("Pending Payments", f"{pending_count:,}", "clock", "Ready to be marked paid")

    st.markdown(
        f'<div class="payout-calc-strip">{PAYOUT_ICONS["calculator"]}'
        '<div><strong>Automatic calculation:</strong> Diamonds redeemed ÷ 200 = redeemed value. '
        'Redeemed value × agency rate = agency earnings. Redeemed value × payout rate = amount payable.</div></div>',
        unsafe_allow_html=True,
    )
    if int(missing_rule.sum()):
        st.warning(
            f"{int(missing_rule.sum())} broadcaster(s) need a payout rule before their payment can be finalized."
        )

    table_col, rule_col = st.columns([2.6, 1], gap="large")
    with table_col:
        st.markdown('<div class="payout-section-head"><h2>Monthly Reward Register</h2>'
                    '<p>Review calculated rewards, select pending rows, and record completed payments.</p></div>',
                    unsafe_allow_html=True)
        pf1, pf2 = st.columns([1.5, 1])
        payout_search = pf1.text_input(
            "Search broadcaster", placeholder="Name or Tango profile", key="payout_search"
        )
        status_filter = pf2.selectbox(
            "Payment status", ["All statuses", "Pending", "Paid", "Rate Missing"], key="payout_status_filter"
        )
        payout_view = payout_rows.copy()
        if payout_search.strip():
            payout_needle = payout_search.strip()
            payout_view = payout_view[
                payout_view["broadcaster_name"].str.contains(payout_needle, case=False, na=False)
                | payout_view["profile_url"].str.contains(payout_needle, case=False, na=False)
            ]
        if status_filter != "All statuses":
            payout_view = payout_view[payout_view["status"] == status_filter]
        payout_view = payout_view.sort_values(
            "amount_payable", ascending=False, na_position="last"
        ).reset_index(drop=True)
        payout_view.insert(0, "selected", False)
        editor_columns = [
            "selected", "broadcaster_name", "sub_agency", "diamonds_redeemed", "redeemed_value",
            "agency_rate_pct", "payout_rate_pct", "amount_payable", "net_earnings", "status",
        ]
        edited_payouts = st.data_editor(
            payout_view[editor_columns], hide_index=True, width="stretch", height=390,
            disabled=[column for column in editor_columns if column != "selected"],
            key=f"payout_register_{current_period}",
            column_config={
                "selected": st.column_config.CheckboxColumn("Select", width="small"),
                "broadcaster_name": st.column_config.TextColumn("Broadcaster", width="medium"),
                "sub_agency": st.column_config.TextColumn("Recruitment Source", width="medium"),
                "diamonds_redeemed": st.column_config.NumberColumn("Diamonds Redeemed", format="localized"),
                "redeemed_value": st.column_config.NumberColumn("Redeemed Value", format="$%.2f"),
                "agency_rate_pct": st.column_config.NumberColumn("Agency Rate", format="%.2f%%"),
                "payout_rate_pct": st.column_config.NumberColumn("Payout Rate", format="%.2f%%"),
                "amount_payable": st.column_config.NumberColumn("Amount Payable", format="$%.2f"),
                "net_earnings": st.column_config.NumberColumn("Net Earnings", format="$%.2f"),
                "status": st.column_config.TextColumn("Status", width="small"),
            },
        )
        selected_positions = edited_payouts.index[edited_payouts["selected"]].tolist()
        selected_profiles = payout_view.loc[selected_positions, "profile_url"].tolist()
        ready_profiles = payout_view[
            payout_view["profile_url"].isin(selected_profiles) & (payout_view["status"] == "Pending")
        ]["profile_url"].tolist()
        st.markdown('<div class="payout-status-key"><span>Pending</span><span class="paid">Paid</span>'
                    '<span class="missing">Rate Missing</span></div>', unsafe_allow_html=True)
        action_left, action_right = st.columns([1, 1])
        with action_left:
            if st.button(
                "Mark Selected as Paid", type="primary", width="stretch",
                disabled=not ready_profiles, icon=":material/task_alt:", key="mark_payouts_paid",
            ):
                store.mark_payouts_paid(business_id, current_period, ready_profiles, username)
                store.log_security_event(
                    "payout_marked_paid", username, user_role, business_id,
                    "monthly_payout", current_period,
                    f"profiles={len(ready_profiles)}",
                )
                refresh_caches()
                st.session_state["_payout_notice"] = f"{len(ready_profiles)} payout(s) marked as paid."
                st.rerun()
        with action_right:
            statement_export = payout_rows.copy()
            statement_export.insert(0, "reporting_month", current_period)
            if can_export:
                st.download_button(
                    "Export Statement", utils.safe_csv_bytes(statement_export),
                    file_name=f"broadcaster_payout_statement_{current_period}.csv", mime="text/csv",
                    width="stretch", icon=":material/download:", key="payout_export_summary",
                )
                if pdf_export_enabled and len(statement_export) <= utils.MAX_PDF_ROWS:
                    st.download_button(
                        "Export Statement (PDF)",
                        utils.safe_pdf_bytes(
                            statement_export, "Broadcaster Payout Statement",
                            f"{html.escape(str(business_name))} — {current_period}",
                        ),
                        file_name=f"broadcaster_payout_statement_{current_period}.pdf",
                        mime="application/pdf", width="stretch",
                        icon=":material/download:", key="payout_export_summary_pdf",
                    )

    with rule_col:
        with st.container(border=True):
            st.markdown("### Set Broadcaster Reward")
            st.caption("Rates apply from the selected month onward. Earlier statements stay unchanged.")
            roster = (
                load_all_raw(business_id)
                .sort_values("period")
                .drop_duplicates("profile_url", keep="last")
            )
            roster = roster[roster["profile_url"].fillna("").astype(str).str.strip() != ""]
            roster_labels = {
                row["profile_url"]: f"{row['broadcaster_name']} · {str(row['profile_url']).rstrip('/').split('/')[-1]}"
                for _, row in roster.iterrows()
            }
            selected_profile = st.selectbox(
                "Broadcaster", roster_labels.keys(), format_func=lambda value: roster_labels[value],
                key="payout_rule_profile",
            )
            effective_options = sorted(set(monthly_periods + [dt.date.today().strftime("%Y-%m")]), reverse=True)
            effective_from = st.selectbox("Effective From", effective_options, key="payout_rule_month")
            selected_name = roster_labels[selected_profile].rsplit(" · ", 1)[0]
            saved_rules = load_payout_rules(business_id)
            saved_match = saved_rules[
                (saved_rules["profile_url"] == selected_profile)
                & (saved_rules["effective_from"] == effective_from)
            ] if not saved_rules.empty else pd.DataFrame()
            default_agency_rate = float(saved_match.iloc[0]["agency_rate_pct"]) if not saved_match.empty else 10.0
            default_payout_rate = float(saved_match.iloc[0]["payout_rate_pct"]) if not saved_match.empty else 3.5
            agency_rates = [10.0, 12.5, 15.0, 17.5, 20.0]
            if default_agency_rate not in agency_rates:
                agency_rates.append(default_agency_rate)
                agency_rates.sort()
            agency_rate = st.selectbox(
                "Agency Earning Rate", agency_rates,
                index=agency_rates.index(default_agency_rate), format_func=lambda value: f"{value:g}%",
                key=f"payout_agency_rate_{selected_profile}_{effective_from}",
                help="The percentage this agency earns from the broadcaster's redeemed value.",
            )
            payout_rate = st.number_input(
                "Broadcaster Payout Rate", min_value=0.0, max_value=20.0,
                value=default_payout_rate, step=0.5, format="%.2f",
                key=f"payout_rate_{selected_profile}_{effective_from}",
                help="The percentage paid back to this broadcaster each month.",
            )
            selected_month_row = payout_rows[payout_rows["profile_url"] == selected_profile]
            preview_value = float(selected_month_row.iloc[0]["redeemed_value"]) if not selected_month_row.empty else 0.0
            preview_agency = preview_value * float(agency_rate) / 100
            preview_payout = preview_value * float(payout_rate) / 100
            if payout_rate > agency_rate:
                st.error("Broadcaster payout rate cannot exceed the agency earning rate.")
            st.info(
                f"**{current_period} preview**  \nRedeemed value: **${preview_value:,.2f}**  \n"
                f"Broadcaster payout: **${preview_payout:,.2f}**  \n"
                f"Net Agency earnings: **${preview_agency - preview_payout:,.2f}**"
            )
            if st.button(
                "Save Reward Rule", type="primary", width="stretch",
                icon=":material/save:", key="save_payout_rule",
                disabled=payout_rate > agency_rate,
            ):
                try:
                    store.save_payout_rule(
                        business_id, selected_profile, selected_name, effective_from,
                        agency_rate, payout_rate, username,
                    )
                    store.log_security_event(
                        "payout_rule_saved", username, user_role, business_id,
                        "broadcaster", selected_profile,
                        f"effective_from={effective_from};agency_rate={agency_rate:g};payout_rate={payout_rate:g}",
                    )
                    refresh_caches()
                    st.session_state["_payout_notice"] = f"Payout rule saved for {selected_name}."
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    payout_summary_panel.__exit__(None, None, None)

    payout_rules_panel = dashboard_panel("payout_dashboard", "Reward Rules")
    payout_rules_panel.__enter__()
    st.markdown('<div class="payout-section-head"><h2>Effective-Dated Reward Rules</h2>'
                '<p>Each change starts in its effective month and preserves all earlier calculations.</p></div>',
                unsafe_allow_html=True)
    all_rules = load_payout_rules(business_id)
    if all_rules.empty:
        st.info("No reward rules have been saved yet. Add the first rule from Monthly Summary.")
    else:
        rule_view = all_rules.rename(columns={
            "broadcaster_name": "Broadcaster", "effective_from": "Effective From",
            "agency_rate_pct": "Agency Rate", "payout_rate_pct": "Payout Rate",
            "created_by": "Updated By", "updated_at": "Updated At",
        })
        st.dataframe(
            rule_view[["Broadcaster", "profile_url", "Effective From", "Agency Rate", "Payout Rate", "Updated By", "Updated At"]],
            hide_index=True, width="stretch",
            column_config={
                "profile_url": st.column_config.LinkColumn("Web Profile", display_text="Open profile"),
                "Agency Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Payout Rate": st.column_config.NumberColumn(format="%.2f%%"),
                "Updated At": st.column_config.DatetimeColumn(format="D MMM YYYY, h:mm a"),
            },
        )
    payout_rules_panel.__exit__(None, None, None)

    payout_statements_panel = dashboard_panel("payout_dashboard", "Statements")
    payout_statements_panel.__enter__()
    st.markdown('<div class="payout-section-head"><h2>Monthly Statement</h2>'
                '<p>A complete calculation and payment record for the selected reporting month.</p></div>',
                unsafe_allow_html=True)
    statement_columns = [
        "broadcaster_name", "profile_url", "sub_agency", "diamonds_redeemed", "redeemed_value",
        "agency_rate_pct", "agency_earnings", "payout_rate_pct", "amount_payable", "net_earnings", "status",
    ]
    st.dataframe(
        payout_rows[statement_columns], hide_index=True, width="stretch",
        column_config={
            **table_column_config(["broadcaster_name", "profile_url", "sub_agency", "diamonds_redeemed"]),
            "redeemed_value": st.column_config.NumberColumn("Redeemed Value", format="$%.2f"),
            "agency_rate_pct": st.column_config.NumberColumn("Agency Rate", format="%.2f%%"),
            "agency_earnings": st.column_config.NumberColumn("Agency Earnings", format="$%.2f"),
            "payout_rate_pct": st.column_config.NumberColumn("Payout Rate", format="%.2f%%"),
            "amount_payable": st.column_config.NumberColumn("Amount Payable", format="$%.2f"),
            "net_earnings": st.column_config.NumberColumn("Net Earnings", format="$%.2f"),
            "status": st.column_config.TextColumn("Payment Status"),
        },
    )
    if can_export:
        st.download_button(
            "Download CSV Statement", utils.safe_csv_bytes(payout_rows[statement_columns]),
            file_name=f"broadcaster_payout_statement_{current_period}.csv", mime="text/csv",
            icon=":material/download:", key="payout_export_statement",
        )
        if pdf_export_enabled and len(payout_rows) <= utils.MAX_PDF_ROWS:
            st.download_button(
                "Download PDF Statement",
                utils.safe_pdf_bytes(
                    payout_rows[statement_columns], "Broadcaster Payout Statement",
                    f"{html.escape(str(business_name))} — {current_period}",
                ),
                file_name=f"broadcaster_payout_statement_{current_period}.pdf", mime="application/pdf",
                icon=":material/download:", key="payout_export_statement_pdf",
            )
    payout_statements_panel.__exit__(None, None, None)

    payout_history_panel = dashboard_panel("payout_dashboard", "History")
    payout_history_panel.__enter__()
    st.markdown('<div class="payout-section-head"><h2>Reward Activity History</h2>'
                '<p>Rate changes and payment confirmations recorded for this agency.</p></div>',
                unsafe_allow_html=True)
    payout_audit = load_security_audit(business_id, limit=500)
    if not payout_audit.empty:
        payout_audit = payout_audit[payout_audit["event_type"].isin(["payout_rule_saved", "payout_marked_paid"])]
    if payout_audit.empty:
        st.info("No payout activity has been recorded yet.")
    else:
        history_view = payout_audit.rename(columns={
            "created_at": "Date", "actor_username": "User", "event_type": "Action",
            "target_type": "Record Type", "target_id": "Record", "details": "Details",
        })
        history_view["Action"] = history_view["Action"].map({
            "payout_rule_saved": "Reward rule saved", "payout_marked_paid": "Reward marked paid",
        })
        st.dataframe(
            history_view[["Date", "User", "Action", "Record Type", "Record", "Details"]],
            hide_index=True, width="stretch",
            column_config={"Date": st.column_config.DatetimeColumn(format="D MMM YYYY, h:mm a")},
        )
    payout_history_panel.__exit__(None, None, None)

    # ---- Plan-Based Rewards: the Reward Plan Management System's view of ----
    # ---- calculated broadcaster rewards. Fully additive - reads/writes    ----
    # ---- only reward_calculations/reward_adjustments, never the tables    ----
    # ---- the panels above use.                                           ----
    plan_rewards_panel = dashboard_panel("payout_dashboard", "Plan-Based Rewards")
    plan_rewards_panel.__enter__()
    st.markdown(
        '<div class="payout-section-head"><h2>Configurable Reward Plan Calculations</h2>'
        '<p>Rewards calculated from Reward Plans (percentage, fixed, or milestone-based) - a separate, '
        'parallel system from the reward rules above. Approve, then mark paid; nothing here is ever '
        'auto-approved or auto-paid.</p></div>', unsafe_allow_html=True,
    )
    plan_notice = st.session_state.pop("_plan_rewards_notice", None)
    if plan_notice:
        st.toast(plan_notice, icon="✅")

    pr_calcs = load_reward_calculations(business_id, recipient_type="broadcaster")
    if pr_calcs.empty:
        st.info("No reward-plan calculations yet. Assign a plan to broadcasters under **Reward Plans**.")
    else:
        pr_calcs = pr_calcs.copy()
        pr_calcs["effective_amount"] = pr_calcs["adjusted_amount"].fillna(pr_calcs["calculated_amount"])
        assignments_lookup = load_assignments(business_id)
        source_map = (
            dict(zip(assignments_lookup["profile_url"], assignments_lookup["sub_agency"]))
            if not assignments_lookup.empty else {}
        )
        pr_calcs["recruitment_source"] = pr_calcs["recipient_id"].map(source_map).fillna("Agency Direct")

        pf1, pf2, pf3, pf4, pf5 = st.columns(5)
        pr_period_choice = pf1.selectbox(
            "Period", ["All periods"] + sorted(pr_calcs["period"].unique().tolist(), reverse=True), key="pr_period",
        )
        pr_plan_choice = pf2.selectbox(
            "Plan", ["All plans"] + sorted(pr_calcs["plan_name"].unique().tolist()), key="pr_plan",
        )
        pr_unit_choice = pf3.selectbox("Reward type", ["All", "Cash", "Coins"], key="pr_unit")
        pr_status_choice = pf4.selectbox(
            "Status", ["All"] + list(utils.REWARD_STATUS_TRANSITIONS.keys()), key="pr_status",
        )
        pr_source_choice = pf5.selectbox(
            "Recruitment source", ["All"] + sorted(pr_calcs["recruitment_source"].unique().tolist()), key="pr_source",
        )
        pr_search = st.text_input("Search broadcaster (Tango profile URL)", key="pr_search")

        pr_view = pr_calcs.copy()
        if pr_period_choice != "All periods":
            pr_view = pr_view[pr_view["period"] == pr_period_choice]
        if pr_plan_choice != "All plans":
            pr_view = pr_view[pr_view["plan_name"] == pr_plan_choice]
        if pr_unit_choice != "All":
            pr_view = pr_view[pr_view["unit"] == pr_unit_choice.lower()]
        if pr_status_choice != "All":
            pr_view = pr_view[pr_view["status"] == pr_status_choice]
        if pr_source_choice != "All":
            pr_view = pr_view[pr_view["recruitment_source"] == pr_source_choice]
        if pr_search.strip():
            pr_view = pr_view[pr_view["recipient_id"].str.contains(pr_search.strip(), case=False, na=False)]

        if pr_view["flagged_for_review"].any():
            st.warning(
                f"{int(pr_view['flagged_for_review'].sum())} reward(s) are flagged for review - "
                "their reporting period was re-uploaded with different values since approval/payment."
            )

        display_cols = [
            "period", "recipient_id", "plan_name", "reward_method", "recruitment_source",
            "effective_amount", "unit", "status", "flagged_for_review",
        ]
        pr_view = pr_view.sort_values(["period", "recipient_id"], ascending=[False, True])
        pr_view.insert(0, "selected", False)
        edited_pr = st.data_editor(
            pr_view[["selected"] + display_cols], hide_index=True, width="stretch",
            disabled=display_cols, key=f"pr_editor_{pr_period_choice}_{pr_plan_choice}",
            column_config={
                "selected": st.column_config.CheckboxColumn("Select", width="small"),
                "period": "Period", "recipient_id": st.column_config.LinkColumn("Broadcaster", display_text="Open profile"),
                "plan_name": "Plan", "reward_method": "Method", "recruitment_source": "Recruitment source",
                "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "unit": "Unit", "status": "Status", "flagged_for_review": st.column_config.CheckboxColumn("Flagged"),
            },
        )
        selected_ids = pr_view.loc[edited_pr.index[edited_pr["selected"]], "id"].tolist()
        approvable_ids = pr_view[
            pr_view["id"].isin(selected_ids) & pr_view["status"].isin(["Awaiting Approval", "Milestone Reached"])
        ]["id"].tolist()
        payable_ids = pr_view[pr_view["id"].isin(selected_ids) & (pr_view["status"] == "Approved")]["id"].tolist()

        act1, act2, act3 = st.columns(3)
        with act1:
            bulk_approve_confirm = st.checkbox(
                f"Confirm approval of {len(approvable_ids)} selected", key="pr_bulk_approve_confirm",
                disabled=not approvable_ids,
            )
            if st.button("Bulk Approve", icon=":material/check_circle:", width="stretch",
                         disabled=not (approvable_ids and bulk_approve_confirm), key="pr_bulk_approve"):
                for calc_id in approvable_ids:
                    store.update_reward_status(business_id, int(calc_id), "Approved", username)
                store.log_security_event(
                    "reward_approved", username, user_role, business_id,
                    "reward_calculation", "bulk", f"count={len(approvable_ids)}",
                )
                refresh_reward_plan_caches()
                st.session_state["_plan_rewards_notice"] = f"Approved {len(approvable_ids)} reward(s)."
                st.rerun()
        with act2:
            bulk_pay_confirm = st.checkbox(
                f"Confirm payment of {len(payable_ids)} selected", key="pr_bulk_pay_confirm",
                disabled=not payable_ids,
            )
            if st.button("Bulk Mark Paid", icon=":material/task_alt:", width="stretch",
                         disabled=not (payable_ids and bulk_pay_confirm), key="pr_bulk_pay"):
                for calc_id in payable_ids:
                    store.update_reward_status(business_id, int(calc_id), "Paid", username)
                store.log_security_event(
                    "reward_marked_paid", username, user_role, business_id,
                    "reward_calculation", "bulk", f"count={len(payable_ids)}",
                )
                refresh_reward_plan_caches()
                st.session_state["_plan_rewards_notice"] = f"Marked {len(payable_ids)} reward(s) paid."
                st.rerun()
        with act3:
            if can_export:
                cash_statement = pr_view[pr_view["unit"] == "cash"][display_cols]
                coin_statement = pr_view[pr_view["unit"] == "coins"][display_cols]
                st.download_button(
                    "Download Cash Statement", utils.safe_csv_bytes(cash_statement),
                    file_name="broadcaster_reward_cash_statement.csv", mime="text/csv",
                    width="stretch", icon=":material/download:", key="pr_export_cash",
                )
                st.download_button(
                    "Download Coin Statement", utils.safe_csv_bytes(coin_statement),
                    file_name="broadcaster_reward_coin_statement.csv", mime="text/csv",
                    width="stretch", icon=":material/download:", key="pr_export_coin",
                )

        st.markdown("##### Reject, reverse, or adjust a single reward")
        if not pr_view.empty:
            single_calc_id = st.selectbox(
                "Reward", pr_view["id"].tolist(),
                format_func=lambda cid: f"{pr_view[pr_view['id'] == cid].iloc[0]['recipient_id']} · "
                                         f"{pr_view[pr_view['id'] == cid].iloc[0]['period']} · "
                                         f"{pr_view[pr_view['id'] == cid].iloc[0]['status']}",
                key="pr_single_select",
            )
            single_row = pr_view[pr_view["id"] == single_calc_id].iloc[0]
            with st.container(border=True):
                perf = single_row.get("performance_snapshot") or {}
                cfg = single_row.get("config_snapshot") or {}
                st.caption(
                    f"Calculation explanation: method **{single_row['reward_method']}**, "
                    f"performance used **{perf}**, config used **{cfg}**, "
                    f"result **{single_row['effective_amount']:,.2f} {single_row['unit']}**."
                )
                sc1, sc2 = st.columns(2)
                with sc1:
                    if single_row["status"] == "Awaiting Approval" and st.button(
                        "Reject", icon=":material/cancel:", key=f"pr_reject_{single_calc_id}",
                    ):
                        store.update_reward_status(business_id, int(single_calc_id), "Rejected", username)
                        store.log_security_event("reward_rejected", username, user_role, business_id,
                                                  "reward_calculation", str(single_calc_id))
                        refresh_reward_plan_caches()
                        st.rerun()
                with sc2:
                    reversal_confirm = st.checkbox("Confirm reversal", key=f"pr_reverse_confirm_{single_calc_id}")
                    if single_row["status"] in ("Approved", "Paid") and st.button(
                        "Reverse", icon=":material/undo:", key=f"pr_reverse_{single_calc_id}",
                        disabled=not reversal_confirm,
                    ):
                        reason = f"Reversed by {username}"
                        store.apply_reward_adjustment(business_id, int(single_calc_id), "reversal", reason, 0, username)
                        store.update_reward_status(business_id, int(single_calc_id), "Cancelled", username)
                        store.log_security_event("reward_reversed", username, user_role, business_id,
                                                  "reward_calculation", str(single_calc_id))
                        refresh_reward_plan_caches()
                        st.rerun()

                with st.popover("Add adjustment (bonus / reduction / note)"):
                    adj_type = st.selectbox(
                        "Adjustment type", ["bonus", "reduction", "approve_custom_milestone", "note_only"],
                        format_func=lambda k: k.replace("_", " ").title(), key=f"pr_adj_type_{single_calc_id}",
                    )
                    adj_amount = st.number_input("Adjustment amount", value=0.0, key=f"pr_adj_amount_{single_calc_id}")
                    adj_reason = st.text_area("Reason (required)", key=f"pr_adj_reason_{single_calc_id}")
                    if st.button("Apply adjustment", type="primary", key=f"pr_adj_go_{single_calc_id}"):
                        if not adj_reason.strip():
                            st.error("A reason is required for every adjustment.")
                        else:
                            try:
                                final_amount = store.apply_reward_adjustment(
                                    business_id, int(single_calc_id), adj_type, adj_reason.strip(),
                                    adj_amount, username,
                                )
                                store.log_security_event(
                                    "reward_adjusted", username, user_role, business_id,
                                    "reward_calculation", str(single_calc_id),
                                    f"type={adj_type};final={final_amount}",
                                )
                                refresh_reward_plan_caches()
                                st.toast("Adjustment applied. The original calculated amount is preserved.", icon="✅")
                                st.rerun()
                            except ValueError as error:
                                st.error(str(error))

                past_adjustments = load_reward_adjustments(business_id, int(single_calc_id))
                if not past_adjustments.empty:
                    st.dataframe(past_adjustments, hide_index=True, width="stretch")
    plan_rewards_panel.__exit__(None, None, None)

elif st.session_state.page == "RewardPlans":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    reward_plan_notice = st.session_state.pop("_reward_plan_notice", None)
    if reward_plan_notice:
        st.toast(reward_plan_notice, icon="✅")
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="overview-hero"><div><div class="overview-eyebrow">Configurable rewards</div>
    <h1>Reward Plans</h1><p>Create, configure, and assign broadcaster and recruiter reward plans -
    percentage, fixed, or milestone-based.</p>
    </div><div class="overview-period-pill">Plan library</div></div>
    """, unsafe_allow_html=True)
    dashboard_section_control(
        "reward_plans_dashboard",
        ["Plan Library", "Broadcaster Assignments", "Recruiter Assignments", "Manual Events & Approvals"],
    )

    REWARD_METHOD_LABELS = {
        "percentage_cash": "Percentage / Cash", "fixed_cash": "Fixed Cash", "fixed_coins": "Fixed Coins",
        "diamond_milestone_cash": "Diamond Milestone → Cash", "diamond_milestone_coins": "Diamond Milestone → Coins",
        "custom_milestone_cash": "Custom Milestone → Cash", "custom_milestone_coins": "Custom Milestone → Coins",
        "hybrid": "Hybrid Percentage + Milestone",
    }
    TRIGGER_TYPE_LABELS = {
        "diamonds_redeemed_threshold": "Diamonds redeemed (threshold)",
        "diamonds_earned_threshold": "Diamonds earned (threshold)",
        "signup_completed": "Signup completed", "first_live_completed": "First live completed",
        "streaming_days_target": "Streaming days target", "streaming_hours_target": "Streaming hours target",
        "diamonds_earned_target": "Diamonds earned target", "diamonds_redeemed_target": "Diamonds redeemed target",
        "manual_approval": "Manual approval", "custom": "Custom milestone",
    }
    TIER_MODE_LABELS = {"highest_only": "Highest milestone only", "cumulative": "Cumulative milestones",
                         "incremental_difference": "Incremental difference"}
    FREQUENCY_LABELS = {"lifetime_once": "Once per broadcaster lifetime", "monthly_once": "Once per reporting month",
                         "period_once": "Once per reporting period", "manual_repeatable": "Manually repeatable"}

    # ============================================================ Plan Library
    plan_library_panel = dashboard_panel("reward_plans_dashboard", "Plan Library")
    plan_library_panel.__enter__()
    pl1, pl2 = st.columns(2)
    filter_recipient = pl1.selectbox("Recipient type", ["All", "Broadcaster", "Recruiter"], key="rp_filter_recipient")
    filter_status = pl2.selectbox("Status", ["All", "Draft", "Active", "Archived"], key="rp_filter_status")
    plans_df = load_reward_plans(
        business_id,
        recipient_type=None if filter_recipient == "All" else ("broadcaster" if filter_recipient == "Broadcaster" else "recruiter"),
        status=None if filter_status == "All" else filter_status.lower(),
    )

    with st.expander("Create a new reward plan", icon=":material/add_circle:"):
        with st.form("create_reward_plan_form", clear_on_submit=True):
            new_name = st.text_input("Plan name")
            new_description = st.text_area("Description", height=80)
            new_recipient = st.selectbox("Recipient type", ["Broadcaster", "Recruiter/Sub-Agency"])
            new_method = st.selectbox(
                "Reward method", list(REWARD_METHOD_LABELS.keys()), format_func=lambda k: REWARD_METHOD_LABELS[k],
            )
            if st.form_submit_button("Create plan", type="primary", icon=":material/add:"):
                if not new_name.strip():
                    st.error("Plan name is required.")
                else:
                    recipient_value = "broadcaster" if new_recipient == "Broadcaster" else "recruiter"
                    new_plan_id = store.create_reward_plan(
                        business_id, new_name.strip(), new_description, recipient_value, new_method, username,
                    )
                    store.log_security_event(
                        "reward_plan_created", username, user_role, business_id,
                        "reward_plan", str(new_plan_id), f"name={new_name.strip()};method={new_method}",
                    )
                    refresh_reward_plan_caches()
                    st.session_state["_reward_plan_notice"] = f"Created plan '{new_name.strip()}'."
                    st.session_state["rp_selected_plan"] = new_plan_id
                    st.rerun()

    if plans_df.empty:
        st.info("No reward plans yet. Create one above.")
    else:
        plan_options = dict(zip(plans_df["id"], plans_df["name"] + " (" + plans_df["status"].str.title() + ")"))
        default_plan_id = st.session_state.get("rp_selected_plan", plans_df.iloc[0]["id"])
        if default_plan_id not in plan_options:
            default_plan_id = plans_df.iloc[0]["id"]
        plan_id_list = list(plan_options.keys())
        selected_plan_id = st.selectbox(
            "Select a plan to configure", plan_id_list, format_func=lambda k: plan_options[k],
            index=plan_id_list.index(default_plan_id), key="rp_plan_selector",
        )
        st.session_state["rp_selected_plan"] = selected_plan_id
        plan_row = store.get_reward_plan(business_id, int(selected_plan_id))

        with st.container(border=True):
            top1, top2 = st.columns([3, 1])
            with top1:
                st.markdown(f"### {plan_row['name']}")
                st.caption(plan_row["description"] or "No description.")
                st.markdown(
                    f"**Recipient:** {plan_row['recipient_type'].title()} &nbsp;·&nbsp; "
                    f"**Method:** {REWARD_METHOD_LABELS.get(plan_row['reward_method'], plan_row['reward_method'])} "
                    f"&nbsp;·&nbsp; **Status:** {plan_row['status'].title()}"
                )
            with top2:
                if plan_row["status"] == "draft":
                    if st.button("Activate", type="primary", icon=":material/play_circle:",
                                  key=f"activate_{selected_plan_id}"):
                        store.set_reward_plan_status(business_id, int(selected_plan_id), "active", username)
                        store.log_security_event("reward_plan_activated", username, user_role, business_id,
                                                  "reward_plan", str(selected_plan_id))
                        refresh_reward_plan_caches()
                        st.rerun()
                elif plan_row["status"] == "active":
                    archive_confirm = st.checkbox("Confirm archive", key=f"archive_confirm_{selected_plan_id}")
                    if st.button("Archive", icon=":material/archive:", key=f"archive_{selected_plan_id}",
                                 disabled=not archive_confirm):
                        store.set_reward_plan_status(business_id, int(selected_plan_id), "archived", username)
                        store.log_security_event("reward_plan_archived", username, user_role, business_id,
                                                  "reward_plan", str(selected_plan_id))
                        refresh_reward_plan_caches()
                        st.session_state["_reward_plan_notice"] = (
                            "Plan archived. It stays visible in historical statements but can no longer be newly assigned."
                        )
                        st.rerun()
                else:
                    if st.button("Reactivate as Draft", icon=":material/restore:", key=f"reactivate_{selected_plan_id}"):
                        store.set_reward_plan_status(business_id, int(selected_plan_id), "draft", username)
                        refresh_reward_plan_caches()
                        st.rerun()
                with st.popover("Duplicate"):
                    dup_name = st.text_input(
                        "New plan name", value=f"{plan_row['name']} (Copy)", key=f"dup_name_{selected_plan_id}",
                    )
                    if st.button("Duplicate plan", type="primary", key=f"dup_go_{selected_plan_id}"):
                        new_id = store.duplicate_reward_plan(business_id, int(selected_plan_id), dup_name.strip(), username)
                        store.log_security_event("reward_plan_duplicated", username, user_role, business_id,
                                                  "reward_plan", str(new_id), f"source={selected_plan_id}")
                        refresh_reward_plan_caches()
                        st.session_state["rp_selected_plan"] = new_id
                        st.session_state["_reward_plan_notice"] = f"Duplicated as '{dup_name.strip()}'."
                        st.rerun()

            if plan_row["recipient_type"] == "broadcaster":
                using = load_broadcaster_assignments(business_id)
                using = using[using["plan_id"] == int(selected_plan_id)] if not using.empty else using
                st.caption(f"Assigned to **{using['profile_url'].nunique() if not using.empty else 0}** broadcaster(s).")
            else:
                using_default = load_recruiter_assignments(business_id)
                using_default = using_default[using_default["plan_id"] == int(selected_plan_id)] if not using_default.empty else using_default
                using_override = load_recruiter_overrides(business_id)
                using_override = using_override[using_override["plan_id"] == int(selected_plan_id)] if not using_override.empty else using_override
                st.caption(
                    f"Default plan for **{using_default['agency_name'].nunique() if not using_default.empty else 0}** "
                    f"recruiter(s), override for **{using_override['profile_url'].nunique() if not using_override.empty else 0}** broadcaster(s)."
                )

        with st.container(border=True):
            st.markdown("#### Configure")
            latest_version = store.get_latest_plan_version(business_id, int(selected_plan_id))
            existing_config = dict(latest_version["config"]) if latest_version is not None else {}
            default_effective_from = dt.date.today().strftime("%Y-%m")
            cfg1, cfg2 = st.columns(2)
            effective_from_input = cfg1.text_input(
                "Effective from (YYYY-MM)",
                value=latest_version["effective_from"] if latest_version is not None else default_effective_from,
                key=f"cfg_from_{selected_plan_id}",
            )
            effective_to_input = cfg2.text_input(
                "Optional end month (YYYY-MM)",
                value=(latest_version["effective_to"] or "") if latest_version is not None else "",
                key=f"cfg_to_{selected_plan_id}",
            )

            milestones_state_key = f"rp_milestones_{selected_plan_id}"
            if plan_row["reward_method"] == "percentage_cash":
                pc1, pc2 = st.columns(2)
                agency_pct = pc1.number_input(
                    "Agency earning percentage", min_value=0.0, max_value=100.0,
                    value=float(existing_config.get("agency_pct", 15.0)), step=0.5,
                    key=f"agency_pct_{selected_plan_id}",
                )
                payout_pct = pc2.number_input(
                    "Broadcaster/Recruiter payout percentage", min_value=0.0, max_value=100.0,
                    value=float(existing_config.get("payout_pct", 10.0)), step=0.5,
                    key=f"payout_pct_{selected_plan_id}",
                )
                if payout_pct > agency_pct:
                    st.error("Payout percentage cannot exceed the agency earning percentage.")
                pc3, pc4, pc5 = st.columns(3)
                currency = pc3.text_input("Currency", value=existing_config.get("currency", "USD"),
                                           key=f"currency_{selected_plan_id}")
                min_diamonds = pc4.number_input(
                    "Optional minimum diamonds", min_value=0.0,
                    value=float(existing_config.get("min_diamonds", 0.0)), key=f"min_diamonds_{selected_plan_id}",
                )
                has_cap = pc5.checkbox(
                    "Set a maximum monthly payout", value=existing_config.get("max_monthly_payout") is not None,
                    key=f"has_cap_{selected_plan_id}",
                )
                max_payout = st.number_input(
                    "Maximum monthly payout", min_value=0.0,
                    value=float(existing_config.get("max_monthly_payout") or 0.0), key=f"max_payout_{selected_plan_id}",
                ) if has_cap else None
                config_to_save = {"agency_pct": agency_pct, "payout_pct": payout_pct, "currency": currency,
                                   "min_diamonds": min_diamonds, "max_monthly_payout": max_payout}
                tier_mode_to_save, frequency_to_save, milestones_to_save = None, None, []
            elif plan_row["reward_method"] in ("fixed_cash", "fixed_coins"):
                fixed_amount = st.number_input(
                    "Fixed reward amount", min_value=0.0,
                    value=float(existing_config.get("fixed_amount", 0.0)), key=f"fixed_amount_{selected_plan_id}",
                )
                config_to_save = {"fixed_amount": fixed_amount}
                tier_mode_to_save, frequency_to_save, milestones_to_save = None, "monthly_once", []
            else:
                mc1, mc2 = st.columns(2)
                tier_mode_keys = list(TIER_MODE_LABELS.keys())
                default_tier_mode = (
                    latest_version["tier_calculation_mode"]
                    if latest_version is not None and latest_version["tier_calculation_mode"] else "highest_only"
                )
                tier_mode_to_save = mc1.selectbox(
                    "Tier calculation", tier_mode_keys, format_func=lambda k: TIER_MODE_LABELS[k],
                    index=tier_mode_keys.index(default_tier_mode), key=f"tier_mode_{selected_plan_id}",
                )
                frequency_keys = list(FREQUENCY_LABELS.keys())
                default_frequency = (
                    latest_version["frequency"] if latest_version is not None and latest_version["frequency"] else "lifetime_once"
                )
                frequency_to_save = mc2.selectbox(
                    "Frequency", frequency_keys, format_func=lambda k: FREQUENCY_LABELS[k],
                    index=frequency_keys.index(default_frequency), key=f"frequency_{selected_plan_id}",
                )
                basis = st.selectbox(
                    "Milestone basis", ["diamonds_redeemed", "diamonds_earned"],
                    index=0 if existing_config.get("milestone_basis", "diamonds_redeemed") == "diamonds_redeemed" else 1,
                    format_func=lambda v: v.replace("_", " ").title(), key=f"basis_{selected_plan_id}",
                )
                has_plan_cap = st.checkbox(
                    "Set a plan-level reward cap", value=existing_config.get("plan_cap") is not None,
                    key=f"has_plan_cap_{selected_plan_id}",
                )
                plan_cap = st.number_input(
                    "Plan-level reward cap", min_value=0.0,
                    value=float(existing_config.get("plan_cap") or 0.0), key=f"plan_cap_{selected_plan_id}",
                ) if has_plan_cap else None
                config_to_save = {"milestone_basis": basis, "plan_cap": plan_cap}

                st.markdown("##### Milestones")
                st.caption("Add, edit, or remove rows below. The Order column controls evaluation order.")
                if milestones_state_key not in st.session_state:
                    if latest_version is not None:
                        existing_milestones = store.get_plan_milestones(business_id, int(latest_version["id"]))
                        st.session_state[milestones_state_key] = (
                            existing_milestones.to_dict("records") if not existing_milestones.empty else []
                        )
                    else:
                        st.session_state[milestones_state_key] = []
                editable_cols = ["order_index", "name", "trigger_type", "threshold", "reward_value", "unit",
                                  "requires_manual_approval", "max_total_reward_per_broadcaster", "frequency"]
                milestone_editor_df = pd.DataFrame(st.session_state[milestones_state_key])
                for col in editable_cols:
                    if col not in milestone_editor_df.columns:
                        milestone_editor_df[col] = None
                edited_milestones = st.data_editor(
                    milestone_editor_df[editable_cols], num_rows="dynamic", hide_index=True, width="stretch",
                    key=f"milestone_editor_{selected_plan_id}",
                    column_config={
                        "order_index": st.column_config.NumberColumn("Order", help="Lower numbers evaluate first."),
                        "name": st.column_config.TextColumn("Milestone name"),
                        "trigger_type": st.column_config.SelectboxColumn("Trigger type", options=list(TRIGGER_TYPE_LABELS.keys())),
                        "threshold": st.column_config.NumberColumn("Threshold"),
                        "reward_value": st.column_config.NumberColumn("Reward value"),
                        "unit": st.column_config.SelectboxColumn("Unit", options=["cash", "coins"]),
                        "requires_manual_approval": st.column_config.CheckboxColumn("Manual approval?"),
                        "max_total_reward_per_broadcaster": st.column_config.NumberColumn("Max total reward"),
                        "frequency": st.column_config.SelectboxColumn("Repeatability", options=list(FREQUENCY_LABELS.keys())),
                    },
                )
                st.session_state[milestones_state_key] = edited_milestones.to_dict("records")

                sorted_edited = edited_milestones.sort_values("order_index", na_position="last").to_dict("records")
                milestones_to_save = [
                    row for row in sorted_edited
                    if row.get("threshold") is not None and row.get("unit") in ("cash", "coins")
                    and row.get("reward_value") is not None
                ]

                st.markdown("##### Preview")
                preview_value = st.number_input(
                    f"Preview at this {basis.replace('_', ' ')} total", min_value=0.0, value=60000.0,
                    key=f"preview_value_{selected_plan_id}",
                )
                preview_milestones = [
                    {**row, "milestone_key": row.get("milestone_key") or f"preview_{i}"}
                    for i, row in enumerate(milestones_to_save)
                ]
                if preview_milestones:
                    preview_result = utils.calculate_milestone_reward(
                        preview_value, preview_milestones, tier_mode_to_save, frequency_to_save, set(),
                    )
                    st.info(
                        f"At **{preview_value:,.0f} {basis.replace('_', ' ')}**: "
                        f"**${preview_result['total_cash']:,.2f}** cash, "
                        f"**{preview_result['total_coins']:,.0f}** coins."
                    )
                else:
                    st.caption("Add at least one milestone with a threshold, reward value, and unit to preview.")

            if st.button("Save configuration", type="primary", icon=":material/save:", key=f"save_cfg_{selected_plan_id}"):
                try:
                    store.save_reward_plan_version(
                        business_id, int(selected_plan_id), effective_from_input.strip(),
                        effective_to_input.strip() or None, config_to_save, tier_mode_to_save,
                        frequency_to_save, milestones_to_save, username,
                    )
                    store.log_security_event(
                        "reward_plan_edited", username, user_role, business_id,
                        "reward_plan", str(selected_plan_id), f"effective_from={effective_from_input.strip()}",
                    )
                    refresh_reward_plan_caches()
                    st.session_state.pop(milestones_state_key, None)
                    st.session_state["_reward_plan_notice"] = "Reward plan configuration saved."
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    plan_library_panel.__exit__(None, None, None)

    # =================================================== Broadcaster Assignments
    broadcaster_assign_panel = dashboard_panel("reward_plans_dashboard", "Broadcaster Assignments")
    broadcaster_assign_panel.__enter__()
    st.markdown("#### Assign a Reward Plan to Broadcasters")
    active_broadcaster_plans = load_reward_plans(business_id, recipient_type="broadcaster", status="active")
    ba_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if active_broadcaster_plans.empty:
        st.info("Activate a broadcaster reward plan first (Plan Library tab).")
    elif not ba_periods:
        st.info("Upload a monthly report first.")
    else:
        ba_period = st.selectbox("Reporting month", ba_periods, key="ba_period")
        roster_all = (
            load_all_raw(business_id).sort_values("period").drop_duplicates("profile_url", keep="last")
        )
        roster_all = roster_all[roster_all["profile_url"].fillna("").astype(str).str.strip() != ""]
        effective_assignments = load_effective_broadcaster_assignments(business_id, ba_period)

        af1, af2 = st.columns(2)
        plan_filter_options = ["All plans", "Without a plan"] + active_broadcaster_plans["name"].tolist()
        plan_filter = af1.selectbox("Filter by plan", plan_filter_options, key="ba_plan_filter")
        search_text = af2.text_input("Search broadcaster", key="ba_search")

        directory = roster_all[["profile_url", "broadcaster_name"]].copy()
        if not effective_assignments.empty:
            directory = directory.merge(
                effective_assignments[["profile_url", "plan_name", "reward_method"]], on="profile_url", how="left",
            )
        else:
            directory["plan_name"] = None
            directory["reward_method"] = None
        if plan_filter == "Without a plan":
            directory = directory[directory["plan_name"].isna()]
        elif plan_filter != "All plans":
            directory = directory[directory["plan_name"] == plan_filter]
        if search_text.strip():
            needle = search_text.strip()
            directory = directory[
                directory["broadcaster_name"].str.contains(needle, case=False, na=False)
                | directory["profile_url"].str.contains(needle, case=False, na=False)
            ]
        st.dataframe(
            directory, hide_index=True, width="stretch",
            column_config={
                "broadcaster_name": "Broadcaster",
                "profile_url": st.column_config.LinkColumn("Profile", display_text="Open"),
                "plan_name": "Current plan", "reward_method": "Method",
            },
        )

        st.markdown("##### Bulk assign")
        name_lookup = dict(zip(directory["profile_url"], directory["broadcaster_name"]))
        bulk_targets = st.multiselect(
            "Broadcasters", directory["profile_url"].tolist(),
            format_func=lambda u: name_lookup.get(u, u), key="ba_bulk_targets",
        )
        bplan_options = dict(zip(active_broadcaster_plans["id"], active_broadcaster_plans["name"]))
        bplan_ids = list(bplan_options.keys())
        bplan_choice = st.selectbox("Reward plan", bplan_ids, format_func=lambda k: bplan_options[k], key="ba_bulk_plan")
        beff1, beff2 = st.columns(2)
        bulk_from = beff1.text_input("Effective from (YYYY-MM)", value=ba_period, key="ba_bulk_from")
        bulk_to = beff2.text_input("Optional end month", key="ba_bulk_to")
        if st.button("Assign selected", type="primary", disabled=not bulk_targets, key="ba_bulk_go"):
            succeeded, failed = store.bulk_assign_broadcasters_to_plan(
                business_id, bulk_targets, int(bplan_choice), bulk_from.strip(), bulk_to.strip() or None, username,
            )
            store.log_security_event(
                "reward_plan_assigned", username, user_role, business_id,
                "reward_plan", str(bplan_choice), f"broadcasters={len(succeeded)};failed={len(failed)}",
            )
            refresh_reward_plan_caches()
            if failed:
                st.warning(
                    f"Assigned {len(succeeded)}; {len(failed)} could not be assigned: "
                    + "; ".join(f"{p}: {e}" for p, e in failed[:5])
                )
            else:
                st.session_state["_reward_plan_notice"] = f"Assigned {len(succeeded)} broadcaster(s)."
            st.rerun()

        st.markdown("##### Assignment history / remove a future assignment")
        if not roster_all.empty:
            history_choice = st.selectbox(
                "Broadcaster", roster_all["profile_url"].tolist(),
                format_func=lambda u: name_lookup.get(u, u), key="ba_history_target",
            )
            history_df = load_broadcaster_assignments(business_id, history_choice)
            if history_df.empty:
                st.caption("No assignment history for this broadcaster.")
            else:
                st.dataframe(history_df, hide_index=True, width="stretch")
                future_rows = history_df[history_df["effective_from"] > ba_period]
                if not future_rows.empty:
                    future_ids = future_rows["id"].tolist()
                    remove_choice = st.selectbox(
                        "Remove a future assignment", future_ids,
                        format_func=lambda rid: (
                            f"{future_rows[future_rows['id'] == rid].iloc[0]['plan_name']} "
                            f"from {future_rows[future_rows['id'] == rid].iloc[0]['effective_from']}"
                        ),
                        key="ba_remove_choice",
                    )
                    if st.button("Remove this future assignment", key="ba_remove_go"):
                        try:
                            store.remove_future_assignment(
                                "broadcaster_reward_assignments", business_id, int(remove_choice), ba_period,
                            )
                            refresh_reward_plan_caches()
                            st.toast("Future assignment removed.", icon="✅")
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
    broadcaster_assign_panel.__exit__(None, None, None)

    # ===================================================== Recruiter Assignments
    recruiter_assign_panel = dashboard_panel("reward_plans_dashboard", "Recruiter Assignments")
    recruiter_assign_panel.__enter__()
    st.markdown("#### Default Reward Plan per Recruiter")
    active_recruiter_plans = load_reward_plans(business_id, recipient_type="recruiter", status="active")
    ra_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    ra_period = st.selectbox("Reporting month", ra_periods or [dt.date.today().strftime("%Y-%m")], key="ra_period")
    agencies_list = load_agencies(business_id)
    if active_recruiter_plans.empty:
        st.info("Activate a recruiter reward plan first (Plan Library tab).")
    elif not agencies_list:
        st.info("No recruiters/Sub-Agencies exist yet.")
    else:
        effective_recruiter = load_effective_recruiter_assignments(business_id, ra_period)
        assigned_agencies = set(effective_recruiter["agency_name"]) if not effective_recruiter.empty else set()
        without_plan = [a for a in agencies_list if a not in assigned_agencies]
        if without_plan:
            st.warning(f"{len(without_plan)} recruiter(s) without a default plan: {', '.join(without_plan)}")
        rplan_options = dict(zip(active_recruiter_plans["id"], active_recruiter_plans["name"]))
        rplan_ids = list(rplan_options.keys())
        r1, r2, r3 = st.columns(3)
        target_agency = r1.selectbox("Recruiter", agencies_list, key="ra_target_agency")
        target_plan = r2.selectbox("Reward plan", rplan_ids, format_func=lambda k: rplan_options[k], key="ra_target_plan")
        target_from = r3.text_input("Effective from (YYYY-MM)", value=ra_period, key="ra_target_from")
        if st.button("Set default plan", type="primary", key="ra_set_default"):
            try:
                store.assign_recruiter_default_plan(
                    business_id, target_agency, int(target_plan), target_from.strip(), None, username,
                )
                store.log_security_event(
                    "reward_plan_assigned", username, user_role, business_id,
                    "recruiter", target_agency, f"plan={target_plan}",
                )
                refresh_reward_plan_caches()
                st.toast(f"Default plan set for {target_agency}.", icon="✅")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        st.dataframe(load_recruiter_assignments(business_id), hide_index=True, width="stretch")

        st.markdown("#### Broadcaster-Level Override")
        override_agency = st.selectbox("Recruiter", agencies_list, key="ra_override_agency")
        roster_assignments = load_assignments(business_id)
        roster_for_agency = (
            roster_assignments[roster_assignments["sub_agency"] == override_agency]
            if not roster_assignments.empty else pd.DataFrame()
        )
        if roster_for_agency.empty:
            st.caption("This recruiter has no recruited broadcasters yet.")
        else:
            override_name_lookup = dict(zip(roster_for_agency["profile_url"], roster_for_agency["broadcaster_name"]))
            override_profile = st.selectbox(
                "Broadcaster", roster_for_agency["profile_url"].tolist(),
                format_func=lambda u: override_name_lookup.get(u, u), key="ra_override_profile",
            )
            o1, o2, o3 = st.columns(3)
            override_plan = o1.selectbox("Reward plan", rplan_ids, format_func=lambda k: rplan_options[k], key="ra_override_plan")
            override_from = o2.text_input("Effective from (YYYY-MM)", value=ra_period, key="ra_override_from")
            with o3:
                st.write("")
                st.write("")
                if st.button("Set override", type="primary", key="ra_override_go"):
                    try:
                        store.assign_recruiter_broadcaster_override(
                            business_id, override_agency, override_profile, int(override_plan),
                            override_from.strip(), None, username,
                        )
                        store.log_security_event(
                            "reward_plan_assigned", username, user_role, business_id,
                            "recruiter_override", override_profile, f"agency={override_agency};plan={override_plan}",
                        )
                        refresh_reward_plan_caches()
                        st.toast("Override set.", icon="✅")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
        st.dataframe(load_recruiter_overrides(business_id), hide_index=True, width="stretch")
    recruiter_assign_panel.__exit__(None, None, None)

    # ================================================ Manual Events & Approvals
    manual_events_panel = dashboard_panel("reward_plans_dashboard", "Manual Events & Approvals")
    manual_events_panel.__enter__()
    st.markdown("#### Record a Manual Milestone Event")
    st.caption("Use this for milestones the monthly CSV can't prove, like signup completed or first live completed.")
    me1, me2, me3 = st.columns(3)
    me_recipient_type = me1.selectbox("Recipient type", ["Broadcaster", "Recruiter"], key="me_recipient_type")
    me_recipient_id, me_related_profile = None, None
    if me_recipient_type == "Broadcaster":
        me_roster = load_all_raw(business_id).sort_values("period").drop_duplicates("profile_url", keep="last")
        me_roster = me_roster[me_roster["profile_url"].fillna("").astype(str).str.strip() != ""]
        if not me_roster.empty:
            me_name_lookup = dict(zip(me_roster["profile_url"], me_roster["broadcaster_name"]))
            me_recipient_id = me2.selectbox(
                "Broadcaster", me_roster["profile_url"].tolist(),
                format_func=lambda u: me_name_lookup.get(u, u), key="me_recipient_broadcaster",
            )
    else:
        me_agencies = load_agencies(business_id)
        if me_agencies:
            me_recipient_id = me2.selectbox("Recruiter", me_agencies, key="me_recipient_agency")
            me_roster_assignments = load_assignments(business_id)
            me_roster_for_agency = (
                me_roster_assignments[me_roster_assignments["sub_agency"] == me_recipient_id]
                if not me_roster_assignments.empty else pd.DataFrame()
            )
            if not me_roster_for_agency.empty:
                me_related_lookup = dict(zip(me_roster_for_agency["profile_url"], me_roster_for_agency["broadcaster_name"]))
                me_related_profile = st.selectbox(
                    "Recruited broadcaster", me_roster_for_agency["profile_url"].tolist(),
                    format_func=lambda u: me_related_lookup.get(u, u), key="me_related_profile",
                )
    me_trigger = me3.selectbox(
        "Milestone", ["signup_completed", "first_live_completed", "manual_approval", "custom"],
        format_func=lambda k: TRIGGER_TYPE_LABELS.get(k, k), key="me_trigger_type",
    )
    me4, me5 = st.columns(2)
    me_event_date = me4.date_input("Event date", value=dt.date.today(), key="me_event_date")
    me_notes = me5.text_input("Notes", key="me_notes")
    if st.button("Record event", type="primary", disabled=not me_recipient_id, key="me_record"):
        store.create_manual_milestone_event(
            business_id, me_recipient_type.lower(), me_recipient_id, me_related_profile,
            me_trigger, me_event_date, me_notes, username,
        )
        store.log_security_event(
            "manual_milestone_recorded", username, user_role, business_id,
            me_recipient_type.lower(), str(me_recipient_id), me_trigger,
        )
        refresh_reward_plan_caches()
        st.toast("Manual milestone event recorded - pending approval below.", icon="✅")
        st.rerun()

    st.markdown("#### Pending Approvals")
    pending_events = load_manual_milestone_events(business_id, status="Pending")
    if pending_events.empty:
        st.info("No manual milestone events awaiting approval.")
    else:
        for _, event in pending_events.iterrows():
            with st.container(border=True):
                st.markdown(
                    f"**{TRIGGER_TYPE_LABELS.get(event['trigger_type'], event['trigger_type'])}** "
                    f"for **{event['recipient_id']}** on {event['event_date']}"
                )
                if event["notes"]:
                    st.caption(event["notes"])
                ce1, ce2 = st.columns(2)
                if ce1.button("Approve", type="primary", icon=":material/check:", key=f"me_approve_{event['id']}"):
                    store.confirm_manual_milestone_event(business_id, int(event["id"]), True, username)
                    store.log_security_event(
                        "manual_milestone_confirmed", username, user_role, business_id,
                        "manual_milestone_event", str(event["id"]), "approved",
                    )
                    refresh_reward_plan_caches()
                    st.rerun()
                if ce2.button("Reject", icon=":material/close:", key=f"me_reject_{event['id']}"):
                    store.confirm_manual_milestone_event(business_id, int(event["id"]), False, username)
                    store.log_security_event(
                        "manual_milestone_confirmed", username, user_role, business_id,
                        "manual_milestone_event", str(event["id"]), "rejected",
                    )
                    refresh_reward_plan_caches()
                    st.rerun()

    st.markdown("#### All Manual Events")
    all_events = load_manual_milestone_events(business_id)
    if not all_events.empty:
        st.dataframe(all_events, hide_index=True, width="stretch")
    manual_events_panel.__exit__(None, None, None)

elif st.session_state.page == "RecruiterRewards":
    if not (is_owner or is_sub_agency):
        st.error("Access denied.")
        st.stop()
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="overview-hero"><div><div class="overview-eyebrow">Recruiter rewards</div>
    <h1>{"Recruiter Rewards" if is_owner else "My Rewards"}</h1>
    <p>Milestone and percentage-based reward progress for {"every recruiter" if is_owner else "your recruited broadcasters"}.</p>
    </div><div class="overview-period-pill">Configurable reward plans</div></div>
    """, unsafe_allow_html=True)

    rr_calcs = load_reward_calculations(business_id, recipient_type="recruiter")
    if not is_owner:
        # Sub-Agency users see only their own roster and rewards (req #12/#17)
        # - no agency-wide totals, no other recruiter's data.
        rr_calcs = rr_calcs[rr_calcs["recipient_id"] == user_agency] if not rr_calcs.empty else rr_calcs

    if rr_calcs.empty:
        st.info(
            "No recruiter reward-plan calculations yet."
            if is_owner else "No reward-plan calculations yet for your roster."
        )
        st.stop()

    rr_calcs = rr_calcs.copy()
    rr_calcs["effective_amount"] = rr_calcs["adjusted_amount"].fillna(rr_calcs["calculated_amount"])

    if is_owner:
        recruiter_choice = st.selectbox(
            "Recruiter", ["All"] + sorted(rr_calcs["recipient_id"].unique().tolist()), key="rr_recruiter_choice",
        )
        if recruiter_choice != "All":
            rr_calcs = rr_calcs[rr_calcs["recipient_id"] == recruiter_choice]

    cash_earned = float(rr_calcs[rr_calcs["unit"] == "cash"]["effective_amount"].sum())
    coins_earned = float(rr_calcs[rr_calcs["unit"] == "coins"]["effective_amount"].sum())
    pending_amt = rr_calcs[rr_calcs["status"] == "Awaiting Approval"]
    approved_amt = rr_calcs[rr_calcs["status"] == "Approved"]
    paid_amt = rr_calcs[rr_calcs["status"] == "Paid"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cash earned", f"${cash_earned:,.2f}")
    m2.metric("Coins earned", f"{coins_earned:,.0f}")
    m3.metric("Pending approval", len(pending_amt))
    m4.metric("Paid rewards", len(paid_amt))
    st.caption("Cash and coin rewards are always shown separately.")

    st.markdown("#### Per-Broadcaster Breakdown")
    breakdown = rr_calcs.groupby(
        ["recipient_id", "related_profile_url", "unit"], as_index=False,
    )["effective_amount"].sum()
    st.dataframe(
        breakdown, hide_index=True, width="stretch",
        column_config={
            "recipient_id": "Recruiter", "related_profile_url": st.column_config.LinkColumn("Broadcaster", display_text="Open profile"),
            "unit": "Unit", "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f"),
        },
    )

    st.markdown("#### Reward Detail")
    detail_cols = ["period", "recipient_id", "related_profile_url", "plan_name", "reward_method",
                   "effective_amount", "unit", "status"]
    st.dataframe(
        rr_calcs[detail_cols].sort_values("period", ascending=False), hide_index=True, width="stretch",
        column_config={
            "period": "Period", "recipient_id": "Recruiter",
            "related_profile_url": st.column_config.LinkColumn("Broadcaster", display_text="Open profile"),
            "plan_name": "Plan", "reward_method": "Method",
            "effective_amount": st.column_config.NumberColumn("Amount", format="%.2f"), "unit": "Unit", "status": "Status",
        },
    )
    if can_export:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.download_button(
                "Download Cash Statement", utils.safe_csv_bytes(rr_calcs[rr_calcs["unit"] == "cash"][detail_cols]),
                file_name="recruiter_reward_cash_statement.csv", mime="text/csv", width="stretch",
                icon=":material/download:", key="rr_export_cash",
            )
        with cc2:
            st.download_button(
                "Download Coin Statement", utils.safe_csv_bytes(rr_calcs[rr_calcs["unit"] == "coins"][detail_cols]),
                file_name="recruiter_reward_coin_statement.csv", mime="text/csv", width="stretch",
                icon=":material/download:", key="rr_export_coin",
            )

    if is_owner:
        st.markdown("#### Approve / Mark Paid")
        rr_calcs_view = rr_calcs.copy()
        rr_calcs_view.insert(0, "selected", False)
        edited_rr = st.data_editor(
            rr_calcs_view[["selected"] + detail_cols], hide_index=True, width="stretch",
            disabled=detail_cols, key="rr_editor",
            column_config={"selected": st.column_config.CheckboxColumn("Select", width="small")},
        )
        rr_selected_ids = rr_calcs_view.loc[edited_rr.index[edited_rr["selected"]], "id"].tolist()
        rr_approvable = rr_calcs_view[
            rr_calcs_view["id"].isin(rr_selected_ids) & rr_calcs_view["status"].isin(["Awaiting Approval", "Milestone Reached"])
        ]["id"].tolist()
        rr_payable = rr_calcs_view[rr_calcs_view["id"].isin(rr_selected_ids) & (rr_calcs_view["status"] == "Approved")]["id"].tolist()
        rrb1, rrb2 = st.columns(2)
        with rrb1:
            rr_approve_confirm = st.checkbox(f"Confirm approval of {len(rr_approvable)} selected", key="rr_approve_confirm",
                                              disabled=not rr_approvable)
            if st.button("Bulk Approve", icon=":material/check_circle:", width="stretch",
                         disabled=not (rr_approvable and rr_approve_confirm), key="rr_bulk_approve"):
                for calc_id in rr_approvable:
                    store.update_reward_status(business_id, int(calc_id), "Approved", username)
                store.log_security_event("reward_approved", username, user_role, business_id,
                                          "reward_calculation", "bulk_recruiter", f"count={len(rr_approvable)}")
                refresh_reward_plan_caches()
                st.rerun()
        with rrb2:
            rr_pay_confirm = st.checkbox(f"Confirm payment of {len(rr_payable)} selected", key="rr_pay_confirm",
                                          disabled=not rr_payable)
            if st.button("Bulk Mark Paid", icon=":material/task_alt:", width="stretch",
                         disabled=not (rr_payable and rr_pay_confirm), key="rr_bulk_pay"):
                for calc_id in rr_payable:
                    store.update_reward_status(business_id, int(calc_id), "Paid", username)
                store.log_security_event("reward_marked_paid", username, user_role, business_id,
                                          "reward_calculation", "bulk_recruiter", f"count={len(rr_payable)}")
                refresh_reward_plan_caches()
                st.rerun()

# =============================================================== BROADCASTERS
elif st.session_state.page == "Broadcasters":
    st.title("Broadcasters" if can_view_full_tenant else "My Broadcasters")
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="bl_month")
    force = None if can_view_full_tenant else user_agency
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
        agency_pick = st.selectbox("Recruitment source", ["All", "Agency Direct"] + load_agencies(business_id), key="bl_agency") \
            if can_view_full_tenant else "All"
    with col2:
        status_pick = st.multiselect("Status", sorted(df["status"].dropna().unique().tolist()), key="bl_status")

    view = df.copy()
    if search:
        view = view[view["broadcaster_name"].str.contains(search, case=False, na=False)]
    if can_view_full_tenant and agency_pick != "All":
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

    broadcaster_label = "broadcaster" if len(view) == 1 else "broadcasters"
    st.caption(f"{len(view)} {broadcaster_label}")
    show_cols = ["broadcaster_name", "sub_agency", "status", "diamonds_redeemed",
                 "streaming_days", "diamonds_per_day", "growth_pct"] if can_view_full_tenant else \
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
        if is_broadcaster:
            st.error("Your broadcaster profile isn't linked correctly. Contact your agency.")
        else:
            st.info("Pick a broadcaster from the Broadcasters list first.")
            if st.button("Go to broadcasters"):
                st.session_state.page = "Broadcasters"
                st.rerun()
        st.stop()

    # A Broadcaster is scoped to exactly one profile_url (memberships.profile_url,
    # set at grant time) - defense in depth alongside the auto-set on login,
    # in case session state were ever manipulated to point somewhere else.
    if is_broadcaster and profile_url != user_profile_url:
        st.error("You don't have access to this broadcaster.")
        st.stop()

    raw = load_all_raw(business_id)
    hist = raw[(raw["profile_url"] == profile_url) & (raw["period_type"] == "monthly")].sort_values("period") \
        if not raw.empty else raw
    if hist.empty:
        st.warning("No data found for this broadcaster.")
        st.stop()

    assignments = load_assignments(business_id)
    a_row = assignments[assignments["profile_url"] == profile_url] if not assignments.empty else assignments
    sub_agency = a_row.iloc[0]["sub_agency"] if not a_row.empty else "Agency Direct"

    if not is_broadcaster and not can_view_full_tenant and sub_agency != user_agency:
        st.error("You don't have access to this broadcaster.")
        st.stop()

    if not is_broadcaster:
        if st.button("\u2190 Back to broadcasters"):
            st.session_state.page = "Broadcasters"
            st.rerun()

    latest = hist.iloc[-1]
    prev = hist.iloc[-2] if len(hist) > 1 else None

    st.title(latest["broadcaster_name"])
    st.caption(f"{profile_url}  \u00b7  {sub_agency}")
    st.link_button("Open Tango profile", profile_url, icon=":material/open_in_new:")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Diamonds redeemed", f"{int(latest['diamonds_redeemed']):,}")
    c2.metric("Diamonds earned", f"{int(latest['diamonds_earned']):,}")
    c3.metric("Days streamed", int(latest["streaming_days"]))
    status = utils.broadcaster_status(latest["streaming_days"], prev["streaming_days"] if prev is not None else None)
    c4.metric("Status", status)
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Streaming hours", f"{float(latest['streaming_hours']):,.1f}")
    c6.metric("Creator revenue", f"${float(latest['usd_earned']):,.2f}")
    if not is_broadcaster:
        # Agency revenue is the agency's own commission/cut, not the
        # broadcaster's own performance (Section 03: Broadcaster sees "own
        # performance only") - not this login's business to see.
        c7.metric("Agency revenue", f"${float(latest['my_earnings_usd']):,.2f}")
    previous_diamonds = float(prev["diamonds_redeemed"]) if prev is not None else 0
    growth = ((float(latest["diamonds_redeemed"]) - previous_diamonds) / previous_diamonds * 100
              if previous_diamonds else None)
    c8.metric("Monthly growth", f"{growth:+.1f}%" if growth is not None else "First period")

    st.markdown("###### Diamonds, all uploaded months")
    st.line_chart(hist.set_index("period")["diamonds_redeemed"], height=220)
    st.markdown("###### Days streamed, all uploaded months")
    st.bar_chart(hist.set_index("period")["streaming_days"], height=160)
    history_left, history_right = st.columns(2)
    with history_left:
        st.markdown("###### Creator revenue history")
        st.line_chart(hist.set_index("period")["usd_earned"], height=190)
    with history_right:
        st.markdown("###### Streaming hours history")
        st.line_chart(hist.set_index("period")["streaming_hours"], height=190)

    if not is_broadcaster:
        # Internal recruiter-assignment history, including which staff
        # username made the change - agency operations, not this
        # broadcaster's own performance (Section 03 scope).
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
    pdf_export_enabled = load_pdf_export_enabled(business_id)
    st.markdown('<div class="owner-overview-page"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="overview-hero"><div><div class="overview-eyebrow">Recruitment analytics</div>
    <h1>Recruiter Dashboard</h1><p>Compare recruiter contribution, activity, retention, commission, and net agency value.</p>
    </div><div class="overview-period-pill">Recruiter performance</div></div>
    """, unsafe_allow_html=True)
    dashboard_section_control("recruiter_dashboard", ["Overview", "Performance", "Commission", "Roster"])
    monthly_periods = sorted(store.list_periods("monthly", business_id), reverse=True)
    if not monthly_periods:
        st.warning("No monthly report uploaded yet.")
        st.stop()
    current_period = st.selectbox("Month", monthly_periods, key="sa_month")
    df = period_data(current_period, "monthly")
    prev_period = previous_period_of(current_period, "monthly")
    df_prev = period_data(prev_period, "monthly") if prev_period else pd.DataFrame()

    agencies = load_agencies(business_id)
    agency_details = load_agency_details(business_id)
    commission_by_agency = {
        row["agency_name"]: (None if pd.isna(row["commission_pct"]) else float(row["commission_pct"]))
        for _, row in agency_details.iterrows()
    }
    rows = []
    for a in ["Agency Direct"] + agencies:
        sub = utils.filter_by_agency(df, a)
        sub_prev = utils.filter_by_agency(df_prev, a) if not df_prev.empty else pd.DataFrame()
        k = utils.compute_kpis(sub)
        pk = utils.compute_kpis(sub_prev) if not sub_prev.empty else {}
        pct, _ = utils.compare_periods(k, pk, "diamonds_redeemed") if pk else (None, None)
        commission_pct = commission_by_agency.get(a)
        gross_usd, commission_due = calculate_sub_agency_earnings(k["diamonds_redeemed"], commission_pct)
        agency_revenue = float(sub["my_earnings_usd"].sum()) if not sub.empty else 0.0
        creator_revenue = float(sub["usd_earned"].sum()) if not sub.empty else 0.0
        retention_value = utils.retention_rate(sub, sub_prev) if not sub_prev.empty else None
        health_value = utils.broadcaster_health_score(sub, sub_prev)
        rows.append(dict(
            agency=a, broadcasters=k["broadcasters"], active=k["active"],
            new=int(sub["is_new"].sum()) if not sub.empty else 0,
            diamonds_earned=float(sub["diamonds_earned"].sum()) if not sub.empty else 0,
            diamonds=k["diamonds_redeemed"], days=k["days_worked"], hours=k["live_hours"], growth=pct,
            commission_pct=commission_pct, gross_usd=gross_usd, commission_due=commission_due,
            creator_revenue=creator_revenue, agency_revenue=agency_revenue,
            net_revenue=agency_revenue - float(commission_due or 0),
            retention=retention_value, health=health_value,
        ))
    summary = pd.DataFrame(rows)

    recruiter_summary = summary[summary["agency"] != "Agency Direct"].copy()
    total_commission = float(recruiter_summary["commission_due"].fillna(0).sum()) if not recruiter_summary.empty else 0
    recruiter_overview_panel = dashboard_panel("recruiter_dashboard", "Overview")
    recruiter_overview_panel.__enter__()
    rk1, rk2, rk3, rk4 = st.columns(4)
    rk1.metric("Total recruiters", f"{len(agencies):,}")
    rk2.metric("Recruiter-hired broadcasters", f"{int(recruiter_summary['broadcasters'].sum()):,}")
    rk3.metric("Active recruiter broadcasters", f"{int(recruiter_summary['active'].sum()):,}")
    rk4.metric("Recruiter diamonds", f"{float(recruiter_summary['diamonds'].sum()):,.0f}")
    rk5, rk6, rk7, rk8 = st.columns(4)
    rk5.metric("Gross Agency revenue", f"${float(recruiter_summary['agency_revenue'].sum()):,.2f}")
    rk6.metric("Recruiter commission", f"${total_commission:,.2f}")
    rk7.metric("Net Agency revenue", f"${float(recruiter_summary['net_revenue'].sum()):,.2f}")
    best_recruiter = (recruiter_summary.sort_values("net_revenue", ascending=False).iloc[0]["agency"]
                      if not recruiter_summary.empty else "—")
    rk8.metric("Top recruiter", best_recruiter)
    recruiter_overview_panel.__exit__(None, None, None)

    recruiter_performance_panel = dashboard_panel("recruiter_dashboard", "Performance")
    recruiter_performance_panel.__enter__()
    if not recruiter_summary.empty:
        rc1, rc2 = st.columns(2)
        revenue_compare = recruiter_summary.sort_values("net_revenue")
        recruiter_fig = go.Figure(go.Bar(
            x=revenue_compare["net_revenue"], y=revenue_compare["agency"], orientation="h",
            marker_color=SO_BRAND, text=revenue_compare["net_revenue"], texttemplate="$%{text:,.0f}",
            textposition="outside", hovertemplate="%{y}<br>Net Agency revenue: $%{x:,.2f}<extra></extra>",
        ))
        recruiter_fig.update_layout(title="Net Agency revenue by recruiter", height=330,
                                    margin=dict(l=10, r=55, t=50, b=20), showlegend=False,
                                    paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                    xaxis=dict(gridcolor=SO_GRID, tickprefix="$"), yaxis=dict(title=None))
        with rc1:
            with st.container(border=True):
                st.plotly_chart(recruiter_fig, use_container_width=True, config={"displayModeBar": False})
        retention_chart = recruiter_summary.copy()
        retention_chart["retention_display"] = retention_chart["retention"].fillna(0)
        retention_fig = go.Figure(go.Bar(
            x=retention_chart["agency"], y=retention_chart["retention_display"],
            marker_color=SO_PERIWINKLE, text=retention_chart["retention_display"], texttemplate="%{text:.1f}%",
            textposition="outside", hovertemplate="%{x}<br>Retention: %{y:.1f}%<extra></extra>",
        ))
        retention_fig.update_layout(title="Recruiter retention comparison", height=330,
                                    margin=dict(l=20, r=20, t=50, b=20), showlegend=False,
                                    paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                    yaxis=dict(range=[0, 110], ticksuffix="%", gridcolor=SO_GRID), xaxis=dict(title=None))
        with rc2:
            with st.container(border=True):
                st.plotly_chart(retention_fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Create and assign a Sub-Agency to unlock recruiter performance comparisons.")
    recruiter_performance_panel.__exit__(None, None, None)

    recruiter_commission_panel = dashboard_panel("recruiter_dashboard", "Commission")
    recruiter_commission_panel.__enter__()
    sort_choice = st.selectbox(
        "Sort by", ["Net revenue", "Diamonds", "Retention", "Growth", "Active broadcasters", "Days streamed", "Broadcaster count"], key="sa_sort"
    )
    sort_map = {"Net revenue": "net_revenue", "Diamonds": "diamonds", "Retention": "retention",
                "Growth": "growth", "Active broadcasters": "active",
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
                help=("Redeemed diamonds ÷ 200 × commission percentage"
                      if r["agency"] != "Agency Direct"
                      else "No Sub-Agency commission applies."),
            )
            d1, d2, d3, d4, d5 = st.columns(5)
            d1.metric("New", int(r["new"]))
            d2.metric("Streaming hours", f"{r['hours']:,.1f}")
            d3.metric("Creator revenue", f"${r['creator_revenue']:,.2f}")
            d4.metric("Agency revenue", f"${r['agency_revenue']:,.2f}")
            d5.metric("Net Agency revenue", f"${r['net_revenue']:,.2f}")
            st.caption(
                f"Retention: **{f'{r['retention']:.1f}%' if pd.notna(r['retention']) else 'First period'}** · "
                f"Health: **{int(r['health'])}/100** · Diamonds earned: **{r['diamonds_earned']:,.0f}**"
            )

            if r["agency"] != "Agency Direct":
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

    recruiter_commission_panel.__exit__(None, None, None)
    recruiter_roster_panel = dashboard_panel("recruiter_dashboard", "Roster")
    recruiter_roster_panel.__enter__()
    if agencies:
        st.markdown("### Recruiter Detail")
        selected_recruiter = st.selectbox("Select recruiter", agencies, key="recruiter_detail")
        recruiter_roster = utils.filter_by_agency(df, selected_recruiter).copy()
        recruiter_prev = utils.filter_by_agency(df_prev, selected_recruiter) if not df_prev.empty else pd.DataFrame()
        recruiter_roster = utils.diamonds_per_day(utils.add_growth_status(recruiter_roster, recruiter_prev))
        selected_rate = commission_by_agency.get(selected_recruiter)
        recruiter_trend_rows = []
        for trend_month in sorted(monthly_periods)[-6:]:
            month_rows = utils.filter_by_agency(period_data(trend_month, "monthly"), selected_recruiter)
            month_kpis = utils.compute_kpis(month_rows)
            _, month_commission = calculate_sub_agency_earnings(
                month_kpis["diamonds_redeemed"], selected_rate
            )
            recruiter_trend_rows.append({
                "Month": trend_month, "Diamonds": month_kpis["diamonds_redeemed"],
                "Active": month_kpis["active"],
                "Net Agency revenue": month_kpis["my_earnings_usd"] - float(month_commission or 0),
            })
        recruiter_trend = pd.DataFrame(recruiter_trend_rows)
        if len(recruiter_trend) > 1:
            rt_fig = make_subplots(specs=[[{"secondary_y": True}]])
            rt_fig.add_trace(go.Scatter(
                name="Diamonds", x=recruiter_trend["Month"], y=recruiter_trend["Diamonds"],
                mode="lines+markers", line=dict(color=SO_BRAND, width=3),
                hovertemplate="%{x}<br>%{y:,.0f} diamonds<extra></extra>",
            ), secondary_y=False)
            rt_fig.add_trace(go.Scatter(
                name="Net Agency revenue", x=recruiter_trend["Month"],
                y=recruiter_trend["Net Agency revenue"], mode="lines+markers",
                line=dict(color=SO_CYAN, width=2.5),
                hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
            ), secondary_y=True)
            rt_fig.update_layout(height=330, margin=dict(l=20, r=20, t=45, b=20),
                                 hovermode="x unified", paper_bgcolor=SO_SURFACE, plot_bgcolor=SO_SURFACE,
                                 legend=dict(orientation="h", y=1.05))
            rt_fig.update_yaxes(title_text="Diamonds", gridcolor=SO_GRID, secondary_y=False)
            rt_fig.update_yaxes(title_text="Net revenue", tickprefix="$", showgrid=False, secondary_y=True)
            with st.container(border=True):
                st.plotly_chart(rt_fig, use_container_width=True, config={"displayModeBar": False})

        recruiter_at_risk = (utils.at_risk_broadcasters(
            utils.filter_by_agency(df, selected_recruiter), recruiter_prev
        ) if not recruiter_prev.empty else recruiter_roster.iloc[0:0])
        recruiter_target = utils.performance_target(
            recruiter_roster["diamonds_redeemed"].sum(),
            recruiter_prev["diamonds_redeemed"].sum() if not recruiter_prev.empty else 0,
        )
        rd1, rd2, rd3 = st.columns(3)
        rd1.metric("Target progress", f"{recruiter_target['progress_pct']:.1f}%",
                   f"Target {recruiter_target['target']:,.0f} diamonds")
        rd2.metric("At-risk broadcasters", f"{len(recruiter_at_risk):,}")
        rd3.metric("Retention", f"{utils.retention_rate(recruiter_roster, recruiter_prev):.1f}%"
                   if not recruiter_prev.empty and utils.retention_rate(recruiter_roster, recruiter_prev) is not None
                   else "First period")
        detail_cols = ["broadcaster_name", "profile_url", "status", "is_new", "streaming_days",
                       "streaming_hours", "diamonds_earned", "diamonds_redeemed", "usd_earned",
                       "my_earnings_usd", "growth_pct"]
        st.dataframe(recruiter_roster[detail_cols].sort_values("diamonds_redeemed", ascending=False),
                     hide_index=True, width="stretch", column_config=table_column_config(detail_cols))
        statement = recruiter_roster[detail_cols].copy()
        statement["gross_redeemed_value"] = statement["diamonds_redeemed"] / DIAMONDS_PER_USD
        statement["commission_pct"] = selected_rate
        statement["commission_due"] = (statement["gross_redeemed_value"] * float(selected_rate) / 100
                                       if selected_rate is not None else None)
        if can_export:
            st.download_button(
                "Download recruiter statement", utils.safe_csv_bytes(statement),
                file_name=f"recruiter_statement_{selected_recruiter}_{current_period}.csv", mime="text/csv",
            )
            if pdf_export_enabled and len(statement) <= utils.MAX_PDF_ROWS:
                st.download_button(
                    "Download recruiter statement (PDF)",
                    utils.safe_pdf_bytes(
                        statement, "Recruiter Statement",
                        f"{html.escape(str(selected_recruiter))} — {current_period}",
                    ),
                    file_name=f"recruiter_statement_{selected_recruiter}_{current_period}.pdf",
                    mime="application/pdf",
                )
    else:
        st.info("No Sub-Agency roster is available yet.")
    recruiter_roster_panel.__exit__(None, None, None)

# ================================================================== ASSIGN
elif st.session_state.page == "Assign":
    if not is_owner_or_manager:
        st.error("Owner or Agency Manager access only.")
        st.stop()
    st.title("Assign Broadcasters")
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

    only_unassigned = st.checkbox("Show only Agency Direct broadcasters", value=True)
    view = df[df["sub_agency"] == "Agency Direct"] if only_unassigned else df

    assignment_columns = ["broadcaster_name", "profile_url", "sub_agency", "diamonds_redeemed"]
    st.dataframe(
        view[assignment_columns].sort_values("diamonds_redeemed", ascending=False),
        width='stretch', hide_index=True,
        column_config=table_column_config(assignment_columns),
    )

    st.markdown("##### Assign Selected")
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
            store.log_security_event(
                "broadcasters_assigned", username, user_role, business_id,
                "sub_agency", target_agency, f"Count: {len(selected)}",
            )
            refresh_caches()
            assigned_label = "broadcaster" if len(selected) == 1 else "broadcasters"
            st.toast(f"Assigned {len(selected)} {assigned_label} to {target_agency}.", icon="\u2705")
            st.rerun()

# ============================================================ CREATE AGENCY
elif st.session_state.page == "CreateAgency":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    if is_restricted:
        st.error(
            "This account is restricted due to non-payment. Creating a new "
            "Sub-Agency is unavailable until payment is recorded. Existing "
            "Sub-Agencies remain visible on the Recruiter Dashboard."
        )
        st.stop()
    create_agency_success = st.session_state.pop("_create_agency_success", None)
    if create_agency_success:
        st.toast(create_agency_success, icon="\u2705")
    form_version = int(st.session_state.get("ca_form_version", 0))
    form_key = f"ca_{form_version}"
    st.title("Create Sub-Agency")

    name = st.text_input("Agency name (e.g. Partner X)", key=f"{form_key}_name")
    contact = st.text_input("Contact person", key=f"{form_key}_contact")
    phone = st.text_input("Phone", key=f"{form_key}_phone")
    commission_pct = st.number_input(
        "Commission percentage", min_value=1.0, max_value=20.0, value=5.0,
        step=0.1, format="%.2f", key=f"{form_key}_commission_pct",
        help="The percentage of this Sub-Agency's redeemed diamond value that they receive.",
    )
    example_gross, example_commission = calculate_sub_agency_earnings(20_000, commission_pct)
    st.info(
        f"Calculation example: **20,000 diamonds ÷ {DIAMONDS_PER_USD} = USD {example_gross:,.2f}** "
        f"redeemed value. At **{commission_pct:g}%**, the Sub-Agency earns "
        f"**USD {example_commission:,.2f}**."
    )

    st.markdown("###### Login Access")
    make_login = st.checkbox("Also create a login for this partner", value=True, key=f"{form_key}_make_login")
    login_email, password = "", ""
    if make_login:
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        with c1:
            login_email = st.text_input("Login email", key=f"{form_key}_email")
        with c2:
            if st.button("Generate password", width="stretch", key=f"{form_key}_generate_password"):
                st.session_state[f"{form_key}_password"] = generate_secure_password()
        password = st.text_input("Password", type="password", key=f"{form_key}_password")

    status = st.selectbox("Status", ["Active", "Inactive"], key=f"{form_key}_status")
    notes = st.text_area("Notes", key=f"{form_key}_notes")

    if st.button("Create Sub-Agency", type="primary", disabled=not name.strip(), key=f"{form_key}_submit"):
        if name.strip() in load_agencies(business_id):
            st.error("A Sub-Agency with this name already exists. Update its commission under Sub-Agency Management.")
            st.stop()
        if make_login:
            if not is_valid_email(login_email):
                st.error("Enter a valid login email to also create a login.")
                st.stop()
            if is_bootstrap_identity(login_email):
                st.error("That email is reserved for the Platform Administrator. Use a different Sub-Agency login.")
                st.stop()
            if not password.strip():
                st.error("Enter a password (or generate one) to also create a login.")
                st.stop()
            password_error = store.password_policy_error(password)
            if password_error:
                st.error(password_error)
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
        store.log_security_event(
            "sub_agency_created", username, user_role, business_id,
            "sub_agency", name.strip(), f"Commission: {commission_pct:g}%",
        )
        refresh_caches()
        st.session_state["_create_agency_success"] = msg
        st.session_state["ca_form_version"] = form_version + 1
        st.rerun()

    st.markdown("##### Existing Sub-Agencies")
    existing_agencies = load_agency_details(business_id)
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
    if not is_owner_or_manager and ptype == "daily":
        st.error("Owner or Agency Manager access only.")
        st.stop()
    if is_restricted:
        st.error(
            "This account is restricted due to non-payment. Uploading reports "
            "is unavailable until payment is recorded."
        )
        st.stop()
    upload_success_key = f"_upload_success_{ptype}"
    upload_success = st.session_state.pop(upload_success_key, None)
    if upload_success:
        st.toast(upload_success, icon="\u2705")
    upload_form_version_key = f"upload_form_version_{ptype}"
    upload_form_version = int(st.session_state.get(upload_form_version_key, 0))
    upload_form_key = f"upload_{ptype}_{upload_form_version}"
    st.title(f"Upload {ptype.title()} Report")
    st.caption("Uploads add new broadcasters and update matching profiles. Existing profiles remain available.")

    default_period = dt.date.today().strftime("%Y-%m") if ptype == "monthly" else dt.date.today().isoformat()
    period_key = f"{upload_form_key}_period"
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

    uploaded = st.file_uploader(
        "Tango Referral Statistics CSV", type=["csv"], key=f"{upload_form_key}_file"
    )

    if uploaded is not None and uploaded.size > 10 * 1024 * 1024:
        st.error("This CSV is larger than the 10 MB security limit.")
        st.stop()

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

        st.markdown("##### Review Before Saving")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records", len(clean_df))
        c2.metric("Recognized", existing_count)
        c3.metric("New", new_count)
        c4.metric("Agency Direct" if is_owner_or_manager else "Not yet assigned", unassigned_count)
        st.caption(
            f"This adds or updates profiles in **{period}**. Existing profiles not present in this file stay untouched."
        )
        preview_columns = ["broadcaster_name", "profile_url", "diamonds_redeemed", "streaming_days"]
        st.dataframe(
            clean_df[preview_columns].head(10), hide_index=True, width='stretch',
            column_config=table_column_config(preview_columns),
        )

        if st.button("Confirm Upload", type="primary", key=f"{upload_form_key}_confirm"):
            # Reward Plan Management System - CSV-replace protection (req #15):
            # if this period already had data, capture it before save_period()
            # overwrites it, so any already-Approved/Paid reward can be flagged
            # for review instead of silently recalculated below.
            previous_period_rows = pd.DataFrame()
            if ptype == "monthly" and not history.empty:
                previous_period_rows = history[history["period"] == period.strip()]

            store.save_period(clean_df, period.strip(), ptype, business_id)
            if is_sub_agency:
                unassigned_here = [u for u in clean_df["profile_url"] if u not in assigned_urls]
                names_map = dict(zip(clean_df["profile_url"], clean_df["broadcaster_name"]))
                store.assign_broadcasters(unassigned_here, names_map, user_agency, business_id, assigned_by=username)
            store.log_security_event(
                "report_uploaded", username, user_role, business_id,
                "report_period", f"{ptype}:{period.strip()}", f"Rows: {len(clean_df)}",
            )
            refresh_caches()

            if ptype == "monthly":
                if not previous_period_rows.empty:
                    changed_profiles = utils.diff_period_for_reward_flags(previous_period_rows, clean_df)
                    if changed_profiles:
                        store.flag_rewards_for_review(
                            business_id, period.strip(), changed_profiles,
                            "Reporting period was re-uploaded with different values.",
                        )
                        store.log_security_event(
                            "reward_csv_replacement_flagged", username, user_role, business_id,
                            "report_period", f"monthly:{period.strip()}",
                            f"profiles={len(changed_profiles)}",
                        )
                reward_count = (
                    recalculate_broadcaster_rewards_for_period(business_id, period.strip(), username)
                    + recalculate_recruiter_rewards_for_period(business_id, period.strip(), username)
                )
                if reward_count:
                    store.log_security_event(
                        "reward_calculated", username, user_role, business_id,
                        "report_period", f"monthly:{period.strip()}", f"rewards={reward_count}",
                    )

            note = f"Saved {len(clean_df)} broadcasters for {period} ({ptype})."
            if is_owner_or_manager and unassigned_count > 0:
                note += f" {unassigned_count} are classified as Agency Direct."
            st.session_state[upload_success_key] = note
            st.session_state[upload_form_version_key] = upload_form_version + 1
            st.rerun()

# =============================================================== USER ACCESS
elif st.session_state.page == "UserAccess":
    if not is_owner_or_manager:
        st.error("Owner or Agency Manager access only.")
        st.stop()
    password_reset_notice = st.session_state.pop("_password_reset_notice", None)
    if password_reset_notice:
        st.toast(password_reset_notice, icon="\u2705")
    st.title("User Access")

    # "auditor" is here so an Auditor account (granted via SQL for now - no
    # UI to create one yet, same as Trial Viewer) displays correctly if it
    # shows up in the Existing Users list below, even though it's not offered
    # in the create-user dropdown further down.
    role_labels = {
        "sub_agency": "Sub-Agency", "agency_manager": "Agency Manager",
        "owner": "Agency Owner", "auditor": "Auditor",
    }
    # An Agency Manager can only create Recruiter (sub_agency) logins - never a
    # peer Manager or an Owner. Only an Owner can create another Owner or a
    # Manager. Enforces "no role can invite a role above or equal to itself"
    # (Section 03 of the SaaS blueprint) at the only place a role is chosen.
    creatable_roles = ["sub_agency"] if is_manager else ["sub_agency", "agency_manager", "owner"]

    st.markdown("##### Create User")
    c1, c2 = st.columns(2)
    with c1:
        new_email = st.text_input("Email", key="ua_email")
        new_name = st.text_input("Name", key="ua_name")
    with c2:
        new_role = st.selectbox(
            "Role", creatable_roles, key="ua_role",
            format_func=lambda role: role_labels[role],
        )
        new_agency = None
        if new_role == "sub_agency":
            agencies = load_agencies(business_id)
            new_agency = st.selectbox("Sub-Agency", agencies, key="ua_agency") if agencies else None
        new_password = st.text_input("Password", type="password", key="ua_password")

    if st.button("Create User", type="primary"):
        limit_error = check_membership_limit(business_id, new_role)
        if is_restricted:
            st.error(
                "This account is restricted due to non-payment. Inviting new "
                "users is unavailable until payment is recorded."
            )
        elif not is_valid_email(new_email):
            st.error("Enter a valid email address.")
        elif is_bootstrap_identity(new_email):
            st.error("That email is reserved for the Platform Administrator. Use a different user email.")
        elif not new_password.strip():
            st.error("Password is required.")
        elif new_role == "sub_agency" and not new_agency:
            st.error("Create a Sub-Agency first, then assign this login to it.")
        elif limit_error:
            st.error(limit_error)
        else:
            ok, msg = store.create_user(
                new_email.strip(), new_name.strip() or new_email.strip(),
                new_password, new_role, business_id, new_agency or "", "Active",
            )
            if ok:
                store.log_security_event("user_created", username, user_role, business_id,
                                         "account", new_email.strip().lower(), f"Role: {new_role}")
                refresh_caches()
                st.toast(msg, icon="\u2705")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("##### Existing Users")
    users_df = load_business_users(business_id)
    if users_df.empty:
        st.caption("No additional users yet \u2014 you're the only login for this agency.")
    else:
        for _, r in users_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                agency_bit = f" \u00b7 {r['sub_agency']}" if r["sub_agency"] else ""
                role_label = role_labels.get(r["role"], str(r["role"]).replace("_", " ").title())
                c1.markdown(f"**{r['name']}**  \n`{r['username']}` \u00b7 {role_label}{agency_bit}")
                c2.markdown(f"Status: **{r['status']}**")
                # An Agency Manager can only suspend/reset a Recruiter (sub_agency)
                # login - never an Owner or a peer Manager. Same role-hierarchy
                # rule as the create-user dropdown above, applied to existing users.
                can_manage_this_user = is_owner or r["role"] == "sub_agency"
                with c3:
                    if not can_manage_this_user:
                        st.caption("Owner-managed account")
                    elif r["status"] == "Active":
                        if st.button("Disable", key=f"dis_{r['username']}"):
                            store.set_user_status(r["username"], "Disabled")
                            store.log_security_event("user_disabled", username, user_role, business_id,
                                                     "account", r["username"])
                            refresh_caches()
                            st.rerun()
                    else:
                        if st.button("Enable", key=f"en_{r['username']}"):
                            store.set_user_status(r["username"], "Active")
                            store.log_security_event("user_enabled", username, user_role, business_id,
                                                     "account", r["username"])
                            refresh_caches()
                            st.rerun()
                if can_manage_this_user:
                    with st.popover("Reset Password"):
                        newpw = st.text_input("New password", type="password", key=f"pw_{r['username']}")
                        if st.button("Save Password", type="primary", key=f"savepw_{r['username']}"):
                            if newpw.strip():
                                ok, message = store.reset_user_password(r["username"], newpw.strip())
                                if ok:
                                    store.log_security_event("password_reset", username, user_role, business_id,
                                                             "account", r["username"])
                                    refresh_caches()
                                    st.session_state["_password_reset_notice"] = message
                                    st.rerun()
                                else:
                                    st.error(message)
                            else:
                                st.error("Enter a new password.")

# =========================================================== DATA MANAGEMENT
elif st.session_state.page == "DataManagement":
    if not is_owner:
        st.error("Owner access only.")
        st.stop()
    st.title("Data Management")
    ptype = st.radio(
        "Report Type", ["monthly", "daily"], horizontal=True, key="dm_ptype",
        format_func=str.title,
    )
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
                            store.log_security_event("period_unarchived", username, user_role, business_id,
                                                     "report_period", f"{ptype}:{p}")
                            refresh_caches()
                            st.rerun()
                    else:
                        if b2.button("Archive", key=f"arch_{ptype}_{p}"):
                            store.archive_period(p, ptype, business_id)
                            store.log_security_event("period_archived", username, user_role, business_id,
                                                     "report_period", f"{ptype}:{p}")
                            refresh_caches()
                            st.rerun()
                    if b3.button("Add or Update", key=f"replace_{ptype}_{p}"):
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
        st.markdown("##### :red[Danger Zone]")
        st.caption("Permanently deletes a period's numbers. Sub-Agency assignments are not affected.")
        target = st.selectbox("Period to clear", all_periods, key="dm_clear_target") if all_periods else None
        confirm = st.checkbox(f"I understand this deletes {ptype} data for the selected period", key="dm_confirm")
        if st.button("Clear This Period", type="primary", disabled=not (confirm and target)):
            store.clear_period(target, ptype, business_id)
            store.log_security_event("period_cleared", username, user_role, business_id,
                                     "report_period", f"{ptype}:{target}")
            refresh_caches()
            st.toast(f"Cleared {ptype} data for {target}.", icon="\u2705")
            st.rerun()

    st.markdown("---")
    st.markdown("##### Security Activity")
    st.caption("Recent sign-ins and security-sensitive changes in this agency workspace.")
    audit_df = load_security_audit(business_id, limit=200)
    if audit_df.empty:
        st.info("No security activity has been recorded yet.")
    else:
        st.dataframe(audit_df, hide_index=True, width="stretch")
