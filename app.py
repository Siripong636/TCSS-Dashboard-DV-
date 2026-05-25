import os
import re
import html
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# TCSS DASHBOARD - VERIFIED SINGLE FILE
# ------------------------------------------------------------
# Key points:
# - No CSS f-string is used. CSS uses raw string + placeholders.
# - Segment filter is removed. Dashboard uses Overall segment by default.
# - Sidebar Time is grouped by Year > Month checkboxes.
# - Lavatory Dirty is separated into Lavatory Cleanliness where the
#   source data identifies lavatory-related rows/topics.
# ============================================================


# -----------------------------
# BRAND COLORS
# -----------------------------
JAGGER = "#370E62"
JAGGER_DARK = "#22083E"
DASHING_YELLOW = "#F5C300"
FLAMBOYANT_PINK = "#B6007D"

PAGE_BG = "#FFFFFF"
CARD_BG = "#FFFFFF"
PLOT_BG = "#FFFFFF"
TEXT_MAIN = "#111827"
TEXT_MUTED = "#6B7280"
BORDER = "#E5E7EB"
CARD_SHADOW = "0 14px 38px rgba(17, 24, 39, 0.08)"

GREEN_GOOD = "#16A34A"
ORANGE_LOW = "#B45309"
RED_BAD = "#C00000"

MONTH_NAME = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

MONTH_ORDER = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

MONTH_NAME_TO_NUM = {v: k for k, v in MONTH_NAME.items()}

# User-facing touchpoint list for sidebar.
SIDEBAR_TOUCHPOINT_OPTIONS = [
    "Check-in",
    "Lounge",
    "Boarding",
    "Cabin Cleanliness",
    "Lavatory Cleanliness",
    "Inflight Meal (DC double catering)",
    "In-flight Beverage",
    "Arrival & Baggage Handling",
    "Irregularity Handling",
]

# Internal canonical touchpoints used for calculation.
CANONICAL_TOUCHPOINTS = [
    "Check-in",
    "Lounge",
    "Boarding",
    "Cabin Cleanliness",
    "Lavatory Cleanliness",
    "In-flight Meal",
    "In-flight Beverage",
    "Arrival & Baggage",
    "Irregularity",
]

DISPLAY_LABELS = {
    "Check-in": "Check-in",
    "Lounge": "Lounge",
    "Boarding": "Boarding",
    "Cabin Cleanliness": "Cabin Cleanliness",
    "Lavatory Cleanliness": "Lavatory Cleanliness",
    "In-flight Meal": "Inflight Meal (DC double catering)",
    "In-flight Beverage": "In-flight Beverage",
    "Arrival & Baggage": "Arrival & Baggage Handling",
    "Irregularity": "Irregularity Handling",
}

SIDEBAR_TO_CANONICAL = {
    "All Touchpoints": "All Touchpoints",
    "Check-in": "Check-in",
    "Lounge": "Lounge",
    "Boarding": "Boarding",
    "Cabin Cleanliness": "Cabin Cleanliness",
    "Lavatory Cleanliness": "Lavatory Cleanliness",
    "Inflight Meal (DC double catering)": "In-flight Meal",
    "In-flight Beverage": "In-flight Beverage",
    "Arrival & Baggage Handling": "Arrival & Baggage",
    "Irregularity Handling": "Irregularity",
}

RATING_ORDER = [
    "Very dissatisfied",
    "Dissatisfied",
    "Acceptable",
    "Satisfied",
    "Very satisfied",
]

RATING_COLORS = {
    "Very dissatisfied": "#C00000",
    "Dissatisfied": "#ED7D31",
    "Acceptable": "#BFBF00",
    "Satisfied": "#39D353",
    "Very satisfied": "#008000",
}

CLASS_ORDER = ["First Class", "Business Class", "Economy Plus", "Economy Class"]
CLASS_CARD_STYLE = {
    "First Class": {
        "short": "F",
        "bg": "linear-gradient(135deg, #FFF2B8 0%, #FFF9E8 100%)",
        "icon": "👑",
    },
    "Business Class": {
        "short": "BC",
        "bg": "linear-gradient(135deg, #EFE3FF 0%, #F8F3FF 100%)",
        "icon": "💼",
    },
    "Economy Plus": {
        "short": "EY Plus",
        "bg": "linear-gradient(135deg, #FFE4F3 0%, #FFF2F9 100%)",
        "icon": "✨",
    },
    "Economy Class": {
        "short": "EY",
        "bg": "linear-gradient(135deg, #FFDDF1 0%, #FFF1F8 100%)",
        "icon": "🧳",
    },
}


STATION_COORDINATES = [
    {"Station": "Bangkok", "Latitude": 13.6900, "Longitude": 100.7501},
    {"Station": "Chiang Mai", "Latitude": 18.7668, "Longitude": 98.9626},
    {"Station": "Chiang Rai", "Latitude": 19.9523, "Longitude": 99.8829},
    {"Station": "Hat Yai", "Latitude": 6.9332, "Longitude": 100.3929},
    {"Station": "Krabi", "Latitude": 8.0991, "Longitude": 98.9862},
    {"Station": "Phuket", "Latitude": 8.1132, "Longitude": 98.3169},
    {"Station": "Ubon Ratchathani", "Latitude": 15.2513, "Longitude": 104.8700},
    {"Station": "UbonRatchathani", "Latitude": 15.2513, "Longitude": 104.8700},
    {"Station": "Udon Thani", "Latitude": 17.3864, "Longitude": 102.7883},
    {"Station": "BURI RAM", "Latitude": 15.2295, "Longitude": 103.2532},
    {"Station": "Buriram", "Latitude": 15.2295, "Longitude": 103.2532},
    {"Station": "Khon Kaen", "Latitude": 16.4666, "Longitude": 102.7837},
    {"Station": "KhonKaen", "Latitude": 16.4666, "Longitude": 102.7837},

    {"Station": "London", "Latitude": 51.4700, "Longitude": -0.4543},
    {"Station": "Paris", "Latitude": 49.0097, "Longitude": 2.5479},
    {"Station": "Frankfurt", "Latitude": 50.0379, "Longitude": 8.5622},
    {"Station": "Munich", "Latitude": 48.3538, "Longitude": 11.7861},
    {"Station": "Brussels", "Latitude": 50.9014, "Longitude": 4.4844},
    {"Station": "Copenhagen", "Latitude": 55.6180, "Longitude": 12.6561},
    {"Station": "Stockholm", "Latitude": 59.6519, "Longitude": 17.9186},
    {"Station": "Zurich", "Latitude": 47.4581, "Longitude": 8.5555},
    {"Station": "OSLO GARDERMOEN", "Latitude": 60.1939, "Longitude": 11.1004},
    {"Station": "Oslo Gardermoen", "Latitude": 60.1939, "Longitude": 11.1004},
    {"Station": "MALPENSA", "Latitude": 45.6306, "Longitude": 8.7281},
    {"Station": "Malpensa", "Latitude": 45.6306, "Longitude": 8.7281},
    {"Station": "Milan Malpensa", "Latitude": 45.6306, "Longitude": 8.7281},
    {"Station": "Istanbul", "Latitude": 41.2753, "Longitude": 28.7519},

    {"Station": "Tokyo", "Latitude": 35.5494, "Longitude": 139.7798},
    {"Station": "Haneda", "Latitude": 35.5494, "Longitude": 139.7798},
    {"Station": "Tokyo Haneda", "Latitude": 35.5494, "Longitude": 139.7798},
    {"Station": "Osaka", "Latitude": 34.7855, "Longitude": 135.4382},
    {"Station": "Nagoya", "Latitude": 34.8584, "Longitude": 136.8054},
    {"Station": "Fukuoka", "Latitude": 33.5859, "Longitude": 130.4507},
    {"Station": "Sapporo", "Latitude": 42.7752, "Longitude": 141.6923},
    {"Station": "Seoul", "Latitude": 37.4602, "Longitude": 126.4407},
    {"Station": "Shanghai", "Latitude": 31.1443, "Longitude": 121.8083},
    {"Station": "Beijing", "Latitude": 40.0799, "Longitude": 116.6031},
    {"Station": "Guangzhou", "Latitude": 23.3924, "Longitude": 113.2988},
    {"Station": "Chengdu", "Latitude": 30.5785, "Longitude": 103.9471},
    {"Station": "Kunming", "Latitude": 25.1019, "Longitude": 102.9292},
    {"Station": "CHANGSHUI INTL. AIRPORT", "Latitude": 25.1019, "Longitude": 102.9292},
    {"Station": "CHANGSHUI INTL AIRPORT", "Latitude": 25.1019, "Longitude": 102.9292},
    {"Station": "Hong Kong", "Latitude": 22.3080, "Longitude": 113.9185},
    {"Station": "Taipei", "Latitude": 25.0777, "Longitude": 121.2328},
    {"Station": "Kaohsiung", "Latitude": 22.5771, "Longitude": 120.3500},

    {"Station": "Singapore", "Latitude": 1.3644, "Longitude": 103.9915},
    {"Station": "Kuala Lumpur", "Latitude": 2.7456, "Longitude": 101.7099},
    {"Station": "Penang", "Latitude": 5.2971, "Longitude": 100.2769},
    {"Station": "Jakarta", "Latitude": -6.1275, "Longitude": 106.6537},
    {"Station": "Denpasar", "Latitude": -8.7482, "Longitude": 115.1670},
    {"Station": "Denpasar-Bali", "Latitude": -8.7482, "Longitude": 115.1670},
    {"Station": "Bali", "Latitude": -8.7482, "Longitude": 115.1670},
    {"Station": "Manila", "Latitude": 14.5086, "Longitude": 121.0198},
    {"Station": "Hanoi", "Latitude": 21.2187, "Longitude": 105.8069},
    {"Station": "Ho Chi Minh City", "Latitude": 10.8188, "Longitude": 106.6520},
    {"Station": "Phnom Penh", "Latitude": 11.5466, "Longitude": 104.8441},
    {"Station": "PHNOM PENH", "Latitude": 11.5466, "Longitude": 104.8441},
    {"Station": "PHNOM PENH INTERNATIONAL", "Latitude": 11.5466, "Longitude": 104.8441},
    {"Station": "PHNOM PENH INTERNATIONAL AIRPORT", "Latitude": 11.5466, "Longitude": 104.8441},
    {"Station": "TECHO INTERNATIONAL AIRPORT", "Latitude": 11.3600, "Longitude": 104.9213},
    {"Station": "Techo International Airport", "Latitude": 11.3600, "Longitude": 104.9213},
    {"Station": "SiemReap", "Latitude": 13.4107, "Longitude": 103.8130},
    {"Station": "Siem Reap", "Latitude": 13.4107, "Longitude": 103.8130},
    {"Station": "Vientiane", "Latitude": 17.9883, "Longitude": 102.5633},
    {"Station": "Yangon", "Latitude": 16.9073, "Longitude": 96.1332},

    {"Station": "Mumbai", "Latitude": 19.0896, "Longitude": 72.8656},
    {"Station": "Delhi", "Latitude": 28.5562, "Longitude": 77.1000},
    {"Station": "New Delhi", "Latitude": 28.5562, "Longitude": 77.1000},
    {"Station": "Bengaluru", "Latitude": 13.1986, "Longitude": 77.7066},
    {"Station": "Ahmedabad", "Latitude": 23.0772, "Longitude": 72.6347},
    {"Station": "Chennai", "Latitude": 12.9941, "Longitude": 80.1709},
    {"Station": "Hyderabad", "Latitude": 17.2403, "Longitude": 78.4294},
    {"Station": "Kolkata", "Latitude": 22.6547, "Longitude": 88.4467},
    {"Station": "Cochin", "Latitude": 10.1520, "Longitude": 76.4019},
    {"Station": "COCHIN INTERNATIONAL AIRPORT", "Latitude": 10.1520, "Longitude": 76.4019},
    {"Station": "Dhaka", "Latitude": 23.8433, "Longitude": 90.3978},
    {"Station": "Kathmandu", "Latitude": 27.6966, "Longitude": 85.3591},
    {"Station": "Colombo", "Latitude": 7.1808, "Longitude": 79.8841},
    {"Station": "COLOMBO AIRPORT", "Latitude": 7.1808, "Longitude": 79.8841},
    {"Station": "Lahore", "Latitude": 31.5216, "Longitude": 74.4036},
    {"Station": "Islamabad", "Latitude": 33.5607, "Longitude": 72.8516},
    {"Station": "Karachi", "Latitude": 24.9065, "Longitude": 67.1608},
    {"Station": "Gaya", "Latitude": 24.7443, "Longitude": 84.9512},

    {"Station": "Jeddah", "Latitude": 21.6796, "Longitude": 39.1565},
    {"Station": "Dubai", "Latitude": 25.2532, "Longitude": 55.3657},
    {"Station": "Doha", "Latitude": 25.2731, "Longitude": 51.6081},
    {"Station": "Muscat", "Latitude": 23.5933, "Longitude": 58.2844},
    {"Station": "Riyadh", "Latitude": 24.9576, "Longitude": 46.6988},
    {"Station": "Dammam", "Latitude": 26.4712, "Longitude": 49.7979},

    {"Station": "Melbourne", "Latitude": -37.6733, "Longitude": 144.8433},
    {"Station": "Perth", "Latitude": -31.9403, "Longitude": 115.9669},
    {"Station": "Sydney", "Latitude": -33.9461, "Longitude": 151.1772},
    {"Station": "SYDNEY", "Latitude": -33.9461, "Longitude": 151.1772},
    {"Station": "Sydney Airport", "Latitude": -33.9461, "Longitude": 151.1772},
]


NATIONALITY_COORDINATES = [
    {"Nationality Group": "European", "Latitude": 50.1109, "Longitude": 8.6821},
    {"Nationality Group": "British", "Latitude": 51.4700, "Longitude": -0.4543},
    {"Nationality Group": "American", "Latitude": 39.8283, "Longitude": -98.5795},
    {"Nationality Group": "Asian", "Latitude": 34.0479, "Longitude": 100.6197},
    {"Nationality Group": "Middle Eastern", "Latitude": 25.2048, "Longitude": 55.2708},
    {"Nationality Group": "African", "Latitude": 0.0236, "Longitude": 37.9062},
    {"Nationality Group": "AUS & NZ", "Latitude": -25.2744, "Longitude": 133.7751},
    {"Nationality Group": "Thai", "Latitude": 13.7563, "Longitude": 100.5018},
    {"Nationality Group": "Others", "Latitude": 0.0000, "Longitude": -30.0000},
]


# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(
    page_title="TCSS Dashboard",
    page_icon="✈️",
    layout="wide",
)

if "dashboard_view_mode" not in st.session_state:
    st.session_state["dashboard_view_mode"] = None

VIEW_MODE = st.session_state.get("dashboard_view_mode")
IS_MOBILE_MODE = VIEW_MODE == "Mobile"
IS_TABLET_MODE = VIEW_MODE == "Tablet"
IS_LANDING_PAGE = VIEW_MODE is None


