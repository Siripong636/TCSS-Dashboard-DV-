import os
import re
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# -----------------------------
# BRAND COLORS
# -----------------------------
JAGGER = "#370E62"
DASHING_YELLOW = "#F5C300"
FLAMBOYANT_PINK = "#B6007D"

DARK_BG = "#FFFFFF"
CARD_BG = "#FFFFFF"
PLOT_BG = "#FFFFFF"
PAGE_BG = "#FFFFFF"
SIDEBAR_BG = "#FFFFFF"
TEXT_MAIN = "#111827"
TEXT_MUTED = "#6B7280"
BORDER = "#E5E7EB"
CARD_SHADOW = "0 12px 30px rgba(17, 24, 39, 0.08)"

GREEN_GOOD = "#16A34A"
ORANGE_LOW = "#ED7D31"

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

# Required display/order for complaint and satisfaction sections.
# Internal normalized topic names are kept stable for data matching.
ALLOWED_COMPLAINT_TOPICS = [
    "Check-in",
    "Lounge",
    "Boarding",
    "Cabin Cleanliness",
    "Lavatory Dirty",
    "In-flight Meal",
    "In-flight Beverage",
    "Arrival & Baggage",
    "Irregularity",
]

RAW_COMPLAINT_TOPIC_ALLOWLIST = [
    "Check-in",
    "Lounge",
    "Cabin Cleanliness",
    "Inflight Meal (DC double catering)",
    "In-flight Beverage",
    "Arrival & Baggage Handling",
    "Irregularity Handling",
    "Boarding",
    "Lavatory Dirty",
]

# Rating trend shows only these touchpoints.
# Some source files use slightly different names, so we normalize before filtering.
ALLOWED_RATING_TREND_TOPICS = [
    "Check-in",
    "Lounge",
    "Boarding",
    "Cabin Cleanliness",
    "Lavatory Dirty",
    "In-flight Meal",
    "In-flight Beverage",
    "Arrival & Baggage",
    "Irregularity",
]

TOPIC_TICK_LABELS = {
    "Check-in": "Check-in",
    "Lounge": "Lounge",
    "Boarding": "Boarding",
    "Cabin Cleanliness": "Cabin<br>Cleanliness",
    "Lavatory Dirty": "Lavatory Dirty",
    "In-flight Meal": "In-flight<br>Meal",
    "In-flight Beverage": "In-flight<br>Beverage",
    "Arrival & Baggage": "Arrival Baggage<br>Handling",
    "Irregularity": "Irregularity<br>Handling",
}

CLASS_CARD_STYLE = {
    "First Class": {"short": "F", "bg": "#FFE38A", "fg": "#111827", "icon": "👑"},
    "Business Class": {"short": "BC", "bg": "#7030A0", "fg": "#FFFFFF", "icon": "💼"},
    "Economy Plus": {"short": "EY Plus", "bg": "#B6007D", "fg": "#FFFFFF", "icon": "✨"},
    "Economy Class": {"short": "EY", "bg": "#C000A0", "fg": "#FFFFFF", "icon": "🧳"},
}


# -----------------------------
# STATION COORDINATES
# -----------------------------
STATION_COORDINATES = [
    {"Station": "Bangkok", "Latitude": 13.6900, "Longitude": 100.7501},
    {"Station": "UTAPAO", "Latitude": 12.6799, "Longitude": 101.0050},
    {"Station": "U-Tapao", "Latitude": 12.6799, "Longitude": 101.0050},
    {"Station": "U Tapao", "Latitude": 12.6799, "Longitude": 101.0050},
    {"Station": "U-Tapao Rayong Pattaya", "Latitude": 12.6799, "Longitude": 101.0050},
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
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="TCSS Dashboard",
    layout="wide"
)


# -----------------------------
# CUSTOM CSS
# -----------------------------
css = r"""
<style>
:root {
    --jagger: {JAGGER};
    --yellow: {DASHING_YELLOW};
    --pink: {FLAMBOYANT_PINK};
    --text-main: {TEXT_MAIN};
    --text-muted: {TEXT_MUTED};
    --border: {BORDER};
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: {PAGE_BG} !important;
    color: {TEXT_MAIN} !important;
    font-family: "Segoe UI", "Inter", "Arial", sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.92) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid {BORDER};
}

section[data-testid="stSidebar"] {
    background: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER};
}

section[data-testid="stSidebar"] * {
    color: {TEXT_MAIN} !important;
}

.block-container {
    padding-top: 2.2rem;
    padding-left: clamp(1rem, 2.5vw, 3.2rem);
    padding-right: clamp(1rem, 2.5vw, 3.2rem);
    padding-bottom: 4rem;
    max-width: 100% !important;
    width: 100% !important;
}

h1 {
    color: {TEXT_MAIN} !important;
    font-size: 3.1rem !important;
    line-height: 1.08 !important;
    font-weight: 850 !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0.5rem !important;
}

h2, h3 {
    color: {TEXT_MAIN} !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

h2 { font-size: 2.25rem !important; margin-top: 2.2rem !important; }
h3 { font-size: 1.75rem !important; margin-top: 1.8rem !important; }

p, span, div, label {
    font-size: 1.02rem;
}

[data-testid="stCaptionContainer"] {
    color: {TEXT_MUTED} !important;
    font-size: 1.05rem !important;
}

/* Premium metric cards for st.metric */
div[data-testid="stMetric"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #FCFCFD 100%);
    border-radius: 20px;
    padding: 22px 22px;
    border: 1px solid {BORDER};
    box-shadow: {CARD_SHADOW};
    min-height: 132px;
}

div[data-testid="stMetricLabel"] p {
    color: {TEXT_MUTED} !important;
    font-size: 1.02rem !important;
    font-weight: 750 !important;
}

div[data-testid="stMetricValue"] div {
    color: {JAGGER} !important;
    font-size: 2.05rem !important;
    font-weight: 850 !important;
    letter-spacing: -0.03em !important;
}

div[data-testid="stMetricDelta"] div {
    font-size: 1rem !important;
    font-weight: 700 !important;
}

.premium-card {
    background: linear-gradient(180deg, #FFFFFF 0%, #FCFCFD 100%);
    border: 1px solid {BORDER};
    border-radius: 22px;
    padding: 22px 24px;
    box-shadow: {CARD_SHADOW};
    min-height: 140px;
}

.premium-label {
    color: {TEXT_MUTED} !important;
    font-size: 1.02rem !important;
    font-weight: 750 !important;
    margin-bottom: 8px;
}

.premium-value {
    color: {JAGGER} !important;
    font-size: 2.05rem !important;
    line-height: 1.15 !important;
    font-weight: 850 !important;
    letter-spacing: -0.03em !important;
    word-break: break-word;
}

.premium-delta {
    margin-top: 10px;
    font-size: 1rem !important;
    font-weight: 800 !important;
}

/* Filters: white background + black text */
.stMultiSelect div[data-baseweb="select"] > div,
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: {TEXT_MAIN} !important;
    border: 1.5px solid {BORDER} !important;
    border-radius: 14px !important;
    min-height: 48px !important;
}

.stMultiSelect [data-baseweb="tag"] {
    background-color: transparent !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    box-shadow: none !important;
}

.stMultiSelect [data-baseweb="tag"] span {
    color: {TEXT_MAIN} !important;
}

.stMultiSelect [data-baseweb="tag"] svg {
    color: {TEXT_MAIN} !important;
    fill: {TEXT_MAIN} !important;
}

.stSelectbox div[data-baseweb="select"] span,
.stMultiSelect div[data-baseweb="select"] span,
.stTextInput input {
    color: {TEXT_MAIN} !important;
}

[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #FFFFFF !important;
    color: {TEXT_MAIN} !important;
}

[data-baseweb="menu"] li, [role="option"] {
    color: {TEXT_MAIN} !important;
    background-color: #FFFFFF !important;
    font-size: 1.02rem !important;
}

[data-baseweb="menu"] li:hover, [role="option"]:hover {
    background-color: #F3F4F6 !important;
}


/* Dataframe/table: force white surface + black text where Streamlit allows CSS override */
[data-testid="stDataFrame"] div,
[data-testid="stDataFrame"] span,
[data-testid="stDataFrame"] p {
    color: {TEXT_MAIN} !important;
}

[data-testid="stDataFrame"] {
    background: #FFFFFF !important;
    border: 1px solid {BORDER} !important;
    box-shadow: {CARD_SHADOW};
}

/* Premium colored cards */
.premium-card.good-card {
    background: linear-gradient(135deg, #ECFDF5 0%, #FFFFFF 72%) !important;
    border-color: #86EFAC !important;
}

.premium-card.bad-card {
    background: linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 72%) !important;
    border-color: #FDBA74 !important;
}

.card-icon {
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #F3F4F6;
    margin-bottom: 10px;
    font-size: 1.25rem !important;
}

.class-card {
    border-radius: 20px;
    padding: 18px 20px;
    min-height: 124px;
    box-shadow: {CARD_SHADOW};
    border: 1px solid rgba(17, 24, 39, 0.10);
}

.class-short {
    font-size: 1.65rem !important;
    line-height: 1 !important;
    font-weight: 900 !important;
    margin-bottom: 10px;
}

.class-label {
    font-size: 0.95rem !important;
    font-weight: 800 !important;
    opacity: 0.95;
    margin-bottom: 8px;
}

.class-value {
    font-size: 2.05rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em !important;
}

.station-mini-card .premium-value {
    font-size: 1.35rem !important;
    line-height: 1.12 !important;
    white-space: nowrap;
}

.station-mini-card .premium-label {
    font-size: 0.82rem !important;
}

hr {
    border-color: {BORDER};
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}

button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {BORDER} !important;
}


/* Force all visible text on white dashboard to be readable */
.main, .block-container, .element-container, .stMarkdown, .stMarkdown *,
[data-testid="stMetric"], [data-testid="stMetric"] *,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
[data-testid="stDataFrame"], [data-testid="stDataFrame"] * {
    color: {TEXT_MAIN} !important;
}

/* Data tables: white background and black text */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] div[role="grid"],
[data-testid="stDataFrame"] div[role="row"],
[data-testid="stDataFrame"] div[role="gridcell"],
[data-testid="stDataFrame"] div[role="columnheader"] {
    background-color: #FFFFFF !important;
    color: {TEXT_MAIN} !important;
}

[data-testid="stDataFrame"] canvas {
    background-color: #FFFFFF !important;
}

/* Plotly axis and legend readability */
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly .xtitle,
.js-plotly-plot .plotly .ytitle,
.js-plotly-plot .plotly .legend text,
.js-plotly-plot .plotly .legendtitletext,
.js-plotly-plot .plotly .colorbar text {
    fill: {TEXT_MAIN} !important;
    color: {TEXT_MAIN} !important;
}


/* Main section titles: bigger than subsection titles */
.main-section-title {
    color: #111827 !important;
    font-size: clamp(1.7rem, 2.2vw, 2.5rem) !important;
    line-height: 1.15 !important;
    font-weight: 900 !important;
    letter-spacing: -0.035em !important;
    margin: 2.6rem 0 1.25rem 0 !important;
}

/* Subsection headings */
h3 {
    font-size: clamp(1.15rem, 1.45vw, 1.55rem) !important;
    color: #111827 !important;
}

/* HTML light tables */
.light-table-wrap {
    width: 100%;
    overflow: auto;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    background: #FFFFFF;
    box-shadow: 0 12px 30px rgba(17, 24, 39, 0.08);
}
.light-table {
    width: 100%;
    border-collapse: collapse;
    background: #FFFFFF !important;
    color: #111827 !important;
    font-size: 0.98rem;
}
.light-table thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: #F8FAFC !important;
    color: #111827 !important;
    font-weight: 900;
    border-bottom: 1px solid #E5E7EB;
    padding: 0.7rem 0.85rem;
    text-align: left;
    white-space: nowrap;
}
.light-table tbody td, .light-table tbody th {
    background: #FFFFFF !important;
    color: #111827 !important;
    border-bottom: 1px solid #EEF2F7;
    padding: 0.62rem 0.85rem;
    vertical-align: top;
}
.light-table tbody tr:nth-child(even) td,
.light-table tbody tr:nth-child(even) th {
    background: #F9FAFB !important;
}
.light-table tbody tr:hover td,
.light-table tbody tr:hover th {
    background: #FFF7E6 !important;
}

/* Make Streamlit widgets responsive */
[data-testid="stHorizontalBlock"] {
    gap: 1.25rem;
}

@media (max-width: 900px) {
    .block-container {
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-top: 1.2rem !important;
    }
    h1 {
        font-size: 2.1rem !important;
    }
    .main-section-title {
        font-size: 1.55rem !important;
        margin-top: 1.8rem !important;
    }
    .premium-card, .class-card {
        min-height: auto !important;
        padding: 16px 18px !important;
    }
    .premium-value, .class-value {
        font-size: 1.55rem !important;
    }
    .light-table {
        font-size: 0.9rem !important;
    }
}

</style>
"""
for _css_key, _css_value in {
    "JAGGER": JAGGER,
    "DASHING_YELLOW": DASHING_YELLOW,
    "FLAMBOYANT_PINK": FLAMBOYANT_PINK,
    "TEXT_MAIN": TEXT_MAIN,
    "TEXT_MUTED": TEXT_MUTED,
    "BORDER": BORDER,
    "PAGE_BG": PAGE_BG,
    "SIDEBAR_BG": SIDEBAR_BG,
    "CARD_SHADOW": CARD_SHADOW,
}.items():
    css = css.replace("{" + _css_key + "}", str(_css_value))