# -----------------------------
# SAFE CSS - NO F-STRING
# -----------------------------
css = r"""
<style>
:root {
    --jagger: __JAGGER__;
    --jagger-dark: __JAGGER_DARK__;
    --yellow: __DASHING_YELLOW__;
    --pink: __FLAMBOYANT_PINK__;
    --text-main: __TEXT_MAIN__;
    --text-muted: __TEXT_MUTED__;
    --border: __BORDER__;
    --card-shadow: __CARD_SHADOW__;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #FFFFFF !important;
    color: var(--text-main) !important;
    font-family: "Segoe UI", "Inter", "Arial", sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.94) !important;
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}

.block-container {
    padding-top: 1.05rem !important;
    padding-left: clamp(1.0rem, 2.3vw, 2.25rem) !important;
    padding-right: clamp(1.0rem, 2.3vw, 2.25rem) !important;
    padding-bottom: 3rem !important;
    max-width: __CONTAINER_MAX__ !important;
}

section[data-testid="stSidebar"] {
    display: __SIDEBAR_DISPLAY__ !important;
    min-width: __SIDEBAR_WIDTH__ !important;
    max-width: __SIDEBAR_WIDTH__ !important;
    width: __SIDEBAR_WIDTH__ !important;
    background:
        radial-gradient(circle at 25% 5%, rgba(245,195,0,0.28) 0%, rgba(245,195,0,0.00) 31%),
        radial-gradient(circle at 80% 88%, rgba(182,0,125,0.24) 0%, rgba(182,0,125,0.00) 32%),
        linear-gradient(180deg, #2B0A51 0%, #3B116A 55%, #160429 100%) !important;
    border-right: 0 !important;
    box-shadow: 12px 0 34px rgba(55, 14, 98, 0.20);
}

section[data-testid="stSidebar"] > div {
    min-width: __SIDEBAR_WIDTH__ !important;
    max-width: __SIDEBAR_WIDTH__ !important;
    width: __SIDEBAR_WIDTH__ !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #FFFFFF !important;
}

.sidebar-brand {
    padding: 0.35rem 0.1rem 1.0rem 0.1rem;
}
.sidebar-logo {
    color: var(--yellow) !important;
    font-weight: 950;
    font-size: 1.38rem !important;
    letter-spacing: 0.02em;
    margin-bottom: 0.85rem;
}
.sidebar-title {
    color: #FFFFFF !important;
    font-size: 1.58rem !important;
    line-height: 1.07 !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em;
}
.sidebar-footer {
    margin-top: 1.2rem;
    padding: 0.85rem;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.14);
    background: linear-gradient(135deg, rgba(255,255,255,0.13), rgba(255,255,255,0.05));
    font-size: 0.82rem !important;
    color: rgba(255,255,255,0.88) !important;
}

/* Sidebar filters */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.11) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.22) !important;
    border-radius: 14px !important;
    min-height: 42px !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: rgba(245,195,0,0.95) !important;
    color: #22083E !important;
    border-radius: 10px !important;
    font-weight: 850 !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] span,
section[data-testid="stSidebar"] [data-baseweb="tag"] svg {
    color: #22083E !important;
    fill: #22083E !important;
}

/* Main typography */
h1, h2, h3, h4, p, span, div, label {
    color: var(--text-main) !important;
}
h1 {
    font-size: clamp(2.0rem, 3.0vw, 3.1rem) !important;
    line-height: 1.05 !important;
    font-weight: 950 !important;
    letter-spacing: -0.045em !important;
    margin-bottom: 0.25rem !important;
}
h2 { font-size: clamp(1.65rem, 2.2vw, 2.3rem) !important; }
h3 { font-size: clamp(1.2rem, 1.45vw, 1.6rem) !important; }

.dashboard-topbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    margin-bottom:0.6rem;
}
.hero-title {
    color:#22083E !important;
    font-size: clamp(2.05rem, 3.0vw, 3.0rem) !important;
    font-weight: 950 !important;
    line-height: 1.03 !important;
    letter-spacing:-0.05em;
    margin:0;
}
.hero-subtitle {
    color:#4B5563 !important;
    font-size:0.98rem !important;
    font-weight:700 !important;
    margin-top:0.35rem;
}
.meta-pill {
    display:inline-flex;
    align-items:center;
    gap:0.45rem;
    padding:0.50rem 0.78rem;
    border:1px solid var(--border);
    border-radius:999px;
    background:#FFFFFF;
    box-shadow:0 8px 22px rgba(17,24,39,0.06);
    font-size:0.86rem !important;
    color:#374151 !important;
    white-space:nowrap;
}
.section-title {
    color:#111827 !important;
    font-size: clamp(1.45rem, 1.8vw, 2.05rem) !important;
    line-height:1.13 !important;
    font-weight:950 !important;
    letter-spacing:-0.035em !important;
    margin:1.55rem 0 0.8rem 0 !important;
}

.period-caption {
    color:#6B7280 !important;
    font-size:0.86rem !important;
    font-weight:650 !important;
    margin-top:-0.62rem !important;
    margin-bottom:0.55rem !important;
}
.compact-section-title {
    color:#111827 !important;
    font-size: clamp(1.35rem, 1.65vw, 1.85rem) !important;
    line-height:1.13 !important;
    font-weight:950 !important;
    letter-spacing:-0.035em !important;
    margin:1.25rem 0 0.6rem 0 !important;
}
.light-html-table-wrap {
    width:100%;
    overflow:auto;
    border:1px solid #E5E7EB;
    border-radius:16px;
    background:#FFFFFF !important;
    box-shadow:0 12px 30px rgba(17,24,39,0.08);
}
.light-html-table {
    width:100%;
    border-collapse:collapse;
    background:#FFFFFF !important;
    color:#111827 !important;
    font-size:0.94rem;
}
.light-html-table thead th {
    background:#F8FAFC !important;
    color:#111827 !important;
    font-weight:900;
    border-bottom:1px solid #E5E7EB;
    padding:0.68rem 0.8rem;
    text-align:left;
    white-space:nowrap;
}
.light-html-table tbody td {
    background:#FFFFFF !important;
    color:#111827 !important;
    border-bottom:1px solid #EEF2F7;
    padding:0.58rem 0.8rem;
    vertical-align:top;
}
.light-html-table tbody tr:nth-child(even) td { background:#F9FAFB !important; }
.light-html-table tbody tr:hover td { background:#FFF7E6 !important; }

/* Cards */
.overview-card, .premium-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FCFCFF 100%);
    border:1px solid var(--border);
    border-radius:22px;
    padding:0.95rem 1.0rem;
    box-shadow: var(--card-shadow);
    min-height:112px;
}
.overview-card {
    display:grid;
    grid-template-columns: 42px 1fr;
    column-gap:0.72rem;
    align-items:start;
}
.overview-icon, .card-icon {
    width:40px;
    height:40px;
    border-radius:15px;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    font-size:1.2rem !important;
    background:linear-gradient(135deg, #EEE7FF, #FFF7D6);
    box-shadow: inset 0 0 0 1px rgba(55,14,98,0.06);
}
.overview-label, .premium-label {
    color:#374151 !important;
    font-size:0.80rem !important;
    font-weight:850 !important;
    margin-bottom:0.35rem;
}
.overview-value, .premium-value {
    color:#2B0A51 !important;
    font-size: clamp(1.25rem, 1.45vw, 1.68rem) !important;
    font-weight:950 !important;
    letter-spacing:-0.035em !important;
    line-height:1.08 !important;
    word-break:break-word;
}
.overview-delta, .premium-delta {
    margin-top:0.55rem;
    font-size:0.82rem !important;
    font-weight:850 !important;
}
.delta-good { color:#16A34A !important; }
.delta-bad { color:#B45309 !important; }
.delta-neutral { color:#6B7280 !important; }

.class-card {
    border-radius:20px;
    padding:0.88rem 0.95rem;
    min-height:104px;
    box-shadow:0 16px 36px rgba(17,24,39,0.07);
    border:1px solid rgba(17,24,39,0.09);
}
.class-short { font-size:1.24rem !important; line-height:1 !important; font-weight:950 !important; margin-bottom:0.58rem; }
.class-label { font-size:0.90rem !important; font-weight:850 !important; opacity:0.86; margin-bottom:0.45rem; }
.class-value { font-size:1.5rem !important; font-weight:950 !important; letter-spacing:-0.035em !important; }

/* Tables */
.light-table-wrap {
    width:100%;
    overflow:auto;
    border:1px solid #E5E7EB;
    border-radius:16px;
    background:#FFFFFF;
    box-shadow:0 12px 30px rgba(17,24,39,0.08);
}
.light-table { width:100%; border-collapse:collapse; background:#FFFFFF !important; color:#111827 !important; font-size:0.94rem; }
.light-table thead th { background:#F8FAFC !important; color:#111827 !important; font-weight:900; border-bottom:1px solid #E5E7EB; padding:0.68rem 0.8rem; text-align:left; white-space:nowrap; }
.light-table tbody td, .light-table tbody th { background:#FFFFFF !important; color:#111827 !important; border-bottom:1px solid #EEF2F7; padding:0.58rem 0.8rem; vertical-align:top; }
.light-table tbody tr:nth-child(even) td, .light-table tbody tr:nth-child(even) th { background:#F9FAFB !important; }
.light-table tbody tr:hover td, .light-table tbody tr:hover th { background:#FFF7E6 !important; }

[data-testid="stDataFrame"] {
    background:#FFFFFF !important;
    border-radius:16px !important;
    border:1px solid #E5E7EB !important;
    box-shadow:0 12px 30px rgba(17,24,39,0.06) !important;
}
[data-testid="stDataFrame"] * { color:#111827 !important; }
[data-testid="stDataFrame"] button, [data-testid="stDataFrame"] svg { color:#111827 !important; fill:#111827 !important; }
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span, [data-testid="stDataFrame"] p { color:#111827 !important; }
[data-testid="stDataFrame"] [role="grid"], [data-testid="stDataFrame"] canvas { background:#FFFFFF !important; }

/* Plotly text readability */
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle,
.js-plotly-plot .plotly .legend text,
.js-plotly-plot .plotly .legendtitletext,
.js-plotly-plot .plotly .colorbar text {
    fill:#111827 !important;
    color:#111827 !important;
}

/* Main select */
.stMultiSelect div[data-baseweb="select"] > div,
.stSelectbox div[data-baseweb="select"] > div {
    background-color:#FFFFFF !important;
    color:#111827 !important;
    border:1.5px solid #E5E7EB !important;
    border-radius:14px !important;
    min-height:44px !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] { background-color:#FFFFFF !important; color:#111827 !important; }
[data-baseweb="menu"] li, [role="option"] { color:#111827 !important; background-color:#FFFFFF !important; font-size:1rem !important; }
[data-baseweb="menu"] li:hover, [role="option"]:hover { background-color:#F3F4F6 !important; }

button[kind="secondary"] {
    background-color:#FFFFFF !important;
    color:#111827 !important;
    border:1px solid #E5E7EB !important;
}

/* Landing page */
.landing-wrap {
    min-height: 86vh;
    display: grid;
    place-items: center;
    background:
        radial-gradient(circle at 78% 18%, rgba(245,195,0,0.20), transparent 28%),
        radial-gradient(circle at 12% 76%, rgba(182,0,125,0.18), transparent 32%),
        linear-gradient(135deg, #FFFFFF 0%, #FBF8FF 46%, #F8F3FF 100%);
}
.landing-card {
    width: min(1060px, 94vw);
    border-radius: 30px;
    padding: clamp(1.5rem, 3vw, 2.7rem);
    background: rgba(255,255,255,0.90);
    border: 1px solid #E6DFF4;
    box-shadow: 0 28px 80px rgba(55,14,98,0.15);
}
.landing-badge {
    display:inline-flex;
    align-items:center;
    gap:0.45rem;
    padding:0.45rem 0.7rem;
    border-radius:999px;
    background:#2B0A51;
    color:#FFFFFF !important;
    font-weight:850;
    font-size:0.82rem;
}
.landing-title {
    margin-top: 1rem;
    font-size: clamp(2.35rem, 5vw, 4.6rem) !important;
    line-height: 0.98 !important;
    font-weight: 950 !important;
    color: #23083F !important;
    letter-spacing: -0.055em;
}
.landing-subtitle {
    max-width: 780px;
    margin-top: 0.8rem;
    font-size: clamp(1rem, 1.45vw, 1.18rem) !important;
    color:#4B5563 !important;
    font-weight:700;
}
.mode-card {
    min-height: 180px;
    border:1px solid #E5E7EB;
    border-radius: 24px;
    background: linear-gradient(180deg, #FFFFFF 0%, #FCFAFF 100%);
    box-shadow: 0 18px 45px rgba(17,24,39,0.08);
    padding:1.3rem;
}
.mode-icon { font-size:2.4rem !important; margin-bottom:0.45rem; }
.mode-title {
    font-size:1.45rem !important;
    font-weight:950 !important;
    color:#23083F !important;
}
.mode-desc {
    margin-top:0.35rem;
    color:#6B7280 !important;
    font-size:0.94rem !important;
}
.mode-button-space .stButton > button {
    height: 52px !important;
    border-radius: 14px !important;
    font-size: 1.02rem !important;
    font-weight: 900 !important;
    background: #111827 !important;
    color: #FFFFFF !important;
    border: 0 !important;
}



/* Sidebar action button: readable on purple sidebar */
section[data-testid="stSidebar"] div.stButton > button {
    background: rgba(245,195,0,0.96) !important;
    color: #22083E !important;
    border: 1px solid rgba(245,195,0,0.55) !important;
    border-radius: 14px !important;
    font-weight: 900 !important;
}
section[data-testid="stSidebar"] div.stButton > button p,
section[data-testid="stSidebar"] div.stButton > button span,
section[data-testid="stSidebar"] div.stButton > button div {
    color: #22083E !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] ~ div .block-container,
[data-testid="stAppViewContainer"] .block-container {
    max-width: 100% !important;
}

@media (max-width: 900px) {
    .block-container {
        max-width: 100% !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }
    .dashboard-topbar {
        align-items:flex-start !important;
        flex-direction:column !important;
    }
    .hero-title {
        font-size: 2.05rem !important;
    }
    .overview-card {
        grid-template-columns: 38px 1fr !important;
    }
    .overview-icon, .card-icon {
        width: 38px !important;
        height: 38px !important;
    }
    .overview-card, .premium-card, .class-card {
        min-height: auto !important;
    }
    .stPlotlyChart {
        overflow-x: auto !important;
    }
}
</style>
"""

container_max = "430px" if IS_MOBILE_MODE else ("980px" if IS_TABLET_MODE else "1280px")
sidebar_width = "235px"
sidebar_display = "none" if (IS_LANDING_PAGE or IS_MOBILE_MODE) else "block"

for _key, _value in {
    "__JAGGER__": JAGGER,
    "__JAGGER_DARK__": JAGGER_DARK,
    "__DASHING_YELLOW__": DASHING_YELLOW,
    "__FLAMBOYANT_PINK__": FLAMBOYANT_PINK,
    "__TEXT_MAIN__": TEXT_MAIN,
    "__TEXT_MUTED__": TEXT_MUTED,
    "__BORDER__": BORDER,
    "__CARD_SHADOW__": CARD_SHADOW,
    "__CONTAINER_MAX__": container_max,
    "__SIDEBAR_DISPLAY__": sidebar_display,
    "__SIDEBAR_WIDTH__": sidebar_width,
}.items():
    css = css.replace(_key, str(_value))

st.markdown(css, unsafe_allow_html=True)


# -----------------------------
# BASIC HELPERS
# -----------------------------
def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_key(value) -> str:
    text = clean_text(value).upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def extract_month_from_file(filename) -> str:
    match = re.search(r"(\d{6})", str(filename))
    if match:
        ym = match.group(1)
        return f"{ym[:4]}-{ym[4:]}"
    return ""


def parse_month_column(col):
    text = str(col).strip()
    if re.match(r"^[A-Za-z]{3}-\d{2}$", text):
        return pd.to_datetime("01-" + text, format="%d-%b-%y", errors="coerce")
    if re.match(r"^[A-Za-z]{3}\s+\d{4}$", text):
        return pd.to_datetime("01 " + text, format="%d %b %Y", errors="coerce")
    parsed = pd.to_datetime(col, errors="coerce")
    if pd.notna(parsed):
        return parsed
    return pd.NaT


def normalize_month_value(value) -> str:
    text = clean_text(value)
    if not text:
        return ""
    direct = pd.to_datetime(text + "-01", errors="coerce")
    if pd.notna(direct):
        return direct.strftime("%Y-%m")
    parsed = parse_month_column(text)
    if pd.notna(parsed):
        return pd.to_datetime(parsed).strftime("%Y-%m")
    return text


def get_selected_month_label(selected_months: List[str]) -> str:
    if not selected_months:
        return ""
    temp = pd.DataFrame({"Month": selected_months})
    temp["MonthDate"] = pd.to_datetime(temp["Month"].astype(str) + "-01", errors="coerce")
    temp = temp.dropna().sort_values("MonthDate")
    if temp.empty:
        return ", ".join(selected_months)

    if len(temp) == 1:
        return temp["MonthDate"].iloc[0].strftime("%b %Y")

    years = temp["MonthDate"].dt.year.unique().tolist()
    if len(years) == 1:
        year = years[0]
        months = temp["MonthDate"].dt.month.tolist()
        expected = list(range(min(months), max(months) + 1))
        if months == expected:
            return f"{temp['MonthDate'].iloc[0].strftime('%b')}-{temp['MonthDate'].iloc[-1].strftime('%b')} {year}"
        return f"{', '.join(temp['MonthDate'].dt.strftime('%b').tolist())} {year}"

    return f"{temp['MonthDate'].iloc[0].strftime('%b %Y')} - {temp['MonthDate'].iloc[-1].strftime('%b %Y')}"


def responsive_columns(spec, gap="medium"):
    count = spec if isinstance(spec, int) else len(spec)
    if IS_MOBILE_MODE:
        return [st.container() for _ in range(count)]
    return st.columns(spec, gap=gap)


def canonical_topic(value) -> str:
    compact = normalize_key(value)

    if "LAVATORY" in compact or "TOILET" in compact:
        return "Lavatory Cleanliness"
    if "ARRIVAL" in compact or "BAGGAGE" in compact:
        return "Arrival & Baggage"
    if "IRREGULARITY" in compact:
        return "Irregularity"
    if "INFLIGHTBEVERAGE" in compact or "BEVERAGE" in compact:
        return "In-flight Beverage"
    if "INFLIGHTMEAL" in compact or "MEAL" in compact or "CATERING" in compact:
        return "In-flight Meal"
    if "CABINCLEAN" in compact or "CABINDIRTY" in compact:
        return "Cabin Cleanliness"
    if "CHECKIN" in compact or "CHECK" in compact:
        return "Check-in"
    if "LOUNGE" in compact:
        return "Lounge"
    if "BOARDING" in compact:
        return "Boarding"

    return clean_text(value)


def display_topic(topic: str) -> str:
    return DISPLAY_LABELS.get(topic, topic)