st.markdown(css, unsafe_allow_html=True)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def extract_month_from_file(filename):
    match = re.search(r"(\d{6})", str(filename))
    if match:
        ym = match.group(1)
        return f"{ym[:4]}-{ym[4:]}"
    return ""


def clean_text(text):
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def normalize_key(value):
    text = clean_text(value).upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def normalize_station_name(value):
    return normalize_key(value)


def normalize_station_touchpoint(value):
    compact = normalize_key(value)

    if "ARRIVAL" in compact or "BAGGAGE" in compact:
        return "Arrival & Baggage"

    if "BOARDING" in compact:
        return "Boarding"

    if "LOUNGE" in compact:
        return "Lounge"

    if "IRREGULARITY" in compact:
        return "Irregularity"

    return clean_text(value)


def normalize_nationality_group(value):
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
    if "africa" in text or "african" in text:
        return "African"
    if "aus" in text or "australia" in text or "new zealand" in text or "nz" in text:
        return "AUS & NZ"
    if "asia" in text or "asian" in text:
        return "Asian"
    if "other" in text:
        return "Others"

    return clean_text(value)


def parse_month_column(col):
    text = str(col).strip()

    if re.match(r"^[A-Za-z]{3}-\d{2}$", text):
        return pd.to_datetime("01-" + text, format="%d-%b-%y", errors="coerce")

    parsed = pd.to_datetime(col, errors="coerce")

    if pd.notna(parsed):
        return parsed

    return pd.NaT


def get_latest_month(selected_months):
    if not selected_months:
        return None

    month_df = pd.DataFrame({"Month": selected_months})
    month_df["MonthDate"] = pd.to_datetime(
        month_df["Month"] + "-01",
        errors="coerce"
    )

    month_df = month_df.dropna()

    if month_df.empty:
        return selected_months[-1]

    return month_df.sort_values("MonthDate")["Month"].iloc[-1]

def get_selected_month_label(selected_months):
    if not selected_months:
        return ""

    temp = pd.DataFrame({"Month": selected_months})
    temp["MonthDate"] = pd.to_datetime(temp["Month"] + "-01", errors="coerce")
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
            start_label = temp["MonthDate"].iloc[0].strftime("%b")
            end_label = temp["MonthDate"].iloc[-1].strftime("%b")
            return f"{start_label}-{end_label} {year}"

        month_labels = ", ".join(temp["MonthDate"].dt.strftime("%b").tolist())
        return f"{month_labels} {year}"

    return f"{temp['MonthDate'].iloc[0].strftime('%b %Y')} - {temp['MonthDate'].iloc[-1].strftime('%b %Y')}"


def get_icon_for_card(label, good=None):
    label_lower = str(label).lower()
    if "top complaint" in label_lower:
        return "💬"
    if "complaint" in label_lower:
        return "📊"
    if "csat" in label_lower:
        return "⭐"
    if "rating" in label_lower:
        return "📈"
    if "rsp" in label_lower or "response" in label_lower:
        return "👥"
    if "lowest" in label_lower:
        return "⚠️"
    if good is True:
        return "✅"
    if good is False:
        return "🔶"
    return "✦"


def render_premium_card(label, value, delta=None, good=None, small=False):
    if delta is None:
        delta_html = ""
    else:
        delta_color = TEXT_MUTED
        if good is True:
            delta_color = GREEN_GOOD
        elif good is False:
            delta_color = ORANGE_LOW

        delta_html = f'<div class="premium-delta" style="color:{delta_color}!important;">{delta}</div>'

    tone_class = ""
    if good is True:
        tone_class = " good-card"
    elif good is False:
        tone_class = " bad-card"

    small_class = " station-mini-card" if small else ""
    icon = get_icon_for_card(label, good)

    st.markdown(
        f"""
        <div class="premium-card{tone_class}{small_class}">
            <div class="card-icon">{icon}</div>
            <div class="premium-label">{label}</div>
            <div class="premium-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_class_card(class_name, value):
    style = CLASS_CARD_STYLE.get(
        class_name,
        {"short": class_name, "bg": JAGGER, "fg": "#FFFFFF", "icon": "✈️"}
    )
    st.markdown(
        f"""
        <div class="class-card" style="background:{style['bg']}; color:{style['fg']}!important;">
            <div class="class-short" style="color:{style['fg']}!important;">{style['icon']} {style['short']}</div>
            <div class="class-label" style="color:{style['fg']}!important;">{class_name}</div>
            <div class="class-value" style="color:{style['fg']}!important;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def apply_premium_plot_layout(fig, height=None, title_size=22, show_grid=True):
    fig.update_layout(
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_MAIN, size=16, family="Segoe UI, Inter, Arial"),
        title=dict(font=dict(size=title_size, color=TEXT_MAIN, family="Segoe UI, Inter, Arial")),
        legend=dict(
            font=dict(size=14, color=TEXT_MAIN),
            title_font=dict(color=TEXT_MAIN, size=14),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=BORDER,
            borderwidth=0
        ),
        margin=dict(l=56, r=56, t=82, b=76),
        xaxis=dict(
            title_font=dict(color=TEXT_MAIN, size=16),
            tickfont=dict(color=TEXT_MAIN, size=14),
            color=TEXT_MAIN,
            linecolor="#CBD5E1"
        ),
        yaxis=dict(
            title_font=dict(color=TEXT_MAIN, size=16),
            tickfont=dict(color=TEXT_MAIN, size=14),
            color=TEXT_MAIN,
            linecolor="#CBD5E1"
        )
    )

    if height is not None:
        fig.update_layout(height=height)

    if show_grid:
        fig.update_xaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB", linecolor="#CBD5E1")
        fig.update_yaxes(gridcolor="#E5E7EB", zerolinecolor="#D1D5DB", linecolor="#CBD5E1")
    else:
        fig.update_xaxes(showgrid=False, linecolor="#CBD5E1")
        fig.update_yaxes(showgrid=False, linecolor="#CBD5E1")

    fig.update_xaxes(tickfont=dict(color=TEXT_MAIN), title_font=dict(color=TEXT_MAIN), color=TEXT_MAIN)
    fig.update_yaxes(tickfont=dict(color=TEXT_MAIN), title_font=dict(color=TEXT_MAIN), color=TEXT_MAIN)

    return fig


def aggregate_profile_for_selected_months(profile_df, selected_months, label_col):
    if profile_df.empty or label_col not in profile_df.columns:
        return pd.DataFrame()

    temp = profile_df[profile_df["Month"].isin(selected_months)].copy()

    if temp.empty:
        return temp

    temp[label_col] = temp[label_col].astype(str).str.strip()

    if "Count" in temp.columns:
        temp["Count"] = pd.to_numeric(temp["Count"], errors="coerce").fillna(0)

        result = (
            temp
            .groupby(label_col, as_index=False)
            .agg({"Count": "sum"})
        )

        total = result["Count"].sum()
        result["Percent"] = result["Count"] / total * 100 if total > 0 else 0
        return result.sort_values("Count", ascending=False)

    if "Percent" in temp.columns:
        temp["Percent"] = pd.to_numeric(temp["Percent"], errors="coerce").fillna(0)

        result = (
            temp
            .groupby(label_col, as_index=False)
            .agg({"Percent": "mean"})
        )

        total = result["Percent"].sum()
        result["Percent"] = result["Percent"] / total * 100 if total > 0 else 0
        return result.sort_values("Percent", ascending=False)

    return pd.DataFrame()


def plot_profile_donut(plot_df, label_col, title, colors):
    if plot_df.empty:
        st.info(f"No data for {title}")
        return

    value_col = "Count" if "Count" in plot_df.columns and plot_df["Count"].sum() > 0 else "Percent"

    fig = px.pie(
        plot_df,
        names=label_col,
        values=value_col,
        hole=0.55,
        title=title,
        color_discrete_sequence=colors
    )

    fig.update_traces(
        textinfo="percent",
        textfont_size=15,
        marker=dict(line=dict(color="#FFFFFF", width=2))
    )

    apply_premium_plot_layout(fig, height=460, title_size=22, show_grid=False)
    fig.update_layout(
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center", font=dict(size=12, color=TEXT_MAIN)),
        margin=dict(l=10, r=10, t=70, b=80)
    )

    st.plotly_chart(fig, width="stretch")