def get_data_file_path(filename: str) -> Optional[Path]:
    app_dir = Path(__file__).resolve().parent
    cwd_dir = Path.cwd()
    candidates = [
        app_dir / filename,
        cwd_dir / filename,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file() and not candidate.name.startswith("~$"):
            return candidate
    return None


def safe_numeric(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def weighted_average(df: pd.DataFrame, value_col: str, weight_col: str = "RSP") -> float:
    if df.empty or value_col not in df.columns:
        return 0.0
    values = pd.to_numeric(df[value_col], errors="coerce")
    weights = pd.to_numeric(df.get(weight_col, 0), errors="coerce").fillna(0)
    valid = values.notna()
    values = values[valid]
    weights = weights[valid]
    if values.empty:
        return 0.0
    if weights.sum() > 0:
        return float((values * weights).sum() / weights.sum())
    return float(values.mean())


def delta_html(current_value, previous_value, unit="", good_when_up=True, decimals=2) -> Tuple[str, bool]:
    if previous_value is None or pd.isna(previous_value):
        return "<span class='delta-neutral'>n/a</span>", True

    change = float(current_value) - float(previous_value)
    good = change >= 0 if good_when_up else change <= 0
    klass = "delta-good" if good else "delta-bad"
    sign = "+" if change >= 0 else ""

    if decimals == 0:
        change_text = f"{sign}{change:,.0f}{unit}"
    else:
        change_text = f"{sign}{change:,.{decimals}f}{unit}"

    return f"<span class='{klass}'>{change_text}</span>", good


def render_overview_card(icon: str, label: str, value: str, delta: str = ""):
    st.markdown(
        f"""
        <div class="overview-card">
            <div class="overview-icon">{icon}</div>
            <div>
                <div class="overview-label">{label}</div>
                <div class="overview-value">{value}</div>
                <div class="overview-delta">{delta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_premium_card(label: str, value: str, delta: Optional[str] = None, good: Optional[bool] = None):
    delta_color = TEXT_MUTED
    if good is True:
        delta_color = GREEN_GOOD
    elif good is False:
        delta_color = ORANGE_LOW

    delta_html = ""
    if delta:
        delta_html = f'<div class="premium-delta" style="color:{delta_color}!important;">{delta}</div>'

    st.markdown(
        f"""
        <div class="premium-card">
            <div class="card-icon">✦</div>
            <div class="premium-label">{label}</div>
            <div class="premium-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_class_card(class_name: str, value: int):
    style = CLASS_CARD_STYLE.get(class_name, {"short": class_name, "bg": "#FFFFFF", "icon": "✈️"})
    st.markdown(
        f"""
        <div class="class-card" style="background:{style['bg']};">
            <div class="class-short">{style['icon']} {style['short']}</div>
            <div class="class-label">{class_name}</div>
            <div class="class-value">{value:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_plot_layout(fig, height: int = 420, title_size: int = 19, show_grid: bool = True):
    fig.update_layout(
        height=height,
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_MAIN, size=12 if IS_MOBILE_MODE else 13, family="Segoe UI, Inter, Arial"),
        title=dict(font=dict(color=TEXT_MAIN, size=title_size, family="Segoe UI, Inter, Arial")),
        legend=dict(
            font=dict(color=TEXT_MAIN, size=11 if IS_MOBILE_MODE else 12),
            title_font=dict(color=TEXT_MAIN, size=11 if IS_MOBILE_MODE else 12),
            bgcolor="rgba(255,255,255,0.88)",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(color=TEXT_MAIN, family="Segoe UI, Inter, Arial"),
        ),
        margin=dict(l=42, r=44, t=76, b=44) if not IS_MOBILE_MODE else dict(l=28, r=24, t=64, b=42),
    )
    fig.update_xaxes(
        tickfont=dict(color=TEXT_MAIN),
        title_font=dict(color=TEXT_MAIN),
        color=TEXT_MAIN,
        linecolor="#CBD5E1",
    )
    fig.update_yaxes(
        tickfont=dict(color=TEXT_MAIN),
        title_font=dict(color=TEXT_MAIN),
        color=TEXT_MAIN,
        linecolor="#CBD5E1",
    )
    if show_grid:
        fig.update_xaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB")
        fig.update_yaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB")
    else:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)
    return fig


def dataframe_white(df: pd.DataFrame, height: int = 360):
    st.dataframe(
        df.style.set_properties(
            **{
                "background-color": "#FFFFFF",
                "color": TEXT_MAIN,
                "border-color": BORDER,
                "font-size": "14px",
            }
        ).set_table_styles(
            [
                {"selector": "th", "props": [("background-color", "#F8FAFC"), ("color", TEXT_MAIN), ("font-weight", "800")]},
                {"selector": "td", "props": [("background-color", "#FFFFFF"), ("color", TEXT_MAIN)]},
                {"selector": "tbody tr:nth-child(even) td", "props": [("background-color", "#F9FAFB")]},
            ]
        ),
        use_container_width=True,
        height=height,
        hide_index=True,
    )


def render_period_caption(label: Optional[str] = None):
    period = label if label is not None else selected_period_label if "selected_period_label" in globals() else ""
    if period:
        st.markdown(f"<div class='period-caption'>Selected period: {html.escape(str(period))}</div>", unsafe_allow_html=True)




def wrap_axis_label(value, width: int = 34) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    return "<br>".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def render_touchpoint_tree(container, option_labels: List[str], default_labels: Optional[List[str]] = None) -> List[str]:
    """Single touchpoint selector with a Time-like expander.

    Returns [] for All Touchpoints or a one-item list for one selected touchpoint.
    """
    container.markdown("### Select Touchpoint")
    options = ["All Touchpoints"] + option_labels
    default_value = "All Touchpoints"
    if default_labels and len(default_labels) == 1 and default_labels[0] in options:
        default_value = default_labels[0]
    with container.expander("▼ Touch Point", expanded=True):
        selected = st.selectbox(
            "Touch Point",
            options=options,
            index=options.index(default_value),
            key=f"single_touchpoint_{VIEW_MODE}",
            label_visibility="collapsed",
        )
    return [] if selected == "All Touchpoints" else [selected]


def render_touchpoint_selector(container, options: List[str], default_index: int = 0) -> str:
    """Backward-compatible single select helper, kept for old calls."""
    container.markdown("### Touchpoint")
    with container.expander("▼ Select Touchpoint", expanded=True):
        return st.selectbox(
            "Touchpoint",
            options=options,
            index=default_index,
            key=f"touchpoint_select_{VIEW_MODE}",
            label_visibility="collapsed",
        )


def find_first_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    if df.empty:
        return None
    lookup = {normalize_key(col): col for col in df.columns}
    for cand in candidates:
        key = normalize_key(cand)
        if key in lookup:
            return lookup[key]
    for col in df.columns:
        key = normalize_key(col)
        for cand in candidates:
            if normalize_key(cand) in key:
                return col
    return None

def render_light_html_table(df: pd.DataFrame, max_height: int = 420):
    if df.empty:
        st.info("No data available.")
        return
    safe_df = df.copy()
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in safe_df.columns)
    rows = []
    for _, row in safe_df.iterrows():
        cells = "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in safe_df.columns)
        rows.append(f"<tr>{cells}</tr>")
    height_style = f"max-height:{int(max_height)}px;" if max_height else ""
    table_html = (
        f"<div class='light-html-table-wrap' style='{height_style}'>"
        f"<table class='light-html-table'><thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)

# -----------------------------
# DATA LOADERS
# -----------------------------
@st.cache_data
def load_rating_data() -> pd.DataFrame:
    path = get_data_file_path("clean_tcss_rating.xlsx")
    if path is None:
        return pd.DataFrame()

    df = pd.read_excel(path)
    df.columns = df.columns.astype(str).str.strip()

    required_cols = ["Month", "Topic", "Segment"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    df["Month"] = df["Month"].apply(normalize_month_value)
    df["Topic Raw"] = df["Topic"].astype(str)
    df["Topic"] = df["Topic"].apply(canonical_topic)
    df["Segment"] = df["Segment"].astype(str).str.strip()
    df["Segment"] = df["Segment"].replace(
        {
            "Economy I": "Economy Plus",
            "Economy l": "Economy Plus",
            "Economy P": "Economy Plus",
            "First": "First",
            "Business": "Business",
            "Economy": "Economy",
        }
    )

    numeric_cols = [
        "Very satisfied",
        "Satisfied",
        "Acceptable",
        "Dissatisfied",
        "Very dissatisfied",
        "RSP",
        "CSAT",
        "Average Rating",
    ]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = safe_numeric(df[col])

    df["MonthDate"] = pd.to_datetime(df["Month"] + "-01", errors="coerce")
    df = df[df["MonthDate"].notna()].copy()
    df["Year"] = df["MonthDate"].dt.year.astype(int)
    df["MonthNum"] = df["MonthDate"].dt.month.astype(int)
    df["MonthName"] = df["MonthNum"].map(MONTH_NAME)

    # Keep only valid dashboard touchpoints.
    df = df[df["Topic"].isin(CANONICAL_TOUCHPOINTS)].copy()

    # De-duplicate at the cleanest possible grain.
    df = df.sort_values(["Month", "Topic", "Segment", "RSP"], ascending=[True, True, True, False])
    df = df.drop_duplicates(subset=["Month", "Topic", "Segment"], keep="first")

    return df


@st.cache_data
def load_raw_text() -> pd.DataFrame:
    path = get_data_file_path("master_tcss.xlsx")
    if path is None:
        return pd.DataFrame(columns=["File", "Content", "Month"])

    raw_df = pd.read_excel(path)
    raw_df.columns = raw_df.columns.astype(str).str.strip()

    if "File" not in raw_df.columns or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["File", "Content", "Month"])

    raw_df["Month"] = raw_df["File"].apply(extract_month_from_file)
    raw_df["Content"] = raw_df["Content"].astype(str)
    return raw_df


@st.cache_data
def load_extra_data() -> Dict[str, pd.DataFrame]:
    path = get_data_file_path("extra_tcss.xlsx")
    if path is None:
        return {}

    sheets: Dict[str, pd.DataFrame] = {}
    try:
        xls = pd.ExcelFile(path)
    except Exception:
        return {}

    for sheet_name in xls.sheet_names:
        try:
            temp = pd.read_excel(path, sheet_name=sheet_name)
        except Exception:
            continue
        temp.columns = temp.columns.astype(str).str.strip()
        if "Month" in temp.columns:
            temp["Month"] = temp["Month"].apply(normalize_month_value)
        for col in ["Percent", "Count", "Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP"]:
            if col in temp.columns:
                temp[col] = safe_numeric(temp[col])

        key = normalize_key(sheet_name).lower()
        sheets[sheet_name] = temp
        sheets[key] = temp
        if "station" in key:
            sheets["station"] = temp
        if "national" in key:
            sheets["nationalities"] = temp
        if "gender" in key:
            sheets["gender"] = temp
        if "age" in key:
            sheets["age_group"] = temp
        if "purpose" in key or "journey" in key:
            sheets["purpose"] = temp

    return sheets


@st.cache_data
def load_station_coordinates() -> pd.DataFrame:
    coord_sources = [pd.DataFrame(STATION_COORDINATES)]
    for filename in ["station_coordinates.xlsx", "station_coordinates.csv"]:
        path = get_data_file_path(filename)
        if path is None:
            continue
        try:
            if filename.endswith(".xlsx"):
                coord_sources.append(pd.read_excel(path))
            else:
                coord_sources.append(pd.read_csv(path))
        except Exception:
            continue

    coord = pd.concat(coord_sources, ignore_index=True)
    coord.columns = coord.columns.astype(str).str.strip()
    if "Station" not in coord.columns:
        return pd.DataFrame(columns=["Station", "Latitude", "Longitude", "StationKey"])
    coord["Station"] = coord["Station"].astype(str).str.strip()
    coord["Latitude"] = safe_numeric(coord.get("Latitude", pd.Series(dtype=float)))
    coord["Longitude"] = safe_numeric(coord.get("Longitude", pd.Series(dtype=float)))
    coord = coord.dropna(subset=["Latitude", "Longitude"]).copy()
    coord["StationKey"] = coord["Station"].apply(normalize_key)
    return coord.drop_duplicates("StationKey", keep="last")


def get_extra_sheet(extra_data_dict: Dict[str, pd.DataFrame], *names: str) -> pd.DataFrame:
    """Return a sheet from extra_tcss.xlsx using exact, compact, and fuzzy matching."""
    if not isinstance(extra_data_dict, dict):
        return pd.DataFrame()

    def key_of(value) -> str:
        return normalize_key(value).lower()

    requested = [key_of(name) for name in names if str(name).strip()]

    for name in names:
        if name in extra_data_dict:
            return extra_data_dict[name]
        compact = key_of(name)
        if compact in extra_data_dict:
            return extra_data_dict[compact]

    for key, df in extra_data_dict.items():
        key_norm = key_of(key)
        for target in requested:
            if target and (target in key_norm or key_norm in target):
                return df

    return pd.DataFrame()


def normalize_station_touchpoint(value) -> str:
    topic = canonical_topic(value)
    if topic in ["Arrival & Baggage", "Boarding", "Lounge", "Irregularity"]:
        return topic
    return clean_text(value)


def normalize_nationality_group(value) -> str:
    text = clean_text(value).lower()
    if "thai" in text:
        return "Thai"
    if "british" in text or "uk" in text:
        return "British"
    if "american" in text or "usa" in text:
        return "American"
    if "europe" in text:
        return "European"
    if "middle east" in text or "middle eastern" in text:
        return "Middle Eastern"
    if "africa" in text:
        return "African"
    if "aus" in text or "australia" in text or "new zealand" in text or "nz" in text:
        return "AUS & NZ"
    if "asia" in text:
        return "Asian"
    if "other" in text:
        return "Others"
    return clean_text(value)


def melt_wide_profile_if_needed(profile_df: pd.DataFrame, selected_months: List[str], label_col: str) -> pd.DataFrame:
    """Support passenger-profile sheets stored in wide format.

    Examples: Month | Gen X | Baby Boomer | Gen Y, or Month | Leisure travel | Business travel.
    """
    if profile_df.empty:
        return pd.DataFrame()
    temp = profile_df.copy()
    if "Month" in temp.columns:
        temp["Month"] = temp["Month"].apply(normalize_month_value)
        temp = temp[temp["Month"].isin(selected_months)].copy()
    if temp.empty:
        return pd.DataFrame()

    ignore_keys = {
        "MONTH", "MONTHDATE", "MONTHNUM", "MONTHNAME", "YEAR", "TOTAL", "TOTALRSP",
        "RSP", "RESPONSES", "RESPONSE", "COUNT", "PERCENT", "PERCENTAGE", "SHARE",
        "FILE", "PAGE", "CONTENT", "SEGMENT", "TOPIC", "TOUCHPOINT",
    }
    value_cols = []
    for col in temp.columns:
        if normalize_key(col) in ignore_keys:
            continue
        numeric = safe_numeric(temp[col])
        if numeric.notna().sum() > 0 and float(numeric.fillna(0).abs().sum()) > 0:
            value_cols.append(col)
    if not value_cols:
        return pd.DataFrame()

    id_vars = [c for c in ["Month"] if c in temp.columns]
    melted = temp.melt(id_vars=id_vars, value_vars=value_cols, var_name=label_col, value_name="__Value")
    melted[label_col] = melted[label_col].astype(str).str.strip()
    melted["__Value"] = safe_numeric(melted["__Value"])
    melted = melted[(melted[label_col] != "") & (melted["__Value"] > 0)].copy()
    if melted.empty:
        return pd.DataFrame()

    if "Month" in melted.columns:
        monthly_sum = melted.groupby("Month")["__Value"].sum()
        is_percent_like = bool((monthly_sum <= 110).all()) or bool(melted["__Value"].max() <= 1.0)
    else:
        total_sum = float(melted["__Value"].sum())
        is_percent_like = total_sum <= 110 or float(melted["__Value"].max()) <= 1.0

    if is_percent_like:
        if float(melted["__Value"].max()) <= 1.0:
            melted["__Value"] = melted["__Value"] * 100.0
        out = melted.groupby(label_col, as_index=False).agg({"__Value": "mean"}).rename(columns={"__Value": "Percent"})
        total_pct = float(out["Percent"].sum())
        out["Percent"] = out["Percent"] / total_pct * 100 if total_pct > 0 else 0
        out["Count"] = out["Percent"]
        return out.sort_values("Percent", ascending=False)

    out = melted.groupby(label_col, as_index=False).agg({"__Value": "sum"}).rename(columns={"__Value": "Count"})
    total = float(out["Count"].sum())
    out["Percent"] = out["Count"] / total * 100 if total > 0 else 0
    return out.sort_values("Count", ascending=False)


def aggregate_profile_for_selected_months(profile_df: pd.DataFrame, selected_months: List[str], label_col: str) -> pd.DataFrame:
    """Aggregate passenger profile data accurately across selected months.

    Priority:
    1) Use Count when available and sum counts.
    2) If Percent + response-like weight is available, convert Percent x weight into estimated Count.
    3) If only Percent exists, use a selected-month mean and re-normalize to 100%.

    This protects Age Group and Purpose of Journey from being misread when sheet columns
    use slightly different names such as AgeGroup, Purpose of Journey, Journey Purpose, etc.
    """
    if profile_df.empty:
        return pd.DataFrame()

    temp = profile_df.copy()
    if "Month" in temp.columns:
        temp["Month"] = temp["Month"].apply(normalize_month_value)
        temp = temp[temp["Month"].isin(selected_months)].copy()
    if temp.empty:
        return pd.DataFrame()

    # Find the best label column even when the Excel sheet name differs slightly.
    candidate_map = {
        "Gender": ["Gender", "Sex"],
        "Age Group": ["Age Group", "AgeGroup", "Age", "Generation", "Gen"],
        "Purpose": ["Purpose", "Purpose of Journey", "Journey Purpose", "Travel Purpose", "Purpose Journey"],
    }
    candidates = candidate_map.get(label_col, [label_col])
    actual_label_col = find_first_column(temp, candidates) or (label_col if label_col in temp.columns else None)
    if actual_label_col is None:
        wide_out = melt_wide_profile_if_needed(profile_df, selected_months, label_col)
        if not wide_out.empty:
            return wide_out
        return pd.DataFrame()

    temp[actual_label_col] = temp[actual_label_col].astype(str).str.strip()
    temp = temp[temp[actual_label_col] != ""].copy()
    if temp.empty:
        return pd.DataFrame()

    count_col = find_first_column(temp, ["Count", "No", "N", "Responses", "RSP", "Pax"])
    percent_col = find_first_column(temp, ["Percent", "Percentage", "Share", "%"])
    weight_col = find_first_column(temp, ["RSP", "Responses", "Response", "Total RSP", "Total Responses", "Count"])

    if count_col is not None and normalize_key(count_col) not in {normalize_key(percent_col or "")}:
        temp["__Count"] = safe_numeric(temp[count_col])
        out = temp.groupby(actual_label_col, as_index=False).agg({"__Count": "sum"}).rename(columns={actual_label_col: label_col, "__Count": "Count"})
        total = float(out["Count"].sum())
        if total > 0:
            out["Percent"] = out["Count"] / total * 100
            return out.sort_values("Count", ascending=False)
        # Fall through to Percent or wide-format fallback if count values are blank/zero.

    if percent_col is not None:
        temp["__Percent"] = safe_numeric(temp[percent_col])
        # Handle sheets that store percent as 0.291 instead of 29.1
        if temp["__Percent"].max() <= 1.0 and temp["__Percent"].sum() <= 2.0:
            temp["__Percent"] = temp["__Percent"] * 100
        if weight_col is not None:
            temp["__Weight"] = safe_numeric(temp[weight_col])
            # Avoid using the same Percent column as weight.
            if normalize_key(weight_col) == normalize_key(percent_col):
                temp["__Weight"] = 0
            if temp["__Weight"].sum() > 0:
                temp["__Count"] = temp["__Percent"] / 100.0 * temp["__Weight"]
                out = temp.groupby(actual_label_col, as_index=False).agg({"__Count": "sum"}).rename(columns={actual_label_col: label_col, "__Count": "Count"})
                total = float(out["Count"].sum())
                out["Percent"] = out["Count"] / total * 100 if total > 0 else 0
                return out.sort_values("Count", ascending=False)
        out = temp.groupby(actual_label_col, as_index=False).agg({"__Percent": "mean"}).rename(columns={actual_label_col: label_col, "__Percent": "Percent"})
        total_pct = float(out["Percent"].sum())
        out["Percent"] = out["Percent"] / total_pct * 100 if total_pct > 0 else 0
        out["Count"] = out["Percent"]
        return out.sort_values("Percent", ascending=False)

    wide_out = melt_wide_profile_if_needed(profile_df, selected_months, label_col)
    if not wide_out.empty:
        return wide_out

    return pd.DataFrame()


def extract_nationalities_from_raw_text(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["Month", "Nationality Group", "Percent", "Count"])
    patterns = {
        "European": [r"EUROPEAN"],
        "British": [r"BRITISH"],
        "American": [r"AMERICAN"],
        "Asian": [r"ASIAN"],
        "Thai": [r"THAI"],
        "Middle Eastern": [r"MIDDLE\s+EASTERN", r"MIDDLE\s+EAST"],
        "African": [r"AFRICAN"],
        "AUS & NZ": [r"AUS\s*&\s*NZ", r"AUSTRALIAN\s*&\s*NEW\s+ZEALANDER", r"AUSTRALIA\s*&\s*NEW\s+ZEALAND"],
        "Others": [r"OTHERS", r"OTHER"],
    }
    records = []
    for _, row in raw_df.iterrows():
        month = clean_text(row.get("Month", ""))
        content = clean_text(row.get("Content", ""))
        if not month or not content:
            continue
        upper = content.upper()
        if "NATIONALIT" not in upper and "EUROPEAN" not in upper:
            continue
        for group, pats in patterns.items():
            for pat in pats:
                regex = rf"{pat}\s*(?:=|:)?\s*([0-9]{{1,3}}(?:\.[0-9]+)?)\s*%?\s*\(?\s*([0-9][0-9,]*)\s*\)?"
                match = re.search(regex, upper, flags=re.IGNORECASE)
                if match:
                    records.append({"Month": month, "Nationality Group": group, "Percent": float(match.group(1)), "Count": int(match.group(2).replace(",", ""))})
                    break
    if not records:
        return pd.DataFrame(columns=["Month", "Nationality Group", "Percent", "Count"])
    out = pd.DataFrame(records).drop_duplicates(["Month", "Nationality Group"], keep="last")
    out["Percent"] = safe_numeric(out["Percent"])
    out["Count"] = safe_numeric(out["Count"])
    return out


@st.cache_data
def load_summary_complaint() -> pd.DataFrame:
    possible_names = [
        "Summary Complaint.xlsx",
        "Summary_Complaint.xlsx",
        "summary_complaint.xlsx",
    ]

    path = None
    for name in possible_names:
        path = get_data_file_path(name)
        if path is not None:
            break

    if path is None:
        return pd.DataFrame()

    try:
        complaint_df = pd.read_excel(path, sheet_name="Summary")
    except Exception:
        return pd.DataFrame()

    complaint_df.columns = complaint_df.columns.astype(str).str.strip()

    topic_col = None
    complaint_col = None
    for col in complaint_df.columns:
        lower = str(col).strip().lower()
        if lower in ["tcss topic", "topic", "touchpoint", "tcss touchpoint"]:
            topic_col = col
        if lower in ["complaint topic", "complaint", "complaints", "commendation topic"]:
            complaint_col = col

    if topic_col is None or complaint_col is None:
        return pd.DataFrame()

    month_cols = []
    month_map = {}
    for col in complaint_df.columns:
        parsed = parse_month_column(col)
        if pd.notna(parsed):
            month_cols.append(col)
            month_map[col] = parsed

    if not month_cols:
        return pd.DataFrame()

    long_df = complaint_df.melt(
        id_vars=[topic_col, complaint_col],
        value_vars=month_cols,
        var_name="MonthColumn",
        value_name="Complaint Count",
    )

    long_df = long_df.rename(columns={topic_col: "Original Topic", complaint_col: "Complaint Topic"})
    long_df["Original Topic"] = long_df["Original Topic"].apply(clean_text)
    long_df["Complaint Topic"] = long_df["Complaint Topic"].apply(clean_text)
    long_df["Complaint Count"] = safe_numeric(long_df["Complaint Count"])

    # Important Lavatory split:
    # If the complaint row is lavatory-related, separate it from Cabin Cleanliness.
    long_df["Topic"] = long_df["Original Topic"].apply(canonical_topic)
    lavatory_mask = long_df["Complaint Topic"].str.contains("lavatory|toilet|amenity in lavatory", case=False, na=False)
    long_df.loc[lavatory_mask, "Topic"] = "Lavatory Cleanliness"

    long_df["MonthDate"] = long_df["MonthColumn"].map(month_map)
    long_df = long_df[long_df["MonthDate"].notna()].copy()
    long_df["Month"] = pd.to_datetime(long_df["MonthDate"]).dt.strftime("%Y-%m")
    long_df["Year"] = pd.to_datetime(long_df["MonthDate"]).dt.year.astype(int)
    long_df["MonthNum"] = pd.to_datetime(long_df["MonthDate"]).dt.month.astype(int)
    long_df["MonthName"] = long_df["MonthNum"].map(MONTH_NAME)

    long_df = long_df[
        (long_df["Topic"].isin(CANONICAL_TOUCHPOINTS)) &
        (long_df["Complaint Topic"] != "") &
        (long_df["Complaint Count"] > 0)
    ].copy()

    long_df = (
        long_df.groupby(
            ["Month", "MonthDate", "Year", "MonthNum", "MonthName", "Topic", "Complaint Topic"],
            as_index=False,
        )
        .agg({"Complaint Count": "sum"})
    )

    long_df["Is Commendation"] = long_df["Complaint Topic"].str.contains("commendation", case=False, na=False)
    long_df["Metric"] = long_df["Is Commendation"].map({True: "Commendation", False: "Complaint"})

    return long_df.sort_values(["MonthDate", "Topic", "Complaint Count"], ascending=[True, True, False])


def extract_monthly_response_counts(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["Month", "Responses"])

    records = []
    for _, row in raw_df.iterrows():
        month = clean_text(row.get("Month", ""))
        content = clean_text(row.get("Content", ""))
        if not month or not content:
            continue

        patterns = [
            r"Responses\s*=\s*([0-9,]+)",
            r"response\s+from\s+passengers\)?\s*([0-9,]+)",
            r"responses\s+([0-9,]+)",
        ]

        values = []
        for pattern in patterns:
            for match in re.findall(pattern, content, flags=re.IGNORECASE):
                try:
                    values.append(int(str(match).replace(",", "")))
                except Exception:
                    pass

        if values:
            records.append({"Month": month, "Responses": max(values)})

    if not records:
        return pd.DataFrame(columns=["Month", "Responses"])

    result = pd.DataFrame(records)
    return result.groupby("Month", as_index=False).agg({"Responses": "max"})


def extract_class_responses_from_raw_text(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["Month", "Class", "Responses"])

    class_map = {
        "F": "First Class",
        "C": "Business Class",
        "PY": "Economy Plus",
        "EY": "Economy Class",
    }

    records = []
    for _, row in raw_df.iterrows():
        month = clean_text(row.get("Month", ""))
        content = clean_text(row.get("Content", ""))
        if not month or not content:
            continue

        text = content[:3500]
        for code, class_name in class_map.items():
            match = re.search(rf"\b{code}\s*=\s*([0-9,]+)", text, flags=re.IGNORECASE)
            if match:
                records.append(
                    {
                        "Month": month,
                        "Class": class_name,
                        "Responses": int(match.group(1).replace(",", "")),
                    }
                )

    if not records:
        return pd.DataFrame(columns=["Month", "Class", "Responses"])

    class_df = pd.DataFrame(records)
    return class_df.groupby(["Month", "Class"], as_index=False).agg({"Responses": "max"})


# -----------------------------
# PERIOD / FILTER HELPERS
# -----------------------------
def get_overall_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    if "Overall" in set(df["Segment"].astype(str).unique()):
        return df[df["Segment"].astype(str) == "Overall"].copy()
    return df.copy()


def build_period_context(selected_months: List[str], all_months: List[str]) -> Dict[str, object]:
    temp = pd.DataFrame({"Month": selected_months})
    temp["MonthDate"] = pd.to_datetime(temp["Month"].astype(str) + "-01", errors="coerce")
    temp = temp.dropna().sort_values("MonthDate")

    if temp.empty:
        return {
            "current_year": None,
            "previous_year": None,
            "month_nums": [],
            "current_months": selected_months,
            "previous_months": [],
        }

    current_year = int(temp["MonthDate"].dt.year.max())
    month_nums = sorted(temp.loc[temp["MonthDate"].dt.year == current_year, "MonthDate"].dt.month.unique().tolist())
    previous_year = current_year - 1

    current_months = [f"{current_year}-{m:02d}" for m in month_nums if f"{current_year}-{m:02d}" in all_months]
    previous_months = [f"{previous_year}-{m:02d}" for m in month_nums if f"{previous_year}-{m:02d}" in all_months]

    return {
        "current_year": current_year,
        "previous_year": previous_year,
        "month_nums": month_nums,
        "current_months": current_months,
        "previous_months": previous_months,
    }


def filter_rating_data(base_df: pd.DataFrame, months: List[str], topics: List[str]) -> pd.DataFrame:
    if base_df.empty:
        return base_df.copy()
    result = base_df[
        (base_df["Month"].isin(months)) &
        (base_df["Topic"].isin(topics))
    ].copy()
    return result


def create_touchpoint_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Topic", "Display Topic", *RATING_ORDER, "Average Rating", "CSAT", "RSP"])

    records = []
    for topic, part in df.groupby("Topic"):
        record = {"Topic": topic, "Display Topic": display_topic(topic)}
        for col in RATING_ORDER:
            record[col] = weighted_average(part, col)
        record["Average Rating"] = weighted_average(part, "Average Rating")
        record["CSAT"] = weighted_average(part, "CSAT")
        record["RSP"] = pd.to_numeric(part["RSP"], errors="coerce").fillna(0).sum()
        records.append(record)

    summary = pd.DataFrame(records)
    for col in RATING_ORDER + ["Average Rating", "CSAT", "RSP"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0)
    summary["TopicOrder"] = summary["Topic"].map({t: i for i, t in enumerate(CANONICAL_TOUCHPOINTS)})
    summary = summary.sort_values("TopicOrder").drop(columns=["TopicOrder"])
    return summary


def get_total_responses(rating_df: pd.DataFrame, raw_response_df: pd.DataFrame, months: List[str]) -> int:
    response_filter = raw_response_df[raw_response_df["Month"].isin(months)].copy()
    if not response_filter.empty:
        return int(pd.to_numeric(response_filter["Responses"], errors="coerce").fillna(0).sum())

    if rating_df.empty:
        return 0
    # Avoid double counting segments by using one RSP per Month + Topic.
    dedup = rating_df[rating_df["Month"].isin(months)].drop_duplicates(["Month", "Topic"])
    return int(pd.to_numeric(dedup["RSP"], errors="coerce").fillna(0).sum())


def aggregate_csat_trend(df: pd.DataFrame, topics: List[str]) -> pd.DataFrame:
    source = df[df["Topic"].isin(topics)].copy()
    if source.empty:
        return pd.DataFrame()

    records = []
    for (year, month_num, month_name), part in source.groupby(["Year", "MonthNum", "MonthName"]):
        records.append(
            {
                "Year": str(int(year)),
                "MonthNum": int(month_num),
                "MonthName": month_name,
                "CSAT": weighted_average(part, "CSAT"),
                "Average Rating": weighted_average(part, "Average Rating"),
                "RSP": pd.to_numeric(part["RSP"], errors="coerce").fillna(0).sum(),
            }
        )
    trend = pd.DataFrame(records)
    if not trend.empty:
        trend["MonthName"] = pd.Categorical(trend["MonthName"], categories=MONTH_ORDER, ordered=True)
        trend = trend.sort_values(["Year", "MonthNum"])
    return trend


def get_complaint_working_df(complaint_df: pd.DataFrame, topics: List[str]) -> pd.DataFrame:
    expected_cols = [
        "Month", "MonthDate", "Year", "MonthNum", "MonthName", "Topic",
        "Complaint Topic", "Complaint Count", "Is Commendation", "Metric"
    ]
    if complaint_df.empty or "Topic" not in complaint_df.columns:
        return pd.DataFrame(columns=expected_cols)
    work = complaint_df[complaint_df["Topic"].isin(topics)].copy()
    for col in expected_cols:
        if col not in work.columns:
            work[col] = pd.Series(dtype="object")
    return work


def monthly_metric_grid(complaint_df: pd.DataFrame, comparison_years: List[int], include_commendation: bool = True) -> pd.DataFrame:
    if complaint_df.empty:
        return pd.DataFrame()

    source = complaint_df[complaint_df["Year"].isin(comparison_years)].copy()
    if source.empty:
        return pd.DataFrame()

    if include_commendation:
        grouped = (
            source.groupby(["Year", "MonthNum", "MonthName", "Metric"], as_index=False)
            .agg({"Complaint Count": "sum"})
        )
        metrics = ["Complaint", "Commendation"]
    else:
        source = source[~source["Is Commendation"]].copy()
        grouped = (
            source.groupby(["Year", "MonthNum", "MonthName"], as_index=False)
            .agg({"Complaint Count": "sum"})
        )
        grouped["Metric"] = "Complaint"
        metrics = ["Complaint"]

    grid_records = []
    for year in comparison_years:
        months_in_year = sorted(
            source.loc[source["Year"] == year, "MonthNum"].dropna().astype(int).unique().tolist()
        )
        for month_num in months_in_year:
            for metric in metrics:
                grid_records.append(
                    {
                        "Year": year,
                        "MonthNum": month_num,
                        "MonthName": MONTH_NAME.get(month_num, str(month_num)),
                        "Metric": metric,
                    }
                )

    grid = pd.DataFrame(grid_records)
    if grid.empty:
        return pd.DataFrame()

    result = grid.merge(
        grouped[["Year", "MonthNum", "MonthName", "Metric", "Complaint Count"]],
        on=["Year", "MonthNum", "MonthName", "Metric"],
        how="left",
    )
    result["Complaint Count"] = result["Complaint Count"].fillna(0)
    result["Year"] = result["Year"].astype(int)
    result["Metric / Year"] = result["Metric"] + " " + result["Year"].astype(str)
    result["MonthName"] = pd.Categorical(result["MonthName"], categories=MONTH_ORDER, ordered=True)
    result = result.sort_values(["Year", "MonthNum", "Metric"])
    return result


def summarize_complaint_by_topic(complaint_df: pd.DataFrame, comparison_years: List[int]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if complaint_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    source = complaint_df[
        (complaint_df["Year"].isin(comparison_years)) &
        (~complaint_df["Is Commendation"])
    ].copy()
    if source.empty:
        return pd.DataFrame(), pd.DataFrame()

    monthly_topic_total = (
        source.groupby(["Year", "MonthNum", "MonthName", "Topic"], as_index=False)
        .agg({"Complaint Count": "sum"})
    )

    grid_records = []
    for year in comparison_years:
        months_in_year = sorted(source.loc[source["Year"] == year, "MonthNum"].dropna().astype(int).unique().tolist())
        for month_num in months_in_year:
            for topic in CANONICAL_TOUCHPOINTS:
                grid_records.append(
                    {
                        "Year": year,
                        "MonthNum": month_num,
                        "MonthName": MONTH_NAME.get(month_num, str(month_num)),
                        "Topic": topic,
                    }
                )

    grid = pd.DataFrame(grid_records)
    if grid.empty:
        return pd.DataFrame(), pd.DataFrame()

    monthly_grid = grid.merge(
        monthly_topic_total[["Year", "MonthNum", "MonthName", "Topic", "Complaint Count"]],
        on=["Year", "MonthNum", "MonthName", "Topic"],
        how="left",
    )
    monthly_grid["Complaint Count"] = monthly_grid["Complaint Count"].fillna(0)

    yearly_avg = (
        monthly_grid.groupby(["Year", "Topic"], as_index=False)
        .agg({"Complaint Count": "mean"})
        .rename(columns={"Complaint Count": "Average Complaint Count"})
    )
    yearly_avg["Display Topic"] = yearly_avg["Topic"].apply(display_topic)
    return yearly_avg, monthly_grid


def extract_top_complaints(raw_df: pd.DataFrame, selected_months: List[str], selected_topics: List[str]) -> pd.DataFrame:
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["Month", "Topic", "Top Complaint"])

    complaint_month_words = (
        "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
        "SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
    )

    records = []
    target_df = raw_df[raw_df["Month"].isin(selected_months)].copy()

    for _, row in target_df.iterrows():
        content = clean_text(row.get("Content", ""))
        if "complaint" not in content.lower():
            continue

        upper = content.upper()
        title_area = upper[:1600]
        page_topic = None

        title_patterns = [
            rf"OVERALL\s+SATISFACTION\s+FOR\s+(.+?)\s+OF\s+({complaint_month_words})\s+\d{{4}}",
            rf"SATISFACTION\s+FOR\s+(.+?)\s+OF\s+({complaint_month_words})\s+\d{{4}}",
            rf"SATISFACTION\s+BY\s+STATION\s+FOR\s+(.+?)\s+OF\s+({complaint_month_words})\s+\d{{4}}",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, title_area, flags=re.IGNORECASE)
            if match:
                page_topic = canonical_topic(match.group(1))
                break

        if page_topic is None or page_topic not in selected_topics:
            continue

        match = re.search(r"TOP\s*3\s*COMPLAINTS?(?:\s*\([^)]*\))?", content, flags=re.IGNORECASE)
        if not match:
            continue

        section = content[match.end():]
        section = re.split(
            r"\s+(?:SATISFACTION\s+FOR|SATISFACTION\s+BY\s+STATION\s+FOR|SCALE\s+4-5|\*RSP)",
            section,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]

        items = re.findall(r"[•●]\s*(.*?)(?=\s*[•●]\s*|\s*$)", section, flags=re.IGNORECASE)
        if not items:
            items = re.findall(
                r"([A-Za-z][A-Za-z0-9\s/&,'\"().+-]{5,}?\([0-9]+(?:\.[0-9]+)?%\))",
                section,
                flags=re.IGNORECASE,
            )

        for item in items[:3]:
            cleaned = clean_text(item)
            cleaned = re.split(
                r"\s+(?:VERY\s+SATISFIED|SATISFIED\s*\(|ACCEPTABLE\s*\(|DISSATISFIED\s*\(|VERY\s+DISSATISFIED|\#RSP|\*RSP|SCALE\s+4-5)",
                cleaned,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip(" -•●")
            if cleaned:
                records.append(
                    {
                        "Month": row["Month"],
                        "Topic": display_topic(page_topic),
                        "Top Complaint": cleaned[:220],
                    }
                )

    if not records:
        return pd.DataFrame(columns=["Month", "Topic", "Top Complaint"])

    result = pd.DataFrame(records).drop_duplicates()
    result["MonthDate"] = pd.to_datetime(result["Month"] + "-01", errors="coerce")
    result = result.sort_values(["MonthDate", "Topic"]).drop(columns=["MonthDate"])
    return result


# -----------------------------
# LANDING PAGE
# -----------------------------
def render_landing_page():
    st.markdown(
        """
        <div class="landing-wrap">
          <div class="landing-card">
            <div class="landing-badge">✈️ THAI Customer Experience Analytics</div>
            <div class="landing-title">THAI Customer Satisfaction Survey</div>
            <div class="landing-subtitle">
                Choose the dashboard version that best matches your screen. Desktop is optimized for executive review, Tablet balances charts for medium displays, and Smartphone stacks cards for compact viewing.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode_options = [
        ("Desktop", "🖥️", "Desktop Dashboard", "Large executive display with full-width charts and tables.", "Open Desktop Version"),
        ("Tablet", "📱", "Tablet Dashboard", "Balanced layout for iPad and medium screens.", "Open Tablet Version"),
        ("Mobile", "📲", "Smartphone Dashboard", "Compact stacked layout for phone screens.", "Open Smartphone Version"),
    ]

    mode_cols = st.columns(3, gap="large")
    for col, (mode_value, icon, title, desc, button_label) in zip(mode_cols, mode_options):
        with col:
            st.markdown(
                f"""
                <div class="mode-card">
                    <div class="mode-icon">{icon}</div>
                    <div class="mode-title">{title}</div>
                    <div class="mode-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="mode-button-space">', unsafe_allow_html=True)
            if st.button(button_label, key=f"open_{mode_value.lower()}_view", use_container_width=True):
                st.session_state["dashboard_view_mode"] = mode_value
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


if IS_LANDING_PAGE:
    render_landing_page()
    st.stop()


# -----------------------------
# LOAD ALL DATA
# -----------------------------
df_all = load_rating_data()
raw_df = load_raw_text()
extra_data = load_extra_data()
coord_df = load_station_coordinates()
complaint_summary_df = load_summary_complaint()
monthly_response_df = extract_monthly_response_counts(raw_df)
class_response_df = extract_class_responses_from_raw_text(raw_df)

if df_all.empty:
    st.error(
        "ไม่พบข้อมูล clean_tcss_rating.xlsx หรือไฟล์ไม่มีคอลัมน์ที่จำเป็น "
        "กรุณาวางไฟล์ไว้ในโฟลเดอร์เดียวกับ app.py แล้วรันใหม่"
    )
    st.stop()

overall_df = get_overall_df(df_all)

month_df = overall_df[["Month", "MonthDate", "Year", "MonthNum", "MonthName"]].drop_duplicates().sort_values("MonthDate")
available_months = month_df["Month"].tolist()
if not available_months:
    st.error("ไม่พบข้อมูลเดือนที่ใช้งานได้")
    st.stop()

latest_month = available_months[-1]
default_months = [latest_month]

available_topics_in_data = [t for t in CANONICAL_TOUCHPOINTS if t in set(overall_df["Topic"].unique())]
# Include Lavatory Cleanliness in UI when complaint data has it, even if rating data has no row.
if not complaint_summary_df.empty and "Lavatory Cleanliness" in set(complaint_summary_df["Topic"].unique()):
    if "Lavatory Cleanliness" not in available_topics_in_data:
        available_topics_in_data.append("Lavatory Cleanliness")

all_months_for_context = sorted(set(available_months) | set(complaint_summary_df["Month"].unique().tolist() if not complaint_summary_df.empty else []))


# -----------------------------
# SIDEBAR / FILTERS
# -----------------------------
def render_time_tree(container, available_month_df: pd.DataFrame, defaults: List[str]) -> List[str]:
    selected = []
    temp = available_month_df.copy().sort_values(["Year", "MonthNum"])

    container.markdown("### Time")
    for year in sorted(temp["Year"].dropna().astype(int).unique().tolist()):
        year_part = temp[temp["Year"] == year].sort_values("MonthNum")
        with container.expander(f"▼ {year}", expanded=(year == int(temp["Year"].max()))):
            all_key = f"time_all_{year}_{VIEW_MODE}"
            all_checked = st.checkbox(f"Select all {year}", key=all_key, value=False)

            for _, row in year_part.iterrows():
                month_value = row["Month"]
                month_name = row["MonthName"]
                month_key = f"time_month_{month_value}_{VIEW_MODE}"
                default_checked = month_value in defaults
                checked = st.checkbox(
                    str(month_name),
                    key=month_key,
                    value=default_checked,
                    disabled=all_checked,
                )
                if all_checked or checked:
                    selected.append(month_value)

    return sorted(set(selected), key=lambda x: pd.to_datetime(str(x) + "-01", errors="coerce"))


if IS_MOBILE_MODE:
    mode_col1, mode_col2 = responsive_columns([1, 1], gap="medium")
    with mode_col1:
        st.markdown("<div class='landing-badge'>📱 Mobile view</div>", unsafe_allow_html=True)
    with mode_col2:
        if st.button("Change view", use_container_width=True):
            st.session_state["dashboard_view_mode"] = None
            st.rerun()

    with st.expander("Filters", expanded=True):
        selected_months = render_time_tree(st, month_df, default_months)
        selected_touchpoint_labels = render_touchpoint_tree(
            st,
            SIDEBAR_TOUCHPOINT_OPTIONS,
            default_labels=["All Touchpoints"],
        )
else:
    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">✤ THAI</div>
            <div class="sidebar-title">TCSS<br>Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_months = render_time_tree(st.sidebar, month_df, default_months)
    selected_touchpoint_labels = render_touchpoint_tree(
        st.sidebar,
        SIDEBAR_TOUCHPOINT_OPTIONS,
        default_labels=["All Touchpoints"],
    )

    st.sidebar.markdown(
        f"""
        <div class="sidebar-footer">
            <div><b>Selected period</b><br>{get_selected_month_label(selected_months)}</div>
            <div style="margin-top:0.35rem; opacity:0.86;">Source: TCSS Survey</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Change Desktop / Tablet / Mobile", use_container_width=True):
        st.session_state["dashboard_view_mode"] = None
        st.rerun()

if not selected_months:
    st.warning("Please select at least one month.")
    st.stop()

selected_period_label = get_selected_month_label(selected_months)
selected_touchpoint_labels = selected_touchpoint_labels if "selected_touchpoint_labels" in globals() else []
# Empty list means All Touchpoints. Non-empty list always contains exactly one selected touchpoint.
if not selected_touchpoint_labels:
    selected_canonical = "All Touchpoints"
    selected_topics = [topic for topic in CANONICAL_TOUCHPOINTS if topic in available_topics_in_data]
else:
    selected_canonical = SIDEBAR_TO_CANONICAL.get(selected_touchpoint_labels[0], selected_touchpoint_labels[0])
    selected_topics = [selected_canonical]

period_context = build_period_context(selected_months, all_months_for_context)
current_year = period_context["current_year"]
previous_year = period_context["previous_year"]
comparison_years = [y for y in [previous_year, current_year] if y is not None]


# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    f"""
    <div class="dashboard-topbar">
        <div>
            <div class="hero-title">THAI Customer Satisfaction Survey</div>
            <div class="hero-subtitle">Customer Satisfaction Overview</div>
        </div>
        <div class="meta-pill">🗓️ Selected period: {selected_period_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# CHART FUNCTIONS
# -----------------------------
def render_touchpoint_stacked_bar(summary: pd.DataFrame, horizontal: bool = False):
    if summary.empty:
        st.info("No touchpoint satisfaction data for the selected filter.")
        return

    plot_df = summary.copy()
    plot_df["Display Topic"] = plot_df["Topic"].apply(display_topic)

    fig = go.Figure()

    if horizontal:
        for rating in RATING_ORDER:
            fig.add_trace(
                go.Bar(
                    y=plot_df["Display Topic"],
                    x=plot_df[rating],
                    name=rating,
                    orientation="h",
                    marker_color=RATING_COLORS[rating],
                    customdata=plot_df[["Average Rating", "CSAT", "RSP"]],
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        + rating
                        + ": %{x:.2f}%<br>"
                        + "Average Rating: %{customdata[0]:.2f}<br>"
                        + "CSAT: %{customdata[1]:.2f}%<br>"
                        + "RSP: %{customdata[2]:,.0f}<extra></extra>"
                    ),
                )
            )
        for _, row in plot_df.iterrows():
            fig.add_annotation(
                x=102,
                y=row["Display Topic"],
                text=f"{row['Average Rating']:.2f}",
                showarrow=False,
                font=dict(color=JAGGER_DARK, size=15),
                xanchor="left",
            )
        fig.update_layout(
            barmode="stack",
            xaxis_title="Percentage",
            yaxis_title="",
            xaxis=dict(range=[0, 112]),
            title="",
        )
        apply_plot_layout(fig, height=300 if not IS_MOBILE_MODE else 300, title_size=18)
    else:
        for rating in RATING_ORDER:
            fig.add_trace(
                go.Bar(
                    x=plot_df["Display Topic"],
                    y=plot_df[rating],
                    name=rating,
                    marker_color=RATING_COLORS[rating],
                    customdata=plot_df[["Average Rating", "CSAT", "RSP"]],
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        + rating
                        + ": %{y:.2f}%<br>"
                        + "Average Rating: %{customdata[0]:.2f}<br>"
                        + "CSAT: %{customdata[1]:.2f}%<br>"
                        + "RSP: %{customdata[2]:,.0f}<extra></extra>"
                    ),
                )
            )
        fig.add_trace(
            go.Scatter(
                x=plot_df["Display Topic"],
                y=[106] * len(plot_df),
                mode="text",
                text=plot_df["Average Rating"].map(lambda x: f"{x:.2f}"),
                textfont=dict(color=JAGGER_DARK, size=15),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.update_layout(
            barmode="stack",
            xaxis_title="",
            yaxis_title="Percentage",
            yaxis=dict(range=[0, 112]),
            title="5-Scale Distribution by Touchpoint",
        )
        apply_plot_layout(fig, height=420 if not IS_MOBILE_MODE else 360, title_size=18)
        fig.update_xaxes(tickangle=-30)

    fig.update_layout(
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06 if horizontal else 1.12,
            xanchor="center",
            x=0.5,
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    render_period_caption()



def plot_profile_donut(plot_df: pd.DataFrame, label_col: str, title: str, colors: List[str]):
    if plot_df.empty:
        st.info(f"No data for {title}")
        return
    value_col = "Count" if "Count" in plot_df.columns and safe_numeric(plot_df["Count"]).sum() > 0 else "Percent"
    fig = px.pie(
        plot_df,
        names=label_col,
        values=value_col,
        hole=0.56,
        title=title,
        color_discrete_sequence=colors,
    )
    fig.update_traces(textinfo="percent", textfont_size=13, marker=dict(line=dict(color="#FFFFFF", width=2)))
    apply_plot_layout(fig, height=300 if not IS_MOBILE_MODE else 280, title_size=15, show_grid=False)
    fig.update_layout(legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"), margin=dict(l=4, r=4, t=48, b=54))
    st.plotly_chart(fig, use_container_width=True)
    render_period_caption()


def render_passenger_profile():
    st.markdown('<div class="section-title">Passenger Profile</div>', unsafe_allow_html=True)
    col1, col2, col3 = responsive_columns(3, gap="medium")
    with col1:
        plot_profile_donut(
            aggregate_profile_for_selected_months(get_extra_sheet(extra_data, "gender", "sex", "gender profile"), selected_months, "Gender"),
            "Gender",
            f"Gender - {selected_period_label}",
            [FLAMBOYANT_PINK, DASHING_YELLOW, JAGGER, "#7A4E9D"],
        )
    with col2:
        plot_profile_donut(
            aggregate_profile_for_selected_months(get_extra_sheet(extra_data, "age_group", "age group", "agegroup", "generation", "gen"), selected_months, "Age Group"),
            "Age Group",
            f"Age Group - {selected_period_label}",
            [JAGGER, "#7A4E9D", FLAMBOYANT_PINK, DASHING_YELLOW, "#39D353", "#00A3E0"],
        )
    with col3:
        plot_profile_donut(
            aggregate_profile_for_selected_months(get_extra_sheet(extra_data, "purpose", "purpose of journey", "journey purpose", "travel purpose"), selected_months, "Purpose"),
            "Purpose",
            f"Purpose of Journey - {selected_period_label}",
            ["#31572C", "#ED7D31", "#2F5597", "#A5A5A5", FLAMBOYANT_PINK],
        )


def get_class_profile_for_selected_period() -> pd.DataFrame:
    class_profile = pd.DataFrame()
    if not class_response_df.empty:
        class_profile = class_response_df[class_response_df["Month"].isin(selected_months)].copy()
        if not class_profile.empty:
            class_profile = class_profile.groupby("Class", as_index=False).agg({"Responses": "sum"})
    if class_profile.empty:
        class_source = df_all[
            (df_all["Month"].isin(selected_months)) &
            (df_all["Segment"].isin(["First", "Business", "Economy Plus", "Economy"]))
        ].copy()
        if not class_source.empty:
            class_source["Class"] = class_source["Segment"].replace({"First": "First Class", "Business": "Business Class", "Economy": "Economy Class"})
            class_profile = class_source.groupby("Class", as_index=False).agg({"RSP": "sum"}).rename(columns={"RSP": "Responses"})
    if class_profile.empty:
        return pd.DataFrame(columns=["Class", "Responses", "Percent"])
    class_profile["Class"] = pd.Categorical(class_profile["Class"], categories=CLASS_ORDER, ordered=True)
    class_profile = class_profile.sort_values("Class")
    class_profile["Responses"] = safe_numeric(class_profile["Responses"])
    total = class_profile["Responses"].sum()
    class_profile["Percent"] = class_profile["Responses"] / total * 100 if total > 0 else 0
    return class_profile


def render_class_response_card(class_name: str, value: int, percent: float):
    style = CLASS_CARD_STYLE.get(class_name, {"short": class_name, "bg": "#FFFFFF", "icon": "✈️"})
    st.markdown(
        f"""
        <div class="class-card" style="background:{style['bg']};">
            <div class="class-short">{style['icon']} {style['short']}</div>
            <div class="class-label">{class_name}</div>
            <div class="class-value">{value:,.0f}</div>
            <div class="premium-delta"><span class="delta-neutral">{percent:.1f}% of responses</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_passenger_class_responses():
    st.markdown('<div class="section-title">Passenger Class Responses</div>', unsafe_allow_html=True)
    class_profile = get_class_profile_for_selected_period()
    if class_profile.empty:
        st.info("No passenger class response data available.")
        return
    values = {str(row["Class"]): (float(row["Responses"]), float(row["Percent"])) for _, row in class_profile.iterrows()}
    card_cols = responsive_columns(4, gap="medium")
    for idx, class_name in enumerate(CLASS_ORDER):
        with card_cols[idx]:
            value, pct = values.get(class_name, (0, 0.0))
            render_class_response_card(class_name, int(value), pct)


def render_nationalities_heatmap():
    nat = extract_nationalities_from_raw_text(raw_df)
    if nat.empty:
        nat = get_extra_sheet(extra_data, "nationalities", "nationality")
    if nat.empty or "Nationality Group" not in nat.columns:
        return
    nat = nat[nat["Month"].isin(selected_months)].copy() if "Month" in nat.columns else nat.copy()
    if nat.empty:
        return
    st.markdown('<div class="section-title">NATIONALITIES</div>', unsafe_allow_html=True)
    nat["Nationality Group"] = nat["Nationality Group"].astype(str).apply(normalize_nationality_group)
    nat["Count"] = safe_numeric(nat.get("Count", pd.Series([0] * len(nat))))
    if "Percent" in nat.columns:
        nat["Percent"] = safe_numeric(nat["Percent"])
    nat = nat.groupby("Nationality Group", as_index=False).agg({"Count": "sum"})
    total = nat["Count"].sum()
    nat["Percent"] = nat["Count"] / total * 100 if total > 0 else 0
    coord = pd.DataFrame(NATIONALITY_COORDINATES)
    map_df = nat.merge(coord, on="Nationality Group", how="left").dropna(subset=["Latitude", "Longitude"])
    col_map, col_table = responsive_columns([1.55, 1], gap="medium")
    with col_map:
        if map_df.empty:
            st.info("No nationality coordinates available.")
        else:
            fig = px.scatter_geo(
                map_df,
                lat="Latitude",
                lon="Longitude",
                hover_name="Nationality Group",
                hover_data={"Latitude": False, "Longitude": False, "Percent": ":.2f", "Count": ":,"},
                size="Count",
                size_max=60,
                color="Percent",
                color_continuous_scale=[[0.00, JAGGER], [0.35, FLAMBOYANT_PINK], [0.65, DASHING_YELLOW], [1.00, "#39D353"]],
                projection="natural earth",
                title=f"Nationalities Heat Map - {selected_period_label}",
            )
            fig.update_traces(marker=dict(line=dict(width=1, color="white"), opacity=0.88))
            fig.update_layout(
                geo=dict(bgcolor=PAGE_BG, showland=True, landcolor="#F3F4F6", showcountries=True, countrycolor="#9CA3AF", showocean=True, oceancolor="#EAF2FF", coastlinecolor="#9CA3AF"),
                coloraxis_colorbar=dict(title=dict(text="Share (%)", font=dict(color=TEXT_MAIN)), tickfont=dict(color=TEXT_MAIN)),
            )
            apply_plot_layout(fig, height=360 if not IS_MOBILE_MODE else 300, title_size=18, show_grid=False)
            st.plotly_chart(fig, use_container_width=True)
            render_period_caption()
    with col_table:
        st.markdown("### Nationalities Summary")
        display = nat.sort_values("Count", ascending=False).copy()
        display["Count"] = display["Count"].map(lambda x: f"{x:,.0f}")
        display["Percent"] = display["Percent"].map(lambda x: f"{x:.2f}%")
        render_light_html_table(display[["Nationality Group", "Count", "Percent"]], max_height=360)


def render_station_satisfaction_map(station_topic: str):
    station_touchpoints = ["Arrival & Baggage", "Boarding", "Lounge", "Irregularity"]
    if station_topic not in station_touchpoints:
        return
    station_df = get_extra_sheet(extra_data, "station", "station satisfaction", "station_satisfaction")
    if station_df.empty:
        st.info("No station-level Appendix data found in extra_tcss.xlsx.")
        return
    required_cols = {"Station", "Topic", "Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP"}
    missing_cols = required_cols - set(station_df.columns)
    if missing_cols:
        st.info("Station data exists, but required columns are missing: " + ", ".join(sorted(missing_cols)))
        return
    work = station_df.copy()
    if "Month" in work.columns:
        work["Month"] = work["Month"].apply(normalize_month_value)
    work["Topic"] = work["Topic"].astype(str).apply(normalize_station_touchpoint)
    work["Station"] = work["Station"].astype(str).str.strip()
    for _station_num_col in ["Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP"]:
        work[_station_num_col] = safe_numeric(work[_station_num_col])
    invalid_keys = {"", "FILE", "PAGE", "CONTENT", "STATION", "TOTAL", "GRANDTOTAL", "MONTH", "TOPIC", "CLASS", "CABIN", "SEGMENT", "OVERALL", "BUSINESS", "ECONOMY", "RSP", "SCALE", "SATISFACTION"}
    work["StationKeyTemp"] = work["Station"].apply(normalize_key)
    work = work[~work["StationKeyTemp"].isin(invalid_keys)].drop(columns=["StationKeyTemp"])
    work = work[work["Topic"] == station_topic].copy()
    if work.empty:
        st.info(f"No station-level rows found for {display_topic(station_topic)}.")
        return
    selected_station = work[work.get("Month", "").isin(selected_months)].copy() if "Month" in work.columns else work.copy()
    station_period = selected_period_label
    if selected_station.empty and "Month" in work.columns:
        latest = sorted(work["Month"].dropna().unique().tolist())[-1]
        selected_station = work[work["Month"] == latest].copy()
        station_period = get_selected_month_label([latest])
    if selected_station.empty:
        st.info(f"No station-level rows found for {display_topic(station_topic)}.")
        return

    st.markdown('<div class="section-title">Station Satisfaction Map</div>', unsafe_allow_html=True)
    station_summary = selected_station.groupby("Station", as_index=False).agg({
        "Satisfaction 5-4": "mean",
        "Neutral 3": "mean",
        "Dissatisfaction 2-1": "mean",
        "RSP": "sum",
    })
    station_summary["StationKey"] = station_summary["Station"].apply(normalize_key)
    total_row = station_summary[station_summary["StationKey"] == "STATIONS"].copy()
    details = station_summary[station_summary["StationKey"] != "STATIONS"].sort_values("Satisfaction 5-4", ascending=False).copy()
    # Multi-month rule: Satisfaction columns are averages, RSP is sum.
    # If the source does not contain a STATIONS total row, calculate a weighted total from station details.
    if total_row.empty and not details.empty:
        total_rsp_calc = float(safe_numeric(details["RSP"]).sum())
        if total_rsp_calc > 0:
            total_values = {
                "Station": "Stations",
                "Satisfaction 5-4": float((safe_numeric(details["Satisfaction 5-4"]) * safe_numeric(details["RSP"])).sum() / total_rsp_calc),
                "Neutral 3": float((safe_numeric(details["Neutral 3"]) * safe_numeric(details["RSP"])).sum() / total_rsp_calc),
                "Dissatisfaction 2-1": float((safe_numeric(details["Dissatisfaction 2-1"]) * safe_numeric(details["RSP"])).sum() / total_rsp_calc),
                "RSP": total_rsp_calc,
                "StationKey": "STATIONS",
            }
        else:
            total_values = {
                "Station": "Stations",
                "Satisfaction 5-4": float(safe_numeric(details["Satisfaction 5-4"]).mean()),
                "Neutral 3": float(safe_numeric(details["Neutral 3"]).mean()),
                "Dissatisfaction 2-1": float(safe_numeric(details["Dissatisfaction 2-1"]).mean()),
                "RSP": 0.0,
                "StationKey": "STATIONS",
            }
        total_row = pd.DataFrame([total_values])
    map_df = details.merge(coord_df[["StationKey", "Latitude", "Longitude"]], on="StationKey", how="left").dropna(subset=["Latitude", "Longitude"])
    map_col, table_col = responsive_columns([1.45, 1.0], gap="medium")
    with map_col:
        if map_df.empty:
            st.info("No station coordinates found for the selected station rows.")
        else:
            map_df["Bubble Size"] = safe_numeric(map_df["RSP"]).clip(lower=1)
            fig = px.scatter_geo(
                map_df,
                lat="Latitude",
                lon="Longitude",
                hover_name="Station",
                hover_data={"Latitude": False, "Longitude": False, "Satisfaction 5-4": ":.2f", "Neutral 3": ":.2f", "Dissatisfaction 2-1": ":.2f", "RSP": ":,"},
                size="Bubble Size",
                size_max=36,
                color="Satisfaction 5-4",
                range_color=[0, 100],
                color_continuous_scale=[[0, "#C00000"], [0.35, "#ED7D31"], [0.55, DASHING_YELLOW], [0.75, "#39D353"], [1, "#008000"]],
                projection="natural earth",
                title=f"Station Satisfaction World Map - {display_topic(station_topic)}",
            )
            fig.update_traces(marker=dict(line=dict(width=0.8, color="white"), opacity=0.88))
            fig.update_layout(
                geo=dict(bgcolor=PAGE_BG, showland=True, landcolor="#F3F4F6", showcountries=True, countrycolor="#9CA3AF", showocean=True, oceancolor="#EAF2FF", coastlinecolor="#9CA3AF"),
                coloraxis_colorbar=dict(title=dict(text="Sat 5-4 (%)", font=dict(color=TEXT_MAIN)), tickfont=dict(color=TEXT_MAIN)),
            )
            apply_plot_layout(fig, height=410 if not IS_MOBILE_MODE else 320, title_size=18, show_grid=False)
            st.plotly_chart(fig, use_container_width=True)
            render_period_caption(station_period)
    with table_col:
        st.markdown("### Station Summary")
        if not total_row.empty:
            total = total_row.iloc[0]
            mini_cols = responsive_columns(4, gap="small")
            with mini_cols[0]:
                render_premium_card("Stations 5-4", f"{float(total['Satisfaction 5-4']):.2f}%")
            with mini_cols[1]:
                render_premium_card("Stations 3", f"{float(total['Neutral 3']):.2f}%")
            with mini_cols[2]:
                render_premium_card("Stations 2-1", f"{float(total['Dissatisfaction 2-1']):.2f}%")
            with mini_cols[3]:
                render_premium_card("Stations RSP", f"{int(float(total['RSP'])):,}")
        disp = details[["Station", "Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP"]].copy()
        disp["Satisfaction 5-4"] = disp["Satisfaction 5-4"].map(lambda x: f"{x:.2f}%")
        disp["Neutral 3"] = disp["Neutral 3"].map(lambda x: f"{x:.2f}%")
        disp["Dissatisfaction 2-1"] = disp["Dissatisfaction 2-1"].map(lambda x: f"{x:.2f}%")
        disp["RSP"] = disp["RSP"].map(lambda x: f"{x:,.0f}")
        render_light_html_table(disp, max_height=440)

def render_class_distribution():
    st.markdown('<div class="section-title">Class Distribution</div>', unsafe_allow_html=True)

    class_profile = pd.DataFrame()
    if not class_response_df.empty:
        class_profile = class_response_df[class_response_df["Month"].isin(selected_months)].copy()
        class_profile = class_profile.groupby("Class", as_index=False).agg({"Responses": "sum"})

    if class_profile.empty:
        class_source = df_all[
            (df_all["Month"].isin(selected_months)) &
            (df_all["Segment"].isin(["First", "Business", "Economy Plus", "Economy"]))
        ].copy()
        if not class_source.empty:
            class_source["Class"] = class_source["Segment"].replace(
                {
                    "First": "First Class",
                    "Business": "Business Class",
                    "Economy": "Economy Class",
                }
            )
            class_profile = class_source.groupby("Class", as_index=False).agg({"RSP": "sum"}).rename(columns={"RSP": "Responses"})

    if class_profile.empty:
        st.info("No class distribution data available.")
        return

    class_profile["Class"] = pd.Categorical(class_profile["Class"], categories=CLASS_ORDER, ordered=True)
    class_profile = class_profile.sort_values("Class")
    class_values = dict(zip(class_profile["Class"].astype(str), class_profile["Responses"]))

    donut_col, cards_col = responsive_columns([1.05, 1.25], gap="medium")

    with donut_col:
        fig = px.pie(
            class_profile,
            names="Class",
            values="Responses",
            hole=0.56,
            title="Cabin Class Distribution",
            color="Class",
            color_discrete_map={
                "First Class": "#E377C2",
                "Business Class": "#7030A0",
                "Economy Plus": FLAMBOYANT_PINK,
                "Economy Class": DASHING_YELLOW,
            },
        )
        fig.update_traces(textinfo="percent", textfont_size=13, marker=dict(line=dict(color="#FFFFFF", width=2)))
        apply_plot_layout(fig, height=330 if not IS_MOBILE_MODE else 310, title_size=17, show_grid=False)
        fig.update_layout(
            legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
            margin=dict(l=6, r=6, t=50, b=78),
        )
        st.plotly_chart(fig, use_container_width=True)
        render_period_caption()

    with cards_col:
        card_cols = responsive_columns(2, gap="small") if IS_MOBILE_MODE else st.columns(2, gap="small")
        for idx, class_name in enumerate(CLASS_ORDER):
            with card_cols[idx % 2]:
                render_class_card(class_name, int(class_values.get(class_name, 0)))


def render_touchpoint_ranking_table(summary: pd.DataFrame):
    st.markdown('<div class="section-title">Touchpoint Ranking Table</div>', unsafe_allow_html=True)
    if summary.empty:
        st.info("No ranking data available.")
        return

    table = summary.sort_values("Average Rating", ascending=False).copy()
    table["Rank"] = range(1, len(table) + 1)
    table = table[["Rank", "Display Topic", "Average Rating", "CSAT", "RSP"]].rename(
        columns={"Display Topic": "Touchpoint"}
    )
    table["Average Rating"] = table["Average Rating"].map(lambda x: f"{x:.2f}")
    table["CSAT"] = table["CSAT"].map(lambda x: f"{x:.2f}%")
    table["RSP"] = table["RSP"].map(lambda x: f"{x:,.0f}")
    render_light_html_table(table, max_height=360 if not IS_MOBILE_MODE else 320)


def render_csat_trend(topics: List[str], title: str):
    trend = aggregate_csat_trend(overall_df, topics)
    if trend.empty:
        st.info("No CSAT trend data available.")
        return

    fig = px.line(
        trend,
        x="MonthName",
        y="CSAT",
        color="Year",
        markers=True,
        category_orders={"MonthName": MONTH_ORDER},
        title=title,
        color_discrete_map={
            str(previous_year): DASHING_YELLOW,
            str(current_year): FLAMBOYANT_PINK,
        },
        hover_data={"CSAT": ":.2f", "Average Rating": ":.2f", "RSP": ":,.0f", "Year": True},
    )
    for trace in fig.data:
        if previous_year is not None and str(previous_year) in trace.name:
            trace.update(line=dict(dash="dash", width=2.0), marker=dict(size=7))
        else:
            trace.update(line=dict(dash="solid", width=3.2), marker=dict(size=8))
    apply_plot_layout(fig, height=350 if not IS_MOBILE_MODE else 320, title_size=18)
    fig.update_layout(xaxis_title="Month", yaxis_title="CSAT (%)", legend_title_text="Year")
    fig.update_xaxes(categoryorder="array", categoryarray=MONTH_ORDER)
    st.plotly_chart(fig, use_container_width=True)


def render_complaint_trend(topics: List[str], include_commendation: bool, title: str, height: Optional[int] = None):
    comp = get_complaint_working_df(complaint_summary_df, topics)
    if comp.empty:
        st.info("No complaint trend data available.")
        return

    years_available = sorted(comp["Year"].dropna().astype(int).unique().tolist())
    target_years = [y for y in [previous_year, current_year] if y in years_available]
    if not target_years:
        target_years = years_available[-2:] if len(years_available) >= 2 else years_available

    metric_df = monthly_metric_grid(comp, target_years, include_commendation=include_commendation)
    if metric_df.empty:
        st.info("No complaint trend data available.")
        return

    color_map = {
        f"Complaint {target_years[0] if target_years else ''}": DASHING_YELLOW,
        f"Complaint {target_years[-1] if target_years else ''}": FLAMBOYANT_PINK,
        f"Commendation {target_years[0] if target_years else ''}": "#7ED321",
        f"Commendation {target_years[-1] if target_years else ''}": GREEN_GOOD,
    }

    fig = px.line(
        metric_df,
        x="MonthName",
        y="Complaint Count",
        color="Metric / Year",
        markers=True,
        category_orders={"MonthName": MONTH_ORDER},
        title=title,
        color_discrete_map=color_map,
        hover_data={"Year": True, "Metric": True, "Complaint Count": ":,.0f"},
    )
    for trace in fig.data:
        if target_years and str(target_years[0]) in trace.name:
            trace.update(line=dict(dash="dash", width=2.0), marker=dict(size=7))
        else:
            trace.update(line=dict(dash="solid", width=3.2), marker=dict(size=8))
    chart_height = height if height is not None else (360 if not IS_MOBILE_MODE else 320)
    apply_plot_layout(fig, height=chart_height, title_size=18)
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Count",
        legend_title_text="Metric / Year",
        legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
        margin=dict(l=48, r=34, t=108, b=56),
    )
    fig.update_xaxes(categoryorder="array", categoryarray=MONTH_ORDER)
    st.plotly_chart(fig, use_container_width=True)


def render_top_complaints_table(topics: List[str]):
    st.markdown('<div class="section-title">Top Complaint by Topic</div>', unsafe_allow_html=True)
    comp = get_complaint_working_df(complaint_summary_df, topics)
    if comp.empty:
        text_table = extract_top_complaints(raw_df, selected_months, topics)
        if text_table.empty:
            st.info("No complaint text found for the selected filters.")
            return
        text_table["Month"] = text_table["Month"].apply(lambda x: get_selected_month_label([x]) if isinstance(x, str) else x)
        render_light_html_table(text_table, max_height=420)
        return

    comp = comp[(comp["Month"].isin(selected_months)) & (~comp["Is Commendation"])].copy()
    if comp.empty:
        st.info("No complaint rows found for the selected period.")
        return
    table = (
        comp.groupby(["Topic", "Complaint Topic"], as_index=False)
        .agg({"Complaint Count": "sum"})
        .sort_values(["Topic", "Complaint Count"], ascending=[True, False])
    )
    table["Rank"] = table.groupby("Topic")["Complaint Count"].rank(method="first", ascending=False)
    table = table[table["Rank"] <= 3].copy()
    table["Selected Period"] = selected_period_label
    table["Touchpoint"] = table["Topic"].apply(display_topic)
    table = table[["Selected Period", "Touchpoint", "Complaint Topic", "Complaint Count"]]
    table["Complaint Count"] = table["Complaint Count"].map(lambda x: f"{x:,.0f}")
    render_light_html_table(table, max_height=460)


def render_complaint_by_topic_chart(topics: List[str]):
    comp = get_complaint_working_df(complaint_summary_df, topics)
    if comp.empty:
        st.info("No complaint by topic data available.")
        return

    years_available = sorted(comp["Year"].dropna().astype(int).unique().tolist())
    target_years = [y for y in [previous_year, current_year] if y in years_available]
    if not target_years:
        target_years = years_available[-2:] if len(years_available) >= 2 else years_available

    avg_long, _ = summarize_complaint_by_topic(comp, target_years)
    if avg_long.empty:
        st.info("No complaint by topic data available.")
        return

    avg_long["Year"] = avg_long["Year"].astype(str)
    fig = px.bar(
        avg_long,
        x="Display Topic",
        y="Average Complaint Count",
        color="Year",
        barmode="group",
        text="Average Complaint Count",
        category_orders={"Display Topic": [display_topic(t) for t in CANONICAL_TOUCHPOINTS]},
        title="Average Complaint by Topic: YoY",
        color_discrete_map={
            str(target_years[0] if target_years else ""): DASHING_YELLOW,
            str(target_years[-1] if target_years else ""): FLAMBOYANT_PINK,
        },
        hover_data={"Average Complaint Count": ":,.0f"},
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    apply_plot_layout(fig, height=390 if not IS_MOBILE_MODE else 340, title_size=18)
    fig.update_xaxes(tickangle=-25)
    fig.update_layout(xaxis_title="Touchpoint", yaxis_title="Average Complaint", legend_title_text="Year")
    st.plotly_chart(fig, use_container_width=True)



def render_average_metric_cards(metric_name: str, title: str):
    comp = get_complaint_working_df(complaint_summary_df, CANONICAL_TOUCHPOINTS)
    if comp.empty or "Metric" not in comp.columns:
        return

    years_available = sorted(comp["Year"].dropna().astype(int).unique().tolist())
    target_years = [y for y in [previous_year, current_year] if y in years_available]
    if len(target_years) < 2:
        target_years = years_available[-2:] if len(years_available) >= 2 else years_available
    if not target_years:
        return

    comp_metric = comp[(comp["Year"].isin(target_years)) & (comp["Metric"] == metric_name)].copy()
    if comp_metric.empty:
        return

    monthly_topic = (
        comp_metric.groupby(["Year", "MonthNum", "Topic"], as_index=False)
        .agg({"Complaint Count": "sum"})
    )
    yearly_avg = (
        monthly_topic.groupby(["Year", "Topic"], as_index=False)
        .agg({"Complaint Count": "mean"})
        .rename(columns={"Complaint Count": "Average Count"})
    )
    pivot = yearly_avg.pivot(index="Topic", columns="Year", values="Average Count").reset_index().fillna(0)
    for year in target_years:
        if year not in pivot.columns:
            pivot[year] = 0.0

    current_y = target_years[-1]
    previous_y = target_years[0]
    pivot["TopicOrder"] = pivot["Topic"].map({t: i for i, t in enumerate(CANONICAL_TOUCHPOINTS)}).fillna(999)
    pivot = pivot.sort_values("TopicOrder")

    total_current = float(pivot[current_y].sum())
    total_previous = float(pivot[previous_y].sum())
    total_delta, total_good = delta_html(
        total_current,
        total_previous,
        good_when_up=(metric_name == "Commendation"),
        decimals=0 if metric_name == "Commendation" else 1,
    )

    high_row = pivot.sort_values(current_y, ascending=False).iloc[0]
    low_row = pivot.sort_values(current_y, ascending=True).iloc[0]

    st.markdown(f'<div class="compact-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    col1, col2, col3 = responsive_columns(3, gap="medium")

    metric_plural = "Commendations" if metric_name == "Commendation" else "Complaints"
    # Executive cards should show whole-number counts.
    decimal_places = 0
    fmt = f"{{:,.{decimal_places}f}}"

    with col1:
        render_premium_card(
            f"Average {metric_plural} {current_y}",
            fmt.format(total_current),
            f"vs {previous_y}: {total_delta}",
            total_good,
        )
    with col2:
        high_delta, high_good = delta_html(
            float(high_row[current_y]),
            float(high_row[previous_y]),
            good_when_up=(metric_name == "Commendation"),
            decimals=0 if metric_name == "Commendation" else 1,
        )
        render_premium_card(
            f"Highest Avg {metric_name} Topic {current_y}",
            display_topic(str(high_row["Topic"])),
            f"{fmt.format(float(high_row[current_y]))} | vs {previous_y}: {high_delta}",
            high_good,
        )
    with col3:
        low_delta, low_good = delta_html(
            float(low_row[current_y]),
            float(low_row[previous_y]),
            good_when_up=(metric_name == "Commendation"),
            decimals=0 if metric_name == "Commendation" else 1,
        )
        render_premium_card(
            f"Lowest Avg {metric_name} Topic {current_y}",
            display_topic(str(low_row["Topic"])),
            f"{fmt.format(float(low_row[current_y]))} | vs {previous_y}: {low_delta}",
            low_good,
        )


def normalize_checkin_sheet(df: pd.DataFrame, label_candidates: List[str]) -> Tuple[pd.DataFrame, Optional[str]]:
    if df.empty:
        return pd.DataFrame(), None
    work = df.copy()
    if "Month" in work.columns:
        work["Month"] = work["Month"].apply(normalize_month_value)
        work = work[work["Month"].isin(selected_months)].copy()
    if work.empty:
        return pd.DataFrame(), None
    label_col = find_first_column(work, label_candidates)
    if label_col is None:
        ignore_cols = {"Month", "MonthDate", "Year", "MonthNum", "MonthName", "Percent", "Count", "RSP", "Responses"}
        label_cols = [c for c in work.columns if c not in ignore_cols and not pd.api.types.is_numeric_dtype(work[c])]
        label_col = label_cols[0] if label_cols else None
    if label_col is None:
        return pd.DataFrame(), None

    if "Count" in work.columns:
        work["Count"] = safe_numeric(work["Count"])
        out = work.groupby(label_col, as_index=False).agg({"Count": "sum"})
    elif "Responses" in work.columns:
        work["Count"] = safe_numeric(work["Responses"])
        out = work.groupby(label_col, as_index=False).agg({"Count": "sum"})
    elif "RSP" in work.columns:
        work["Count"] = safe_numeric(work["RSP"])
        out = work.groupby(label_col, as_index=False).agg({"Count": "sum"})
    elif "Percent" in work.columns:
        work["Percent"] = safe_numeric(work["Percent"])
        out = work.groupby(label_col, as_index=False).agg({"Percent": "mean"})
        out["Count"] = out["Percent"]
    else:
        return pd.DataFrame(), None
    out[label_col] = out[label_col].astype(str).str.strip()
    out = out[out[label_col] != ""].copy()
    return out.sort_values("Count", ascending=False), label_col


def render_checkin_extra_charts():
    if selected_canonical != "Check-in":
        return

    how_df = get_extra_sheet(
        extra_data,
        "how did you check-in for this trip",
        "how did you check in for this trip",
        "check-in method",
        "checkin method",
        "how_checkin",
        "how_check_in",
    )
    kiosk_df = get_extra_sheet(
        extra_data,
        "kiosk by age group",
        "kiosk age group",
        "kiosk_by_age_group",
        "checkin kiosk by age",
    )

    how_plot, how_label = normalize_checkin_sheet(
        how_df,
        ["How did you check-in", "Check-in Method", "Method", "Check in", "Check-in"],
    )
    kiosk_plot, kiosk_label = normalize_checkin_sheet(
        kiosk_df,
        ["Age Group", "Generation", "Age", "Kiosk by Age Group"],
    )

    if how_plot.empty and kiosk_plot.empty:
        return

    st.markdown('<div class="compact-section-title">Check-in Passenger Behavior</div>', unsafe_allow_html=True)
    c1, c2 = responsive_columns(2, gap="medium")
    with c1:
        if not how_plot.empty and how_label:
            plot_profile_donut(
                how_plot,
                how_label,
                "How did you check-in for this trip",
                [JAGGER, FLAMBOYANT_PINK, DASHING_YELLOW, "#7A4E9D", "#39D353"],
            )
        else:
            st.info("No check-in method data available.")
    with c2:
        if not kiosk_plot.empty and kiosk_label:
            plot_profile_donut(
                kiosk_plot,
                kiosk_label,
                "Kiosk by Age Group",
                [JAGGER, "#7A4E9D", FLAMBOYANT_PINK, DASHING_YELLOW, "#39D353", "#00A3E0"],
            )
        else:
            st.info("No kiosk by age group data available.")


# -----------------------------
# MAIN / DETAIL DATA
# -----------------------------
filtered_df = filter_rating_data(overall_df, selected_months, selected_topics)
if filtered_df.empty and selected_canonical == "Lavatory Cleanliness":
    st.warning("No rating data found for Lavatory Cleanliness. Complaint data may still be available below.")
elif filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

summary = create_touchpoint_summary(filtered_df)

# Current vs comparison-year period data for KPI deltas.
current_months = period_context["current_months"] or selected_months
previous_months = period_context["previous_months"]

current_df = filter_rating_data(overall_df, current_months, selected_topics)
previous_df = filter_rating_data(overall_df, previous_months, selected_topics)

current_summary = create_touchpoint_summary(current_df)
previous_summary = create_touchpoint_summary(previous_df)

current_csat = weighted_average(current_df, "CSAT")
previous_csat = weighted_average(previous_df, "CSAT") if not previous_df.empty else None
current_rating = weighted_average(current_df, "Average Rating")
previous_rating = weighted_average(previous_df, "Average Rating") if not previous_df.empty else None
total_rsp = get_total_responses(overall_df, monthly_response_df, selected_months)

if selected_canonical == "All Touchpoints":
    best_row = summary.sort_values("Average Rating", ascending=False).head(1)
    low_row = summary.sort_values("Average Rating", ascending=True).head(1)
else:
    best_row = summary
    low_row = summary

best_topic_text = display_topic(best_row.iloc[0]["Topic"]) if not best_row.empty else "n/a"
best_rating_value = float(best_row.iloc[0]["Average Rating"]) if not best_row.empty else 0.0
low_topic_text = display_topic(low_row.iloc[0]["Topic"]) if not low_row.empty else "n/a"
low_rating_value = float(low_row.iloc[0]["Average Rating"]) if not low_row.empty else 0.0


# -----------------------------
# KPI ROW
# -----------------------------
if selected_canonical == "All Touchpoints":
    kpi_cols = responsive_columns(5, gap="medium")
    csat_delta, _ = delta_html(current_csat, previous_csat, unit=" pp", good_when_up=True)
    rating_delta, _ = delta_html(current_rating, previous_rating, good_when_up=True)

    previous_total_rsp = get_total_responses(overall_df, monthly_response_df, previous_months) if previous_months else None
    rsp_delta, _ = delta_html(total_rsp, previous_total_rsp, good_when_up=True, decimals=0)

    with kpi_cols[0]:
        render_overview_card("⭐", "Overall CSAT", f"{current_csat:.2f}%", csat_delta)
    with kpi_cols[1]:
        render_overview_card("📈", "Average Rating", f"{current_rating:.2f}", rating_delta)
    with kpi_cols[2]:
        render_overview_card("👥", "Total Responses", f"{total_rsp:,}", rsp_delta)
    with kpi_cols[3]:
        render_overview_card("🏆", "Best Touchpoint", best_topic_text, f"<span class='delta-neutral'>Rating {best_rating_value:.2f}</span>")
    with kpi_cols[4]:
        render_overview_card("⚠️", "Needs Improvement", low_topic_text, f"<span class='delta-neutral'>Rating {low_rating_value:.2f}</span>")

else:
    # Detail page KPI cards.
    comp_detail = get_complaint_working_df(complaint_summary_df, selected_topics)
    selected_current_comp = comp_detail[comp_detail["Month"].isin(current_months)].copy()
    selected_previous_comp = comp_detail[comp_detail["Month"].isin(previous_months)].copy()

    def avg_monthly_metric(source: pd.DataFrame, metric_name: str) -> float:
        if source.empty:
            return 0.0
        part = source[source["Metric"] == metric_name].copy()
        if part.empty:
            return 0.0
        monthly = part.groupby("Month", as_index=False).agg({"Complaint Count": "sum"})
        if monthly.empty:
            return 0.0
        return float(monthly["Complaint Count"].mean())

    current_avg_complaint = avg_monthly_metric(selected_current_comp, "Complaint")
    previous_avg_complaint = avg_monthly_metric(selected_previous_comp, "Complaint") if previous_months else None
    current_avg_commend = avg_monthly_metric(selected_current_comp, "Commendation")
    previous_avg_commend = avg_monthly_metric(selected_previous_comp, "Commendation") if previous_months else None

    complaint_delta, complaint_good = delta_html(current_avg_complaint, previous_avg_complaint, good_when_up=False, decimals=1)
    commend_delta, commend_good = delta_html(current_avg_commend, previous_avg_commend, good_when_up=True, decimals=1)
    rating_delta, _ = delta_html(current_rating, previous_rating, good_when_up=True)

    kpi_cols = responsive_columns(4, gap="medium")
    with kpi_cols[0]:
        render_overview_card("📈", "Average Rating YoY", f"{current_rating:.2f}", rating_delta)
    with kpi_cols[1]:
        render_overview_card("👥", "Total Responses", f"{total_rsp:,}", "")
    with kpi_cols[2]:
        render_overview_card("📊", "Average Complaint YoY", f"{current_avg_complaint:,.0f}", complaint_delta)
    with kpi_cols[3]:
        render_overview_card("✅", "Average Commendation YoY", f"{current_avg_commend:,.0f}", commend_delta)

    render_checkin_extra_charts()


# -----------------------------
# MAIN DASHBOARD RENDERING
# -----------------------------
if selected_canonical == "All Touchpoints":
    # Executive overview order requested by management.
    render_passenger_profile()
    render_passenger_class_responses()
    render_nationalities_heatmap()

    render_touchpoint_stacked_bar(summary, horizontal=False)

    bottom_left, bottom_right = responsive_columns([1.05, 1], gap="medium")
    with bottom_left:
        render_touchpoint_ranking_table(summary)
    with bottom_right:
        st.markdown('<div class="compact-section-title">CSAT Trend Line</div>', unsafe_allow_html=True)
        render_csat_trend(selected_topics, "CSAT Trend Line: YoY 2025 vs 2026")

    render_average_metric_cards("Complaint", f"Average Complaint: {current_year} vs {previous_year}")
    render_average_metric_cards("Commendation", f"Average Commendation: {current_year} vs {previous_year}")

    st.markdown('<div class="compact-section-title">Complaint and Commendation Trend YoY</div>', unsafe_allow_html=True)
    render_complaint_trend(selected_topics, include_commendation=True, title="Complaint and Commendation Trend YoY")

    render_top_complaints_table(selected_topics)

else:
    # Single touchpoint view: left = satisfaction bar, right = CSAT line trend.
    touch_left, touch_right = responsive_columns([1, 1], gap="medium")
    with touch_left:
        st.markdown('<div class="compact-section-title">5-Scale Distribution</div>', unsafe_allow_html=True)
        render_touchpoint_stacked_bar(summary, horizontal=True)
    with touch_right:
        st.markdown('<div class="compact-section-title">CSAT Line Trend</div>', unsafe_allow_html=True)
        render_csat_trend(selected_topics, f"{display_topic(selected_canonical)} - CSAT Line Trend: YoY")

    if selected_canonical in ["Arrival & Baggage", "Boarding", "Lounge", "Irregularity"]:
        render_station_satisfaction_map(selected_canonical)

    line_col, topic_col = responsive_columns([1, 1.08], gap="medium")
    with line_col:
        st.markdown('<div class="compact-section-title">Total Complaint Line Trend</div>', unsafe_allow_html=True)
        render_complaint_trend(
            selected_topics,
            include_commendation=True,
            title=f"{display_topic(selected_canonical)} - Complaint and Commendation Trend YoY",
            height=600 if not IS_MOBILE_MODE else 480,
        )

    with topic_col:
        st.markdown('<div class="compact-section-title">Complaint by Topic</div>', unsafe_allow_html=True)
        comp_detail = get_complaint_working_df(complaint_summary_df, selected_topics)
        if comp_detail.empty:
            st.info("No complaint topic data available.")
        else:
            years_available = sorted(comp_detail["Year"].dropna().astype(int).unique().tolist())
            target_years = [y for y in [previous_year, current_year] if y in years_available]
            if not target_years:
                target_years = years_available[-2:] if len(years_available) >= 2 else years_available

            topic_comp = comp_detail[(comp_detail["Year"].isin(target_years)) & (~comp_detail["Is Commendation"])].copy()

            if topic_comp.empty:
                st.info("No complaint topic data available.")
            else:
                detail_avg = (
                    topic_comp.groupby(["Year", "Complaint Topic"], as_index=False)
                    .agg({"Complaint Count": "mean"})
                    .rename(columns={"Complaint Count": "Average Complaint Count"})
                )
                pivot = detail_avg.pivot(index="Complaint Topic", columns="Year", values="Average Complaint Count").reset_index().fillna(0)
                for year_value in target_years:
                    if year_value not in pivot.columns:
                        pivot[year_value] = 0
                sort_year = target_years[-1]
                pivot = pivot.sort_values(sort_year, ascending=False).head(10)
                pivot["Wrapped Complaint Topic"] = pivot["Complaint Topic"].apply(lambda x: wrap_axis_label(x, 38))
                order_topics = pivot["Wrapped Complaint Topic"].tolist()[::-1]
                dynamic_bar_height = max(600 if not IS_MOBILE_MODE else 480, 180 + 82 * max(1, len(pivot)))

                fig = go.Figure()
                ordered_years_for_bar = list(target_years)
                for year_value in ordered_years_for_bar:
                    color_value = DASHING_YELLOW if year_value == target_years[0] else FLAMBOYANT_PINK
                    fig.add_trace(
                        go.Bar(
                            x=pivot[year_value],
                            y=pivot["Wrapped Complaint Topic"],
                            name=str(year_value),
                            orientation="h",
                            marker_color=color_value,
                            text=[f"{v:,.0f}" for v in pivot[year_value]],
                            textposition="outside",
                            customdata=pivot[["Complaint Topic"]],
                            hovertemplate=f"<b>%{{customdata[0]}}</b><br>Year: {year_value}<br>Average Complaint Count: %{{x:,.0f}}<extra></extra>",
                        )
                    )
                fig.update_layout(
                    barmode="group",
                    title=f"{display_topic(selected_canonical)} - Complaint by Topic: YoY",
                    xaxis_title="Average Complaint Count",
                    yaxis_title="",
                    legend_title_text="Year",
                    legend=dict(orientation="h", yanchor="bottom", y=1.10, xanchor="center", x=0.5, traceorder="normal"),
                    margin=dict(l=280, r=60, t=112, b=56),
                )
                apply_plot_layout(fig, height=dynamic_bar_height, title_size=18)
                fig.update_yaxes(categoryorder="array", categoryarray=order_topics, tickfont=dict(size=11, color=TEXT_MAIN), automargin=True)
                fig.update_xaxes(automargin=True)
                st.plotly_chart(fig, use_container_width=True)

    render_top_complaints_table(selected_topics)

# -----------------------------
# DATA TABLES
# -----------------------------
with st.expander("Show Filtered Rating Data"):
    display_df = filtered_df.copy()
    display_df["Display Topic"] = display_df["Topic"].apply(display_topic)
    dataframe_white(display_df, height=420)