def format_delta_value(current_value, previous_value, inverse_good=True):
    change = current_value - previous_value

    if previous_value == 0 and current_value > 0:
        delta_text = f"{change:+,.1f} (New)"
    elif previous_value == 0:
        delta_text = "0.0 (0.0%)"
    else:
        pct = change / previous_value * 100
        delta_text = f"{change:+,.1f} ({pct:+.1f}%)"

    good = change <= 0 if inverse_good else change >= 0
    return delta_text, good



def light_table_style(styler):
    return (
        styler
        .set_properties(**{
            "background-color": "#FFFFFF",
            "color": TEXT_MAIN,
            "border-color": BORDER,
            "font-size": "14px"
        })
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#F8FAFC"), ("color", TEXT_MAIN), ("font-weight", "800"), ("border-color", BORDER)]},
            {"selector": "td", "props": [("background-color", "#FFFFFF"), ("color", TEXT_MAIN), ("border-color", BORDER)]},
            {"selector": "tbody tr:nth-child(even) td", "props": [("background-color", "#F9FAFB")]},
        ])
    )


def section_header(title):
    st.markdown(
        f'<div class="main-section-title">{title}</div>',
        unsafe_allow_html=True
    )


def render_light_table(df, height=420, formats=None, hide_index=True):
    """Render a readable white-background HTML table instead of dark Streamlit grid."""
    if df is None or df.empty:
        st.info("No data available.")
        return

    display_df = df.copy()

    if formats:
        for col, fmt in formats.items():
            if col in display_df.columns:
                def _fmt_val(v, fmt=fmt):
                    try:
                        if pd.isna(v):
                            return ""
                        return fmt.format(v)
                    except Exception:
                        return str(v)
                display_df[col] = display_df[col].apply(_fmt_val)

    html = display_df.to_html(index=not hide_index, escape=False, classes="light-table")
    st.markdown(
        f'<div class="light-table-wrap" style="max-height:{height}px;">{html}</div>',
        unsafe_allow_html=True
    )


# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("clean_tcss_rating.xlsx")
    df.columns = df.columns.astype(str).str.strip()

    df["Month"] = df["Month"].astype(str).str.strip()
    df["Topic"] = df["Topic"].astype(str).str.strip()
    df["Segment"] = df["Segment"].astype(str).str.strip()

    df["Segment"] = df["Segment"].replace({
        "Economy I": "Economy Plus",
        "Economy l": "Economy Plus",
        "Economy P": "Economy Plus"
    })

    numeric_cols = [
        "Very satisfied",
        "Satisfied",
        "Acceptable",
        "Dissatisfied",
        "Very dissatisfied",
        "RSP",
        "CSAT",
        "Average Rating"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["MonthDate"] = pd.to_datetime(df["Month"] + "-01", errors="coerce")
    df = df[df["MonthDate"].notna()].copy()

    df["Year"] = df["MonthDate"].dt.year.astype(int)
    df["MonthNum"] = df["MonthDate"].dt.month.astype(int)
    df["MonthName"] = df["MonthNum"].map(MONTH_NAME)

    df = df.sort_values(
        ["Month", "Topic", "Segment", "RSP"],
        ascending=[True, True, True, False]
    )

    df = df.drop_duplicates(
        subset=["Month", "Topic", "Segment"],
        keep="first"
    )

    return df


@st.cache_data
def load_raw_text():
    if not os.path.exists("master_tcss.xlsx"):
        return pd.DataFrame()

    raw_df = pd.read_excel("master_tcss.xlsx")
    raw_df.columns = raw_df.columns.astype(str).str.strip()

    if "File" not in raw_df.columns or "Content" not in raw_df.columns:
        return pd.DataFrame()

    raw_df["Month"] = raw_df["File"].apply(extract_month_from_file)
    raw_df["Content"] = raw_df["Content"].astype(str)

    return raw_df


@st.cache_data
def load_extra_data():
    if not os.path.exists("extra_tcss.xlsx"):
        return {}

    sheets = {}
    xls = pd.ExcelFile("extra_tcss.xlsx")

    for sheet in xls.sheet_names:
        temp_df = pd.read_excel("extra_tcss.xlsx", sheet_name=sheet)
        temp_df.columns = temp_df.columns.astype(str).str.strip()

        if "Month" in temp_df.columns:
            temp_df["Month"] = temp_df["Month"].astype(str).str.strip()

        numeric_columns = [
            "Percent",
            "Count",
            "Satisfaction 5-4",
            "Neutral 3",
            "Dissatisfaction 2-1",
            "RSP"
        ]

        for col in numeric_columns:
            if col in temp_df.columns:
                temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")

        sheets[sheet] = temp_df

    return sheets


@st.cache_data
def load_station_coordinates():
    built_in_df = pd.DataFrame(STATION_COORDINATES)
    coord_sources = [built_in_df]

    if os.path.exists("station_coordinates.xlsx"):
        user_coord_df = pd.read_excel("station_coordinates.xlsx")
        coord_sources.append(user_coord_df)
    elif os.path.exists("station_coordinates.csv"):
        user_coord_df = pd.read_csv("station_coordinates.csv")
        coord_sources.append(user_coord_df)

    coord_df = pd.concat(coord_sources, ignore_index=True)
    coord_df.columns = coord_df.columns.astype(str).str.strip()

    coord_df["Station"] = coord_df["Station"].astype(str).str.strip()
    coord_df["Latitude"] = pd.to_numeric(coord_df["Latitude"], errors="coerce")
    coord_df["Longitude"] = pd.to_numeric(coord_df["Longitude"], errors="coerce")

    coord_df = coord_df.dropna(subset=["Latitude", "Longitude"])
    coord_df["StationKey"] = coord_df["Station"].apply(normalize_station_name)

    coord_df = coord_df.drop_duplicates(
        subset=["StationKey"],
        keep="last"
    )

    return coord_df


# -----------------------------
# TOTAL RESPONSE + CLASS FROM SUMMARY PAGE
# -----------------------------
def extract_monthly_response_counts(raw_df):
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
            r"responses\s+([0-9,]+)"
        ]

        found_values = []

        for pattern in patterns:
            matches = re.findall(pattern, content, flags=re.IGNORECASE)

            for match in matches:
                try:
                    found_values.append(int(str(match).replace(",", "")))
                except Exception:
                    pass

        if found_values:
            records.append({
                "Month": month,
                "Responses": max(found_values)
            })

    result_df = pd.DataFrame(records)

    if result_df.empty:
        return pd.DataFrame(columns=["Month", "Responses"])

    result_df = (
        result_df
        .groupby("Month", as_index=False)
        .agg({"Responses": "max"})
    )

    return result_df


def extract_class_responses_from_raw_text(raw_df):
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=["Month", "Class", "Responses"])

    class_map = {
        "F": "First Class",
        "C": "Business Class",
        "PY": "Economy Plus",
        "EY": "Economy Class"
    }

    records = []

    for _, row in raw_df.iterrows():
        month = clean_text(row.get("Month", ""))
        content = clean_text(row.get("Content", ""))

        if not month or not content:
            continue

        text = content[:3000]

        for code, class_name in class_map.items():
            pattern = rf"\b{code}\s*=\s*([0-9,]+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)

            if match:
                records.append({
                    "Month": month,
                    "Class": class_name,
                    "Responses": int(match.group(1).replace(",", ""))
                })

    class_df = pd.DataFrame(records)

    if class_df.empty:
        return pd.DataFrame(columns=["Month", "Class", "Responses"])

    class_df = (
        class_df
        .groupby(["Month", "Class"], as_index=False)
        .agg({"Responses": "max"})
    )

    return class_df


# -----------------------------
# NATIONALITIES FROM PDF RAW TEXT
# -----------------------------
def extract_nationalities_from_raw_text(raw_df):
    if raw_df.empty or "Content" not in raw_df.columns:
        return pd.DataFrame(columns=[
            "Month",
            "Nationality Group",
            "Percent",
            "Count"
        ])

    nationality_patterns = {
        "European": [r"EUROPEAN"],
        "British": [r"BRITISH"],
        "American": [r"AMERICAN"],
        "Asian": [r"ASIAN"],
        "Thai": [r"THAI"],
        "Middle Eastern": [r"MIDDLE\s+EASTERN", r"MIDDLE\s+EAST"],
        "African": [r"AFRICAN"],
        "AUS & NZ": [
            r"AUS\s*&\s*NZ",
            r"AUSTRALIAN\s*&\s*NEW\s+ZEALANDER",
            r"AUSTRALIA\s*&\s*NEW\s+ZEALAND"
        ],
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

        for group_name, patterns in nationality_patterns.items():
            for pattern in patterns:
                regex = (
                    rf"{pattern}"
                    rf"\s*(?:=|:)?\s*"
                    rf"([0-9]{{1,3}}(?:\.[0-9]+)?)"
                    rf"\s*%?"
                    rf"\s*\(?\s*([0-9][0-9,]*)\s*\)?"
                )

                match = re.search(
                    regex,
                    upper,
                    flags=re.IGNORECASE
                )

                if match:
                    percent_value = float(match.group(1))
                    count_value = int(match.group(2).replace(",", ""))

                    records.append({
                        "Month": month,
                        "Nationality Group": group_name,
                        "Percent": percent_value,
                        "Count": count_value
                    })

                    break

    nationality_df = pd.DataFrame(records)

    if nationality_df.empty:
        return pd.DataFrame(columns=[
            "Month",
            "Nationality Group",
            "Percent",
            "Count"
        ])

    nationality_df = (
        nationality_df
        .sort_values(["Month", "Nationality Group", "Count"])
        .drop_duplicates(
            subset=["Month", "Nationality Group"],
            keep="last"
        )
    )

    nationality_df["Percent"] = pd.to_numeric(
        nationality_df["Percent"],
        errors="coerce"
    )

    nationality_df["Count"] = pd.to_numeric(
        nationality_df["Count"],
        errors="coerce"
    )

    return nationality_df


# -----------------------------
# TOP COMPLAINTS FROM PDF TEXT
# -----------------------------
COMPLAINT_MONTH_WORDS = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
    "SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)


def normalize_topic_from_text(text):
    compact = normalize_key(text)

    if "ARRIVAL" in compact or "BAGGAGE" in compact:
        return "Arrival & Baggage"

    if "BOARDING" in compact:
        return "Boarding"

    if "LOUNGE" in compact:
        return "Lounge"

    if "IRREGULARITY" in compact:
        return "Irregularity"

    if "WEBSITE" in compact:
        return "Website"

    if "MOBILE" in compact:
        return "Mobile App"

    if "CALL" in compact or "CONTACT" in compact:
        return "Call Center"

    if "TICKETING" in compact:
        return "Ticketing"

    if "CHECK" in compact:
        return "Check-in"

    if "CABINCREW" in compact:
        return "Cabin Crew"

    if "CABINCLEAN" in compact:
        return "Cabin Cleanliness"

    if "LAVATORY" in compact:
        return "Lavatory Dirty"

    if "SEAT" in compact:
        return "Seat"

    if "IFE" in compact or "ENTERTAINMENT" in compact:
        return "In-flight Entertainment"

    if "MEAL" in compact:
        return "In-flight Meal"

    if "BEVERAGE" in compact:
        return "In-flight Beverage"

    if "ROP" in compact or "ROYALORCHID" in compact:
        return "ROP"

    return None


def detect_complaint_page_topic(content):
    text = clean_text(content)
    upper = text.upper()

    if "COMPLAINT" not in upper:
        return None

    title_area = upper[:1500]

    patterns = [
        rf"OVERALL\s+SATISFACTION\s+FOR\s+(.+?)\s+OF\s+({COMPLAINT_MONTH_WORDS})\s+\d{{4}}",
        rf"SATISFACTION\s+FOR\s+(.+?)\s+OF\s+({COMPLAINT_MONTH_WORDS})\s+\d{{4}}",
        rf"SATISFACTION\s+BY\s+STATION\s+FOR\s+(.+?)\s+OF\s+({COMPLAINT_MONTH_WORDS})\s+\d{{4}}",
    ]

    for pattern in patterns:
        match = re.search(pattern, title_area, flags=re.IGNORECASE)

        if match:
            topic = normalize_topic_from_text(match.group(1))

            if topic:
                return topic

    return None


def clean_complaint_item(item):
    item = clean_text(item)

    item = re.split(
        r"\s+(?:ARRIVAL\s*&?\s*BAGGAGE|BOARDING|LOUNGE|IRREGULARITY|WEBSITE|MOBILE\s+APP|TICKETING|CHECK-IN|CABIN\s+CREW|CABIN\s+CLEANLINESS|SEAT|ROP)\s*(?:\(|VERY\s+SATISFIED|SATISFACTION|OVERALL)",
        item,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    item = re.split(
        r"\s+(?:VERY\s+SATISFIED|SATISFIED\s*\(|ACCEPTABLE\s*\(|DISSATISFIED\s*\(|VERY\s+DISSATISFIED|\#RSP|\*RSP|SCALE\s+4-5)",
        item,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    item = item.strip(" -•●")

    if len(item) > 220:
        item = item[:220] + "..."

    return item


def extract_complaints_from_exact_topic_page(content):
    text = clean_text(content)

    if "complaint" not in text.lower():
        return []

    match = re.search(
        r"TOP\s*3\s*COMPLAINTS?(?:\s*\([^)]*\))?",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return []

    section = text[match.end():]

    section = re.split(
        r"\s+(?:SATISFACTION\s+FOR|SATISFACTION\s+BY\s+STATION\s+FOR|SCALE\s+4-5|\*RSP)",
        section,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    complaints = []

    bullet_items = re.findall(
        r"[•●]\s*(.*?)(?=\s*[•●]\s*|\s*$)",
        section,
        flags=re.IGNORECASE
    )

    if not bullet_items:
        bullet_items = re.findall(
            r"([A-Za-z][A-Za-z0-9\s/&,'\"().+-]{5,}?\([0-9]+(?:\.[0-9]+)?%\))",
            section,
            flags=re.IGNORECASE
        )

    for item in bullet_items:
        cleaned = clean_complaint_item(item)

        if cleaned and cleaned not in complaints:
            complaints.append(cleaned)

    return complaints[:3]


def get_top_complaints(raw_df, selected_months, selected_topics):
    if raw_df.empty:
        return pd.DataFrame()

    records = []

    target_df = raw_df[
        raw_df["Month"].isin(selected_months)
    ].copy()

    for _, row in target_df.iterrows():
        content = clean_text(row["Content"])
        page_topic = detect_complaint_page_topic(content)

        if not page_topic:
            continue

        if page_topic not in selected_topics:
            continue

        complaints = extract_complaints_from_exact_topic_page(content)

        for complaint in complaints:
            records.append({
                "Month": row["Month"],
                "Topic": page_topic,
                "Top Complaint": complaint
            })

    complaint_df = pd.DataFrame(records)

    if complaint_df.empty:
        return complaint_df

    complaint_df = complaint_df.drop_duplicates(
        subset=["Month", "Topic", "Top Complaint"]
    )

    return complaint_df


# -----------------------------
# SUMMARY COMPLAINT EXCEL
# -----------------------------
def normalize_summary_complaint_topic(value):
    compact = normalize_key(value)

    if "ARRIVAL" in compact or "BAGGAGE" in compact:
        return "Arrival & Baggage"

    if "CHECKIN" in compact or "CHECK" in compact:
        return "Check-in"

    if "LOUNGE" in compact:
        return "Lounge"

    if "CABINCLEAN" in compact or "CABINDIRTY" in compact:
        return "Cabin Cleanliness"

    if "LAVATORY" in compact:
        return "Lavatory Dirty"

    if "INFLIGHTBEVERAGE" in compact or "BEVERAGE" in compact:
        return "In-flight Beverage"

    if "INFLIGHTMEAL" in compact or "MEAL" in compact:
        return "In-flight Meal"

    if "BOARDING" in compact:
        return "Boarding"

    if "IRREGULARITY" in compact:
        return "Irregularity"

    if "SEAT" in compact:
        return "Seat"

    if "CABINCREW" in compact:
        return "Cabin Crew"

    if "WEBSITE" in compact:
        return "Website"

    if "MOBILE" in compact:
        return "Mobile App"

    if "TICKETING" in compact:
        return "Ticketing"

    if "ROP" in compact or "ROYALORCHID" in compact:
        return "ROP"

    return clean_text(value)


@st.cache_data
def load_summary_complaint():
    app_dir = Path(__file__).resolve().parent
    cwd_dir = Path.cwd()

    possible_files = [
        app_dir / "Summary Complaint.xlsx",
        app_dir / "Summary_Complaint.xlsx",
        app_dir / "summary_complaint.xlsx",
        cwd_dir / "Summary Complaint.xlsx",
        cwd_dir / "Summary_Complaint.xlsx",
        cwd_dir / "summary_complaint.xlsx",
    ]

    found_files = [
        file for file in possible_files
        if file.exists() and file.is_file() and not file.name.startswith("~$")
    ]

    if not found_files:
        st.warning(
            "ไม่พบไฟล์ Summary Complaint.xlsx | "
            f"app.py folder: {app_dir} | current folder: {cwd_dir}"
        )
        return pd.DataFrame()

    file_path = found_files[0]

    try:
        complaint_df = pd.read_excel(file_path, sheet_name="Summary")
        complaint_df.columns = complaint_df.columns.astype(str).str.strip()

        topic_col = None
        complaint_col = None

        for col in complaint_df.columns:
            col_lower = str(col).strip().lower()

            if col_lower in ["tcss topic", "topic", "touchpoint"]:
                topic_col = col

            if col_lower in ["complaint topic", "complaint", "complaints"]:
                complaint_col = col

        if topic_col is None or complaint_col is None:
            st.warning(
                f"พบไฟล์ {file_path.name} และ sheet Summary แล้ว "
                "แต่ไม่พบคอลัมน์ TCSS Topic หรือ Complaint Topic"
            )
            return pd.DataFrame()

        month_cols = []
        month_map = {}

        for col in complaint_df.columns:
            parsed_month = parse_month_column(col)

            if pd.notna(parsed_month):
                month_cols.append(col)
                month_map[col] = parsed_month

        if not month_cols:
            st.warning(
                f"พบไฟล์ {file_path.name} และ sheet Summary แล้ว "
                "แต่ไม่พบคอลัมน์เดือน เช่น Jan-25 หรือคอลัมน์วันที่ของเดือน"
            )
            return pd.DataFrame()

        long_df = complaint_df.melt(
            id_vars=[topic_col, complaint_col],
            value_vars=month_cols,
            var_name="MonthColumn",
            value_name="Complaint Count"
        )

        long_df = long_df.rename(columns={
            topic_col: "Original Topic",
            complaint_col: "Complaint Topic"
        })

        long_df["Topic"] = long_df["Original Topic"].apply(
            normalize_summary_complaint_topic
        )

        long_df["Complaint Topic"] = long_df["Complaint Topic"].apply(clean_text)

        long_df["Complaint Count"] = pd.to_numeric(
            long_df["Complaint Count"],
            errors="coerce"
        ).fillna(0)

        long_df["MonthDate"] = long_df["MonthColumn"].map(month_map)
        long_df = long_df[long_df["MonthDate"].notna()].copy()

        long_df["Month"] = pd.to_datetime(long_df["MonthDate"]).dt.strftime("%Y-%m")
        long_df["Year"] = pd.to_datetime(long_df["MonthDate"]).dt.year.astype(int)
        long_df["MonthNum"] = pd.to_datetime(long_df["MonthDate"]).dt.month.astype(int)
        long_df["MonthName"] = long_df["MonthNum"].map(MONTH_NAME)

        long_df = long_df[
            (long_df["Topic"].notna()) &
            (long_df["Complaint Topic"] != "") &
            (long_df["Complaint Count"] > 0)
        ].copy()

        long_df = (
            long_df
            .groupby(
                [
                    "Month",
                    "MonthDate",
                    "Year",
                    "MonthNum",
                    "MonthName",
                    "Topic",
                    "Complaint Topic"
                ],
                as_index=False
            )
            .agg({"Complaint Count": "sum"})
        )

        long_df = long_df[long_df["Topic"].isin(ALLOWED_COMPLAINT_TOPICS)].copy()

        # Separate positive feedback from complaint counts.
        # Rows whose Complaint Topic is exactly/essentially "Commendation" are counted as commendations.
        long_df["Is Commendation"] = (
            long_df["Complaint Topic"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .eq("commendation")
        )

        long_df["Source File"] = file_path.name
        long_df["Source Sheet"] = "Summary"

        return long_df.sort_values(
            ["MonthDate", "Topic", "Complaint Count"],
            ascending=[True, True, False]
        )

    except Exception as e:
        st.warning(f"อ่านไฟล์ Summary Complaint.xlsx sheet Summary ไม่สำเร็จ: {e}")
        return pd.DataFrame()


# -----------------------------
# LOAD ALL
# -----------------------------
df = load_data()
raw_df = load_raw_text()
extra_data = load_extra_data()
coord_df = load_station_coordinates()
complaint_summary_df = load_summary_complaint()

monthly_response_df = extract_monthly_response_counts(raw_df)
class_response_df = extract_class_responses_from_raw_text(raw_df)


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.markdown("## ✈️ TCSS Dashboard")

topic_list = sorted(df["Topic"].dropna().unique())
segment_list = sorted(df["Segment"].dropna().unique())

month_df = (
    df[["Month", "MonthDate"]]
    .dropna()
    .drop_duplicates()
    .sort_values("MonthDate")
)

available_months = month_df["Month"].tolist()
default_months = [available_months[-1]] if available_months else []

selected_months = st.sidebar.multiselect(
    "Select Month",
    options=available_months,
    default=default_months
)

if not selected_months:
    st.warning("Please select at least one month.")
    st.stop()

selected_topic = st.sidebar.selectbox(
    "Select Touchpoint",
    options=["All Touchpoints"] + topic_list
)

segment_options = ["All Segments"] + segment_list

default_segment_index = (
    segment_options.index("Overall")
    if "Overall" in segment_options
    else 0
)

selected_segment = st.sidebar.selectbox(
    "Select Segment",
    options=segment_options,
    index=default_segment_index
)

selected_topics = (
    topic_list
    if selected_topic == "All Touchpoints"
    else [selected_topic]
)

selected_segments = (
    segment_list
    if selected_segment == "All Segments"
    else [selected_segment]
)


# -----------------------------
# FILTER DATA
# -----------------------------
filtered_df = df.copy()

filtered_df = filtered_df[
    (filtered_df["Month"].isin(selected_months)) &
    (filtered_df["Topic"].isin(selected_topics)) &
    (filtered_df["Segment"].isin(selected_segments))
]

class_df = df.copy()

class_df = class_df[
    (class_df["Month"].isin(selected_months)) &
    (class_df["Segment"].isin(["First", "Business", "Economy Plus", "Economy"]))
]

if filtered_df.empty:
    st.warning("No data available from selected filters.")
    st.stop()


# -----------------------------
# HEADER
# -----------------------------
st.title("✈️ THAI Customer Satisfaction Survey")
st.caption("TCSS Dashboard from converted PDF data")


# -----------------------------
# KPI ROW
# -----------------------------
avg_csat = round(filtered_df["CSAT"].mean(), 2)
avg_rating = round(filtered_df["Average Rating"].mean(), 2)

response_filter = monthly_response_df[
    monthly_response_df["Month"].isin(selected_months)
].copy()

if not response_filter.empty:
    total_rsp = int(response_filter["Responses"].sum())
else:
    total_rsp = (
        filtered_df
        .groupby("Month")["RSP"]
        .max()
        .sum()
    )
    total_rsp = int(total_rsp) if pd.notna(total_rsp) else 0

lowest_topic = (
    filtered_df
    .groupby("Topic", as_index=False)["Average Rating"]
    .mean()
    .sort_values("Average Rating")
    .iloc[0]
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Average CSAT", f"{avg_csat:.2f}%")

with col2:
    st.metric("Average Rating", f"{avg_rating:.2f}")

with col3:
    st.metric("Total RSP", f"{total_rsp:,}")

with col4:
    st.metric("Lowest Touchpoint", lowest_topic["Topic"])


# -----------------------------
# PASSENGER PROFILE
# -----------------------------
section_header("Passenger Profile")

profile_month_label = get_selected_month_label(selected_months)

profile_col1, profile_col2, profile_col3 = st.columns(3, gap="large")

with profile_col1:
    gender_df = extra_data.get("gender", pd.DataFrame())
    gender_plot = aggregate_profile_for_selected_months(
        gender_df,
        selected_months,
        "Gender"
    )

    plot_profile_donut(
        gender_plot,
        "Gender",
        f"Gender - {profile_month_label}",
        [FLAMBOYANT_PINK, DASHING_YELLOW, JAGGER, "#7A4E9D"]
    )

with profile_col2:
    age_df = extra_data.get("age_group", pd.DataFrame())
    age_plot = aggregate_profile_for_selected_months(
        age_df,
        selected_months,
        "Age Group"
    )

    plot_profile_donut(
        age_plot,
        "Age Group",
        f"Age Group - {profile_month_label}",
        [JAGGER, "#7A4E9D", FLAMBOYANT_PINK, DASHING_YELLOW, "#39D353", "#00A3E0"]
    )

with profile_col3:
    purpose_df = extra_data.get("purpose", pd.DataFrame())
    purpose_plot = aggregate_profile_for_selected_months(
        purpose_df,
        selected_months,
        "Purpose"
    )

    plot_profile_donut(
        purpose_plot,
        "Purpose",
        f"Purpose of Journey - {profile_month_label}",
        ["#31572C", "#ED7D31", "#2F5597", "#A5A5A5", FLAMBOYANT_PINK]
    )


# -----------------------------
# CLASS RESPONSES FROM SUMMARY PAGE
# Cards only: no bar chart
# -----------------------------
if not class_response_df.empty:
    class_profile = class_response_df[
        class_response_df["Month"].isin(selected_months)
    ].copy()

    if not class_profile.empty:
        section_header("Passenger Class Responses")

        class_profile = (
            class_profile
            .groupby("Class", as_index=False)
            .agg({"Responses": "sum"})
        )

        class_order = [
            "First Class",
            "Business Class",
            "Economy Plus",
            "Economy Class"
        ]

        class_profile["Class"] = pd.Categorical(
            class_profile["Class"],
            categories=class_order,
            ordered=True
        )

        class_profile = class_profile.sort_values("Class")
        class_values = dict(zip(class_profile["Class"].astype(str), class_profile["Responses"]))

        class_cols = st.columns(4, gap="large")
        for idx, class_name in enumerate(class_order):
            with class_cols[idx]:
                render_class_card(
                    class_name,
                    f"{int(class_values.get(class_name, 0)):,.0f}"
                )


# -----------------------------
# NATIONALITIES MAP
# -----------------------------
nationality_df = extract_nationalities_from_raw_text(raw_df)

if nationality_df.empty:
    nationality_df = extra_data.get("nationalities", pd.DataFrame())

if not nationality_df.empty:
    nationality_plot = nationality_df[
        nationality_df["Month"].isin(selected_months)
    ].copy()

    if not nationality_plot.empty:
        section_header("Nationalities Map")

        nationality_plot["Nationality Group"] = (
            nationality_plot["Nationality Group"]
            .astype(str)
            .apply(normalize_nationality_group)
        )

        nationality_plot["Count"] = pd.to_numeric(
            nationality_plot.get("Count", 0),
            errors="coerce"
        ).fillna(0)

        nationality_plot["Percent"] = pd.to_numeric(
            nationality_plot.get("Percent", 0),
            errors="coerce"
        ).fillna(0)

        nationality_plot = (
            nationality_plot
            .groupby("Nationality Group", as_index=False)
            .agg({"Count": "sum"})
        )

        total_nationality_count = nationality_plot["Count"].sum()

        if total_nationality_count > 0:
            nationality_plot["Percent"] = (
                nationality_plot["Count"] / total_nationality_count * 100
            )
        else:
            nationality_plot["Percent"] = 0

        nationality_plot["Percent"] = nationality_plot["Percent"].round(2)

        nationality_coord_df = pd.DataFrame(NATIONALITY_COORDINATES)

        nationality_map_df = nationality_plot.merge(
            nationality_coord_df,
            on="Nationality Group",
            how="left"
        )

        nationality_map_df = nationality_map_df.dropna(
            subset=["Latitude", "Longitude"]
        )

        nat_col1, nat_col2 = st.columns([1.55, 1])

        with nat_col1:
            if not nationality_map_df.empty:
                fig_nationality_map = px.scatter_geo(
                    nationality_map_df,
                    lat="Latitude",
                    lon="Longitude",
                    hover_name="Nationality Group",
                    hover_data={
                        "Latitude": False,
                        "Longitude": False,
                        "Percent": ":.2f",
                        "Count": ":,"
                    },
                    size="Count",
                    size_max=60,
                    color="Percent",
                    color_continuous_scale=[
                        [0.00, JAGGER],
                        [0.35, FLAMBOYANT_PINK],
                        [0.65, DASHING_YELLOW],
                        [1.00, "#39d353"]
                    ],
                    projection="natural earth",
                    title=(
                        f"Nationalities World Map - "
                        f"{get_selected_month_label(selected_months)}"
                    )
                )

                fig_nationality_map.update_traces(
                    marker=dict(
                        line=dict(width=1, color="white"),
                        opacity=0.90
                    )
                )

                fig_nationality_map.update_layout(
                    paper_bgcolor=DARK_BG,
                    plot_bgcolor=DARK_BG,
                    font_color=TEXT_MAIN,
                    geo=dict(
                        bgcolor=DARK_BG,
                        showland=True,
                        landcolor="#F3F4F6",
                        showcountries=True,
                        countrycolor="#9CA3AF",
                        showocean=True,
                        oceancolor="#EAF2FF",
                        lakecolor="#EAF2FF",
                        coastlinecolor="#9CA3AF",
                        projection_scale=1.05
                    ),
                    margin=dict(l=10, r=10, t=60, b=10),
                    coloraxis_colorbar=dict(title="Share (%)"),
                    height=620
                )

                apply_premium_plot_layout(fig_nationality_map, height=620, title_size=20, show_grid=False)
                fig_nationality_map.update_layout(
                    font=dict(color=TEXT_MAIN),
                    coloraxis_colorbar=dict(title=dict(text="Share (%)", font=dict(color=TEXT_MAIN)), tickfont=dict(color=TEXT_MAIN))
                )
                st.plotly_chart(fig_nationality_map, width="stretch")

        with nat_col2:
            st.markdown("### Nationalities Summary")

            display_nat = nationality_plot.sort_values(
                "Count",
                ascending=False
            )

            render_light_table(
                display_nat,
                height=420,
                formats={"Count": "{:,.0f}", "Percent": "{:.2f}%"},
                hide_index=True
            )


# -----------------------------
# SUMMARY DATA
# -----------------------------
summary_source_df = filtered_df.copy()
summary_source_df["Topic"] = summary_source_df["Topic"].apply(normalize_summary_complaint_topic)
summary_source_df["Topic"] = summary_source_df["Topic"].replace({
    "Inflight Meal (DC double catering)": "In-flight Meal",
    "Arrival & Baggage Handling": "Arrival & Baggage",
    "Irregularity Handling": "Irregularity",
    "Lavatory Cleanliness": "Lavatory Dirty",
})
summary_source_df = summary_source_df[summary_source_df["Topic"].isin(ALLOWED_RATING_TREND_TOPICS)].copy()

summary = (
    summary_source_df
    .groupby("Topic", as_index=False)
    .agg({
        "Very dissatisfied": "mean",
        "Dissatisfied": "mean",
        "Acceptable": "mean",
        "Satisfied": "mean",
        "Very satisfied": "mean",
        "Average Rating": "mean",
        "CSAT": "mean",
        "RSP": "max"
    })
)

summary["TopicOrder"] = summary["Topic"].map({t: i for i, t in enumerate(ALLOWED_RATING_TREND_TOPICS)})
summary = summary.sort_values("TopicOrder").drop(columns=["TopicOrder"], errors="ignore")

for col in [
    "Very dissatisfied",
    "Dissatisfied",
    "Acceptable",
    "Satisfied",
    "Very satisfied",
    "Average Rating",
    "CSAT"
]:
    summary[col] = summary[col].round(2)


# -----------------------------
# TOP CHARTS
# -----------------------------
chart_col1, chart_col2, chart_col3 = st.columns([1.2, 1.2, 1.2])

with chart_col1:
    section_header("Class")

    if not class_df.empty:
        class_summary = (
            class_df
            .groupby(["Month", "Segment"], as_index=False)
            .agg({"RSP": "max"})
        )

        class_summary = (
            class_summary
            .groupby("Segment", as_index=False)
            .agg({"RSP": "sum"})
        )

        fig_class = px.pie(
            class_summary,
            names="Segment",
            values="RSP",
            hole=0.55,
            title="Class Distribution",
            color_discrete_sequence=[
                FLAMBOYANT_PINK,
                DASHING_YELLOW,
                JAGGER,
                "#7A4E9D"
            ]
        )

        fig_class.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=DARK_BG,
            font_color=TEXT_MAIN,
            legend=dict(orientation="h", y=-0.2)
        )

        apply_premium_plot_layout(fig_class, height=460, title_size=20, show_grid=False)
        st.plotly_chart(fig_class, width="stretch")

with chart_col2:
    section_header("Best Touchpoints")

    best_df = (
        summary
        .sort_values("Average Rating", ascending=False)
        .head(5)
    )

    fig_best = px.bar(
        best_df,
        x="Average Rating",
        y="Topic",
        orientation="h",
        text="Average Rating",
        hover_data=["CSAT", "RSP"],
        title="Top 5 Average Rating"
    )

    fig_best.update_traces(
        marker_color=GREEN_GOOD,
        textfont_color=TEXT_MAIN,
        texttemplate="%{text:.2f}"
    )

    fig_best.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color=TEXT_MAIN,
        xaxis_title="Average Rating",
        yaxis_title="",
        yaxis=dict(categoryorder="total ascending")
    )

    apply_premium_plot_layout(fig_best, height=460, title_size=20)
    st.plotly_chart(fig_best, width="stretch")

with chart_col3:
    section_header("Low Touchpoints")

    low_df = (
        summary
        .sort_values("Average Rating", ascending=True)
        .head(5)
    )

    fig_low = px.bar(
        low_df,
        x="Average Rating",
        y="Topic",
        orientation="h",
        text="Average Rating",
        hover_data=["CSAT", "RSP"],
        title="Bottom 5 Average Rating"
    )

    fig_low.update_traces(
        marker_color=ORANGE_LOW,
        textfont_color=TEXT_MAIN,
        texttemplate="%{text:.2f}"
    )

    fig_low.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color=TEXT_MAIN,
        xaxis_title="Average Rating",
        yaxis_title="",
        yaxis=dict(categoryorder="total descending")
    )

    apply_premium_plot_layout(fig_low, height=460, title_size=20)
    st.plotly_chart(fig_low, width="stretch")


# -----------------------------
# STACKED BAR
# -----------------------------
section_header("Touchpoint Satisfaction Rating")

rating_order = [
    "Very dissatisfied",
    "Dissatisfied",
    "Acceptable",
    "Satisfied",
    "Very satisfied"
]

rating_colors = {
    "Very dissatisfied": "#c00000",
    "Dissatisfied": "#ed7d31",
    "Acceptable": "#bfbf00",
    "Satisfied": "#39d353",
    "Very satisfied": "#008000"
}

fig_stack = go.Figure()

for rating in rating_order:
    fig_stack.add_trace(
        go.Bar(
            x=summary["Topic"],
            y=summary[rating],
            name=rating,
            marker_color=rating_colors[rating],
            customdata=summary[["Average Rating", "CSAT", "RSP"]],
            hovertemplate=
                "<b>%{x}</b><br>" +
                rating + ": %{y:.2f}%<br>" +
                "Average Rating: %{customdata[0]:.2f}<br>" +
                "CSAT: %{customdata[1]:.2f}%<br>" +
                "RSP: %{customdata[2]:,.0f}<extra></extra>"
        )
    )

fig_stack.add_trace(
    go.Scatter(
        x=summary["Topic"],
        y=[106] * len(summary),
        mode="text",
        text=summary["Average Rating"].round(2),
        textfont=dict(
            color=TEXT_MAIN,
            size=16
        ),
        showlegend=False,
        hoverinfo="skip"
    )
)

fig_stack.update_layout(
    barmode="stack",
    height=560,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PLOT_BG,
    font_color=TEXT_MAIN,
    title="5-Scale Satisfaction by Touchpoint",
    xaxis_title="",
    yaxis_title="Percentage",
    yaxis=dict(range=[0, 112]),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="center",
        x=0.5
    ),
    margin=dict(l=40, r=40, t=90, b=120)
)

fig_stack.update_xaxes(
    tickangle=-35,
    categoryorder="array",
    categoryarray=ALLOWED_RATING_TREND_TOPICS,
    tickmode="array",
    tickvals=ALLOWED_RATING_TREND_TOPICS,
    ticktext=[TOPIC_TICK_LABELS.get(t, t) for t in ALLOWED_RATING_TREND_TOPICS],
    tickfont=dict(color=TEXT_MAIN, size=13),
    title_font=dict(color=TEXT_MAIN),
    color=TEXT_MAIN
)
fig_stack.update_yaxes(
    tickfont=dict(color=TEXT_MAIN, size=13),
    title_font=dict(color=TEXT_MAIN),
    color=TEXT_MAIN,
    gridcolor="#E5E7EB"
)
fig_stack.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="center",
        x=0.5,
        font=dict(color=TEXT_MAIN, size=13),
        title_font=dict(color=TEXT_MAIN)
    ),
    font=dict(color=TEXT_MAIN)
)
apply_premium_plot_layout(fig_stack, height=560, title_size=22)
st.plotly_chart(fig_stack, width="stretch")


# -----------------------------
# STATION SATISFACTION MAP + STATIONS SCORE
# -----------------------------
section_header("Station Satisfaction Map")

station_df = extra_data.get("station", pd.DataFrame())

STATION_TOUCHPOINTS = [
    "Arrival & Baggage",
    "Boarding",
    "Lounge",
    "Irregularity"
]

INVALID_STATION_KEYS_APP = {
    "",
    "FILE",
    "PAGE",
    "CONTENT",
    "STATION",
    "TOTAL",
    "GRANDTOTAL",
    "MONTH",
    "TOPIC",
    "CLASS",
    "CABIN",
    "SEGMENT",
    "OVERALL",
    "ERALL",
    "BUSINESS",
    "ECONOMY",
    "ECONOMYPLUS",
    "FIRST",
    "F",
    "C",
    "PY",
    "EY",
    "PAX",
    "RSP",
    "SCALE",
    "SATISFACTION",
}

if station_df.empty:
    st.info("No station data found. Please run extract_extra_tcss.py.")
else:
    station_df = station_df.copy()

    station_df["Topic"] = (
        station_df["Topic"]
        .astype(str)
        .apply(normalize_station_touchpoint)
    )

    station_df["Station"] = (
        station_df["Station"]
        .astype(str)
        .str.strip()
    )

    station_df["StationKeyTemp"] = station_df["Station"].apply(normalize_station_name)

    station_df = station_df[
        ~station_df["StationKeyTemp"].isin(INVALID_STATION_KEYS_APP)
    ].copy()

    station_df = station_df.drop(columns=["StationKeyTemp"])

    station_df = station_df[
        station_df["Topic"].isin(STATION_TOUCHPOINTS)
    ].copy()

    default_station_topic_index = 0

    if selected_topic in STATION_TOUCHPOINTS:
        default_station_topic_index = STATION_TOUCHPOINTS.index(selected_topic)
    elif "Boarding" in STATION_TOUCHPOINTS:
        default_station_topic_index = STATION_TOUCHPOINTS.index("Boarding")

    selected_station_topic = st.selectbox(
        "Select Station Touchpoint",
        options=STATION_TOUCHPOINTS,
        index=default_station_topic_index
    )

    station_filter = station_df[
        (station_df["Month"].isin(selected_months)) &
        (station_df["Topic"] == selected_station_topic)
    ].copy()

    if station_filter.empty:
        st.info("No station data for selected month and touchpoint.")
    else:
        station_summary = (
            station_filter
            .groupby("Station", as_index=False)
            .agg({
                "Satisfaction 5-4": "mean",
                "Neutral 3": "mean",
                "Dissatisfaction 2-1": "mean",
                "RSP": "sum"
            })
        )

        station_summary["Station"] = station_summary["Station"].astype(str).str.strip()
        station_summary["StationKey"] = station_summary["Station"].apply(normalize_station_name)

        station_total_row = station_summary[
            station_summary["StationKey"] == "STATIONS"
        ].copy()

        station_detail_summary = station_summary[
            station_summary["StationKey"] != "STATIONS"
        ].copy()

        station_detail_summary = station_detail_summary.sort_values(
            "Satisfaction 5-4",
            ascending=False
        )

        station_map_df = station_detail_summary.merge(
            coord_df[["StationKey", "Latitude", "Longitude"]],
            on="StationKey",
            how="left"
        )

        missing_coord_df = station_map_df[
            station_map_df["Latitude"].isna() | station_map_df["Longitude"].isna()
        ].copy()

        station_map_df = station_map_df.dropna(
            subset=["Latitude", "Longitude"]
        ).copy()

        if not station_map_df.empty:
            station_map_df["RSP"] = station_map_df["RSP"].fillna(1)
            station_map_df["Bubble Size"] = station_map_df["RSP"].clip(lower=1)

        map_col1, map_col2 = st.columns([1.55, 1])

        with map_col1:
            if station_map_df.empty:
                st.warning(
                    "No station coordinates found. Please add missing station coordinates."
                )
            else:
                fig_station_map = px.scatter_geo(
                    station_map_df,
                    lat="Latitude",
                    lon="Longitude",
                    hover_name="Station",
                    hover_data={
                        "Latitude": False,
                        "Longitude": False,
                        "Satisfaction 5-4": ":.2f",
                        "Neutral 3": ":.2f",
                        "Dissatisfaction 2-1": ":.2f",
                        "RSP": ":,"
                    },
                    size="Bubble Size",
                    size_max=35,
                    color="Satisfaction 5-4",
                    range_color=[0, 100],
                    color_continuous_scale=[
                        [0.00, "#c00000"],
                        [0.35, "#ed7d31"],
                        [0.55, "#F5C300"],
                        [0.75, "#39d353"],
                        [1.00, "#008000"]
                    ],
                    projection="natural earth",
                    title=f"Station Satisfaction World Map - {selected_station_topic}"
                )

                fig_station_map.update_traces(
                    marker=dict(
                        line=dict(width=0.8, color="white"),
                        opacity=0.88
                    )
                )

                fig_station_map.update_layout(
                    paper_bgcolor=DARK_BG,
                    plot_bgcolor=DARK_BG,
                    font_color=TEXT_MAIN,
                    geo=dict(
                        bgcolor=DARK_BG,
                        showland=True,
                        landcolor="#F3F4F6",
                        showcountries=True,
                        countrycolor="#9CA3AF",
                        showocean=True,
                        oceancolor="#EAF2FF",
                        lakecolor="#EAF2FF",
                        coastlinecolor="#9CA3AF",
                        projection_scale=1.05
                    ),
                    margin=dict(l=10, r=10, t=60, b=10),
                    coloraxis_colorbar=dict(
                        title=dict(text="Sat 5-4 (%)", font=dict(color=TEXT_MAIN)),
                        tickfont=dict(color=TEXT_MAIN)
                    ),
                    height=680
                )

                apply_premium_plot_layout(fig_station_map, height=680, title_size=20, show_grid=False)
                fig_station_map.update_layout(
                    coloraxis_colorbar=dict(title=dict(text="Sat 5-4 (%)", font=dict(color=TEXT_MAIN)), tickfont=dict(color=TEXT_MAIN))
                )
                st.plotly_chart(fig_station_map, width="stretch")

        with map_col2:
            st.markdown("### Station Summary")

            if not station_total_row.empty:
                total_row = station_total_row.iloc[0]

                score_col1, score_col2, score_col3, score_col4 = st.columns(4, gap="small")

                with score_col1:
                    render_premium_card("Stations 5-4", f"{total_row['Satisfaction 5-4']:.2f}%", small=True)

                with score_col2:
                    render_premium_card("Stations 3", f"{total_row['Neutral 3']:.2f}%", small=True)

                with score_col3:
                    render_premium_card("Stations 2-1", f"{total_row['Dissatisfaction 2-1']:.2f}%", small=True)

                with score_col4:
                    render_premium_card("Stations RSP", f"{int(total_row['RSP']):,}", small=True)
            else:
                st.info("No Stations summary row found from Appendix.")

            display_station_summary = station_detail_summary.drop(columns=["StationKey"])

            render_light_table(
                display_station_summary,
                height=440,
                formats={
                    "Satisfaction 5-4": "{:.2f}%",
                    "Neutral 3": "{:.2f}%",
                    "Dissatisfaction 2-1": "{:.2f}%",
                    "RSP": "{:,.0f}"
                },
                hide_index=True
            )

            if not missing_coord_df.empty:
                st.markdown("### Missing Coordinates")
                st.caption(
                    "ยังมีบาง Station ที่ไม่พบพิกัด กรุณาเพิ่มชื่อด้านล่างเข้า STATION_COORDINATES"
                )

                missing_display = (
                    missing_coord_df[["Station"]]
                    .drop_duplicates()
                    .sort_values("Station")
                )
                render_light_table(
                    missing_display,
                    height=220,
                    hide_index=True
                )
            else:
                pass


# -----------------------------
# YEAR-OVER-YEAR TREND BY TOUCHPOINT
# -----------------------------
section_header("Average Rating Trend: Year over Year by Touchpoint")

trend_df = df.copy()

if "Overall" in trend_df["Segment"].unique():
    trend_df = trend_df[trend_df["Segment"] == "Overall"]

trend_summary = (
    trend_df
    .groupby(["Year", "MonthNum", "MonthName", "Topic"], as_index=False)
    .agg({
        "Average Rating": "mean",
        "CSAT": "mean",
        "RSP": "max"
    })
)

trend_summary["Topic"] = trend_summary["Topic"].apply(normalize_summary_complaint_topic)
trend_summary["Topic"] = trend_summary["Topic"].replace({
    "Lavatory Cleanliness": "Lavatory Dirty",
    "Inflight Meal (DC double catering)": "In-flight Meal",
    "Arrival & Baggage Handling": "Arrival & Baggage",
    "Irregularity Handling": "Irregularity",
})
trend_summary = trend_summary[trend_summary["Topic"].isin(ALLOWED_RATING_TREND_TOPICS)].copy()

trend_summary["Year"] = trend_summary["Year"].astype(int).astype(str)
trend_summary["Average Rating"] = trend_summary["Average Rating"].round(2)
trend_summary["CSAT"] = trend_summary["CSAT"].round(2)

trend_topics = [t for t in ALLOWED_RATING_TREND_TOPICS if t in trend_summary["Topic"].dropna().unique()]

for i in range(0, len(trend_topics), 2):
    col_left, col_right = st.columns(2)

    for col, topic in zip([col_left, col_right], trend_topics[i:i + 2]):
        topic_trend = trend_summary[
            trend_summary["Topic"] == topic
        ].copy()

        with col:
            fig_topic_trend = px.line(
                topic_trend,
                x="MonthName",
                y="Average Rating",
                color="Year",
                markers=True,
                category_orders={
                    "MonthName": MONTH_ORDER
                },
                hover_data={
                    "Year": True,
                    "Average Rating": True,
                    "CSAT": True,
                    "RSP": ":,"
                },
                title=f"{topic} - Average Rating YoY",
                color_discrete_sequence=[
                    DASHING_YELLOW,
                    FLAMBOYANT_PINK,
                    "#39d353",
                    "#7A4E9D",
                    "#00B0F0"
                ]
            )

            for trace in fig_topic_trend.data:
                if trace.name == "2025":
                    trace.update(
                        line=dict(
                            dash="dash",
                            width=1.5
                        ),
                        marker=dict(
                            size=5
                        )
                    )
                else:
                    trace.update(
                        line=dict(
                            dash="solid",
                            width=3
                        ),
                        marker=dict(
                            size=7
                        )
                    )

            apply_premium_plot_layout(fig_topic_trend, height=400, title_size=21)
            fig_topic_trend.update_layout(
                xaxis_title="Month",
                yaxis_title="Average Rating",
                legend_title_text="Year"
            )

            fig_topic_trend.update_xaxes(
                categoryorder="array",
                categoryarray=MONTH_ORDER
            )

            min_rating = topic_trend["Average Rating"].min()
            max_rating = topic_trend["Average Rating"].max()

            if pd.notna(min_rating) and pd.notna(max_rating):
                fig_topic_trend.update_yaxes(
                    range=[
                        max(1, min_rating - 0.2),
                        min(5, max_rating + 0.2)
                    ]
                )

            st.plotly_chart(
                fig_topic_trend,
                width="stretch"
            )


# -----------------------------
# COMPLAINT / COMMENDATION COUNT CHART FROM SUMMARY COMPLAINT
# Average 2026 vs 2025 + separated Commendation
# -----------------------------
section_header("Complaint Count by Topic")

if complaint_summary_df.empty:
    st.info(
        "ยังไม่พบไฟล์ Summary Complaint.xlsx หรืออ่านข้อมูลไม่ได้ "
        "หากต้องการแสดงกราฟจำนวน complaint ให้วางไฟล์ไว้ในโฟลเดอร์เดียวกับ app.py "
        "และใช้ sheet ชื่อ Summary"
    )

else:
    complaint_all = complaint_summary_df.copy()
    complaint_all = complaint_all[complaint_all["Topic"].isin(ALLOWED_COMPLAINT_TOPICS)].copy()

    complaint_all["MonthDate"] = pd.to_datetime(
        complaint_all["MonthDate"],
        errors="coerce"
    )

    complaint_all = complaint_all[
        complaint_all["MonthDate"].notna()
    ].copy()

    if "Is Commendation" not in complaint_all.columns:
        complaint_all["Is Commendation"] = (
            complaint_all["Complaint Topic"]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .eq("commendation")
        )

    if complaint_all.empty:
        st.info("Complaint data is empty after filtering the required TCSS topics.")

    else:
        available_years = sorted(complaint_all["Year"].dropna().astype(int).unique().tolist())
        current_year = 2026 if 2026 in available_years else max(available_years)
        previous_year = current_year - 1
        comparison_years = [y for y in [previous_year, current_year] if y in available_years]

        complaint_only = complaint_all[~complaint_all["Is Commendation"]].copy()
        commendation_only = complaint_all[complaint_all["Is Commendation"]].copy()

        def build_monthly_topic_grid(metric_df, value_col="Complaint Count"):
            monthly_topic_total = (
                metric_df
                .groupby(["Year", "MonthNum", "MonthName", "Topic"], as_index=False)
                .agg({value_col: "sum"})
            )

            monthly_topic_total = monthly_topic_total[
                monthly_topic_total["Year"].isin(comparison_years)
            ].copy()

            # Use all available months from the source year so each year average is monthly average.
            grid_records = []
            for y in comparison_years:
                months_in_year = sorted(
                    complaint_all.loc[complaint_all["Year"] == y, "MonthNum"]
                    .dropna()
                    .astype(int)
                    .unique()
                    .tolist()
                )
                for m in months_in_year:
                    for topic in ALLOWED_COMPLAINT_TOPICS:
                        grid_records.append({
                            "Year": y,
                            "MonthNum": m,
                            "MonthName": MONTH_NAME[m],
                            "Topic": topic
                        })

            grid_df = pd.DataFrame(grid_records)
            if grid_df.empty:
                return pd.DataFrame(columns=["Year", "MonthNum", "MonthName", "Topic", value_col])

            monthly_grid = grid_df.merge(
                monthly_topic_total[["Year", "MonthNum", "MonthName", "Topic", value_col]],
                on=["Year", "MonthNum", "MonthName", "Topic"],
                how="left"
            )
            monthly_grid[value_col] = monthly_grid[value_col].fillna(0)
            return monthly_grid

        def build_yearly_avg_topic(monthly_grid, output_col_name):
            if monthly_grid.empty:
                return pd.DataFrame(columns=["Topic", previous_year, current_year, "Delta", "Delta %"]), pd.DataFrame()

            yearly_avg_topic = (
                monthly_grid
                .groupby(["Year", "Topic"], as_index=False)
                .agg({"Complaint Count": "mean"})
                .rename(columns={"Complaint Count": output_col_name})
            )

            yearly_avg_pivot = yearly_avg_topic.pivot(
                index="Topic",
                columns="Year",
                values=output_col_name
            ).reset_index().fillna(0)

            if previous_year not in yearly_avg_pivot.columns:
                yearly_avg_pivot[previous_year] = 0
            if current_year not in yearly_avg_pivot.columns:
                yearly_avg_pivot[current_year] = 0

            yearly_avg_pivot["Delta"] = yearly_avg_pivot[current_year] - yearly_avg_pivot[previous_year]
            yearly_avg_pivot["Delta %"] = yearly_avg_pivot.apply(
                lambda r: None if r[previous_year] == 0 else (r["Delta"] / r[previous_year] * 100),
                axis=1
            )
            yearly_avg_pivot["TopicOrder"] = yearly_avg_pivot["Topic"].map({t: i for i, t in enumerate(ALLOWED_COMPLAINT_TOPICS)})
            yearly_avg_pivot = yearly_avg_pivot.sort_values("TopicOrder").drop(columns=["TopicOrder"], errors="ignore")

            yearly_avg_topic["TopicOrder"] = yearly_avg_topic["Topic"].map({t: i for i, t in enumerate(ALLOWED_COMPLAINT_TOPICS)})
            yearly_avg_topic = yearly_avg_topic.sort_values(["TopicOrder", "Year"]).drop(columns=["TopicOrder"], errors="ignore")
            return yearly_avg_pivot, yearly_avg_topic

        def render_three_kpi_cards(yearly_avg_pivot, metric_word, title_prefix, inverse_good=True, whole_number=False):
            if yearly_avg_pivot.empty:
                return

            def fmt_avg_value(value):
                return f"{value:,.0f}" if whole_number else f"{value:,.1f}"

            def fmt_delta_value(current_value, previous_value):
                change = current_value - previous_value
                change_text = f"{change:+,.0f}" if whole_number else f"{change:+,.1f}"

                if previous_value == 0 and current_value > 0:
                    delta_text = f"{change_text} (New)"
                elif previous_value == 0:
                    delta_text = "0 (0.0%)" if whole_number else "0.0 (0.0%)"
                else:
                    pct = change / previous_value * 100
                    delta_text = f"{change_text} ({pct:+.1f}%)"

                good = change <= 0 if inverse_good else change >= 0
                return delta_text, good

            total_avg_current = yearly_avg_pivot[current_year].sum()
            total_avg_previous = yearly_avg_pivot[previous_year].sum()
            total_delta, total_good = fmt_delta_value(total_avg_current, total_avg_previous)

            highest_topic_row = yearly_avg_pivot.sort_values(current_year, ascending=False).iloc[0]
            lowest_topic_row = yearly_avg_pivot.sort_values(current_year, ascending=True).iloc[0]

            kpi_1, kpi_2, kpi_3 = st.columns(3, gap="large")
            with kpi_1:
                render_premium_card(
                    f"Average {metric_word}s {current_year}",
                    fmt_avg_value(total_avg_current),
                    f"vs {previous_year}: {total_delta}",
                    total_good
                )
            with kpi_2:
                topic_delta, topic_good = fmt_delta_value(highest_topic_row[current_year], highest_topic_row[previous_year])
                render_premium_card(
                    f"Highest Avg {metric_word} Topic {current_year}",
                    highest_topic_row["Topic"],
                    f"{fmt_avg_value(highest_topic_row[current_year])} | vs {previous_year}: {topic_delta}",
                    topic_good
                )
            with kpi_3:
                topic_delta, topic_good = fmt_delta_value(lowest_topic_row[current_year], lowest_topic_row[previous_year])
                render_premium_card(
                    f"Lowest Avg {metric_word} Topic {current_year}",
                    lowest_topic_row["Topic"],
                    f"{fmt_avg_value(lowest_topic_row[current_year])} | vs {previous_year}: {topic_delta}",
                    topic_good
                )

        def render_avg_bar(yearly_avg_topic, value_col, title):
            avg_long = yearly_avg_topic.copy()
            if avg_long.empty:
                st.info(f"No data for {title}.")
                return

            avg_long["Year"] = avg_long["Year"].astype(str)

            fig_avg_topic = px.bar(
                avg_long,
                x="Topic",
                y=value_col,
                color="Year",
                barmode="group",
                text=value_col,
                category_orders={"Topic": ALLOWED_COMPLAINT_TOPICS},
                title=title,
                color_discrete_map={
                    str(previous_year): DASHING_YELLOW,
                    str(current_year): FLAMBOYANT_PINK
                }
            )

            fig_avg_topic.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
                textfont=dict(color=TEXT_MAIN, size=14)
            )

            apply_premium_plot_layout(fig_avg_topic, height=560, title_size=26)
            fig_avg_topic.update_xaxes(
                tickangle=-25,
                categoryorder="array",
                categoryarray=ALLOWED_COMPLAINT_TOPICS,
                tickmode="array",
                tickvals=ALLOWED_COMPLAINT_TOPICS,
                ticktext=[TOPIC_TICK_LABELS.get(t, t) for t in ALLOWED_COMPLAINT_TOPICS]
            )
            fig_avg_topic.update_layout(
                xaxis_title="TCSS Topic",
                yaxis_title=value_col,
                legend_title_text="Year"
            )
            st.plotly_chart(fig_avg_topic, width="stretch")

        monthly_complaint_grid = build_monthly_topic_grid(complaint_only)
        yearly_complaint_pivot, yearly_complaint_avg = build_yearly_avg_topic(
            monthly_complaint_grid,
            "Average Complaint Count"
        )

        monthly_commendation_grid = build_monthly_topic_grid(commendation_only)
        yearly_commendation_pivot, yearly_commendation_avg = build_yearly_avg_topic(
            monthly_commendation_grid,
            "Average Commendation Count"
        )

        st.markdown(f"### Average Complaint: {current_year} vs {previous_year}")
        render_three_kpi_cards(
            yearly_complaint_pivot,
            metric_word="Complaint",
            title_prefix="Average Complaint",
            inverse_good=True
        )
        render_avg_bar(
            yearly_complaint_avg,
            "Average Complaint Count",
            f"Average Complaint by Topic: {current_year} VS {previous_year}"
        )

        st.markdown(f"### Average Commendation: {current_year} vs {previous_year}")
        render_three_kpi_cards(
            yearly_commendation_pivot,
            metric_word="Commendation",
            title_prefix="Average Commendation",
            inverse_good=False,
            whole_number=True
        )
        render_avg_bar(
            yearly_commendation_avg,
            "Average Commendation Count",
            f"Average Commendation by Topic: {current_year} VS {previous_year}"
        )

        # ----- Complaint Topic Detail: Left line chart separates Complaint and Commendation, Right horizontal complaint-only bar -----
        st.markdown("### Complaint Topic Detail")

        selected_complaint_topic = st.selectbox(
            "Select TCSS Topic for Complaint Detail Chart",
            options=ALLOWED_COMPLAINT_TOPICS,
            index=ALLOWED_COMPLAINT_TOPICS.index("In-flight Meal") if "In-flight Meal" in ALLOWED_COMPLAINT_TOPICS else 0,
            key="complaint_detail_topic_select"
        )

        detail_left, detail_right = st.columns([1.05, 1], gap="large")

        with detail_left:
            topic_complaint_yoy = monthly_complaint_grid[
                monthly_complaint_grid["Topic"] == selected_complaint_topic
            ].copy()
            topic_complaint_yoy["Metric"] = "Complaint"

            topic_commendation_yoy = monthly_commendation_grid[
                monthly_commendation_grid["Topic"] == selected_complaint_topic
            ].copy()
            topic_commendation_yoy["Metric"] = "Commendation"

            metric_yoy = pd.concat([topic_complaint_yoy, topic_commendation_yoy], ignore_index=True)
            metric_yoy["Year"] = metric_yoy["Year"].astype(int)
            metric_yoy["MonthName"] = pd.Categorical(
                metric_yoy["MonthName"],
                categories=MONTH_ORDER,
                ordered=True
            )
            metric_yoy = metric_yoy.sort_values(["Metric", "Year", "MonthNum"])

            fig_detail_line = go.Figure()
            trace_settings = [
                ("Complaint", previous_year, DASHING_YELLOW, "dash", 2.0),
                ("Complaint", current_year, FLAMBOYANT_PINK, "solid", 3.4),
                ("Commendation", previous_year, "#84CC16", "dash", 2.0),
                ("Commendation", current_year, "#16A34A", "solid", 3.4),
            ]

            for metric_name, year_value, line_color, dash_style, line_width in trace_settings:
                trace_df = metric_yoy[
                    (metric_yoy["Metric"] == metric_name) &
                    (metric_yoy["Year"] == year_value)
                ].copy()
                if trace_df.empty:
                    continue

                fig_detail_line.add_trace(
                    go.Scatter(
                        x=trace_df["MonthName"],
                        y=trace_df["Complaint Count"],
                        mode="lines+markers",
                        name=f"{metric_name} {year_value}",
                        line=dict(color=line_color, dash=dash_style, width=line_width),
                        marker=dict(size=7),
                        hovertemplate=(
                            f"<b>{metric_name} {year_value}</b><br>"
                            "Month: %{x}<br>"
                            "Count: %{y:,.0f}<extra></extra>"
                        )
                    )
                )

            fig_detail_line.update_layout(
                title=f"{selected_complaint_topic}: Complaint vs Commendation Trend YoY",
                xaxis_title="Month",
                yaxis_title="Count",
                legend_title_text="Metric / Year"
            )
            apply_premium_plot_layout(fig_detail_line, height=540, title_size=23)
            fig_detail_line.update_xaxes(categoryorder="array", categoryarray=MONTH_ORDER)
            st.plotly_chart(fig_detail_line, width="stretch")

        with detail_right:
            selected_detail = complaint_only[
                complaint_only["Topic"] == selected_complaint_topic
            ].copy()

            selected_detail_avg = (
                selected_detail
                .groupby(["Year", "Complaint Topic"], as_index=False)
                .agg({"Complaint Count": "mean"})
            )

            selected_detail_pivot = selected_detail_avg.pivot(
                index="Complaint Topic",
                columns="Year",
                values="Complaint Count"
            ).reset_index().fillna(0)

            if previous_year not in selected_detail_pivot.columns:
                selected_detail_pivot[previous_year] = 0
            if current_year not in selected_detail_pivot.columns:
                selected_detail_pivot[current_year] = 0

            selected_detail_pivot = (
                selected_detail_pivot
                .sort_values(current_year, ascending=False)
                .head(10)
                .sort_values(current_year, ascending=True)
            )

            selected_detail_long = selected_detail_pivot.melt(
                id_vars="Complaint Topic",
                value_vars=[previous_year, current_year],
                var_name="Year",
                value_name="Average Complaint Count"
            )
            selected_detail_long["Year"] = selected_detail_long["Year"].astype(str)

            fig_detail_bar = px.bar(
                selected_detail_long,
                x="Average Complaint Count",
                y="Complaint Topic",
                color="Year",
                barmode="group",
                orientation="h",
                text="Average Complaint Count",
                title=f"{selected_complaint_topic}: Complaint Topic Average",
                color_discrete_map={
                    str(previous_year): DASHING_YELLOW,
                    str(current_year): FLAMBOYANT_PINK
                }
            )

            fig_detail_bar.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
                textfont=dict(color=TEXT_MAIN, size=13)
            )

            apply_premium_plot_layout(fig_detail_bar, height=540, title_size=23)
            fig_detail_bar.update_layout(
                xaxis_title="Average Complaint Count",
                yaxis_title="Complaint Topic",
                legend_title_text="Year"
            )
            st.plotly_chart(fig_detail_bar, width="stretch")

        with st.expander(f"Show {selected_complaint_topic} Complaint / Commendation Topic Data"):
            selected_raw = complaint_all[complaint_all["Topic"] == selected_complaint_topic].copy()
            selected_raw = selected_raw.sort_values(["Year", "MonthNum", "Is Commendation", "Complaint Count"], ascending=[False, False, True, False])
            render_light_table(selected_raw, height=360, hide_index=True)



# -----------------------------
# TOP COMPLAINTS - ORIGINAL TEXT TABLE
# -----------------------------
section_header("Top Complaints")

complaint_df = get_top_complaints(
    raw_df=raw_df,
    selected_months=selected_months,
    selected_topics=selected_topics
)

if raw_df.empty:
    st.info(
        "master_tcss.xlsx was not found. "
        "Please keep master_tcss.xlsx in the same folder as app.py."
    )
elif complaint_df.empty:
    st.info("No complaint text found for the selected filters.")
else:
    render_light_table(complaint_df, height=460, hide_index=True)


# -----------------------------
# DATA TABLE
# -----------------------------
with st.expander("Show Data Table"):
    render_light_table(filtered_df, height=520, hide_index=True)
