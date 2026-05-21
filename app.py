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

DARK_BG = "#111111"
CARD_BG = "#1f1f1f"
PLOT_BG = "#303030"

GREEN_GOOD = "#39D353"
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


# -----------------------------
# STATION COORDINATES
# -----------------------------
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
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="TCSS Dashboard",
    layout="wide"
)


# -----------------------------
# CUSTOM CSS
# -----------------------------
css = """
<style>
.stApp {
    background-color: COLOR_DARK_BG;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: COLOR_JAGGER;
}

.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

div[data-testid="stMetric"] {
    background-color: COLOR_CARD_BG;
    border-radius: 14px;
    padding: 18px;
    border: 1px solid #333333;
}

div[data-testid="stMetricLabel"] {
    color: #d9d9d9;
}

div[data-testid="stMetricValue"] {
    color: COLOR_DASHING_YELLOW;
    font-size: 30px;
}

h1, h2, h3 {
    color: white;
}

.stMultiSelect [data-baseweb="tag"] {
    background-color: COLOR_FLAMBOYANT_PINK !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    border-color: COLOR_FLAMBOYANT_PINK !important;
}
</style>
"""

css = (
    css
    .replace("COLOR_DARK_BG", DARK_BG)
    .replace("COLOR_JAGGER", JAGGER)
    .replace("COLOR_CARD_BG", CARD_BG)
    .replace("COLOR_DASHING_YELLOW", DASHING_YELLOW)
    .replace("COLOR_FLAMBOYANT_PINK", FLAMBOYANT_PINK)
)

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
        return "Lavatory Cleanliness"

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
        return "Lavatory Cleanliness"

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
st.subheader("Passenger Profile")

profile_month = get_latest_month(selected_months)

profile_col1, profile_col2, profile_col3 = st.columns(3)

with profile_col1:
    gender_df = extra_data.get("gender", pd.DataFrame())

    if not gender_df.empty:
        gender_plot = gender_df[gender_df["Month"] == profile_month].copy()

        if not gender_plot.empty:
            fig_gender = px.pie(
                gender_plot,
                names="Gender",
                values="Percent",
                hole=0.45,
                title=f"Gender - {profile_month}",
                color_discrete_sequence=[
                    FLAMBOYANT_PINK,
                    DASHING_YELLOW,
                    JAGGER,
                    "#7A4E9D"
                ]
            )

            fig_gender.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=DARK_BG,
                font_color="white",
                legend=dict(orientation="h", y=-0.2)
            )

            st.plotly_chart(fig_gender, width="stretch")

with profile_col2:
    age_df = extra_data.get("age_group", pd.DataFrame())

    if not age_df.empty:
        age_plot = age_df[age_df["Month"] == profile_month].copy()

        if not age_plot.empty:
            fig_age = px.pie(
                age_plot,
                names="Age Group",
                values="Percent",
                hole=0.45,
                title=f"Age Group - {profile_month}",
                color_discrete_sequence=[
                    JAGGER,
                    "#7A4E9D",
                    FLAMBOYANT_PINK,
                    DASHING_YELLOW,
                    "#39d353",
                    "#00B0F0"
                ]
            )

            fig_age.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=DARK_BG,
                font_color="white",
                legend=dict(orientation="h", y=-0.2)
            )

            st.plotly_chart(fig_age, width="stretch")

with profile_col3:
    purpose_df = extra_data.get("purpose", pd.DataFrame())

    if not purpose_df.empty:
        purpose_plot = purpose_df[purpose_df["Month"] == profile_month].copy()

        if not purpose_plot.empty:
            fig_purpose = px.pie(
                purpose_plot,
                names="Purpose",
                values="Percent",
                hole=0.45,
                title=f"Purpose of Journey - {profile_month}",
                color_discrete_sequence=[
                    "#2F4F20",
                    "#ed7d31",
                    "#2F5597",
                    "#A5A5A5"
                ]
            )

            fig_purpose.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=DARK_BG,
                font_color="white",
                legend=dict(orientation="h", y=-0.2)
            )

            st.plotly_chart(fig_purpose, width="stretch")


# -----------------------------
# CLASS RESPONSES FROM SUMMARY PAGE
# -----------------------------
if not class_response_df.empty:
    class_profile = class_response_df[
        class_response_df["Month"].isin(selected_months)
    ].copy()

    if not class_profile.empty:
        st.subheader("Passenger Class Responses")

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

        class_cols = st.columns(4)

        for idx, row in class_profile.reset_index(drop=True).iterrows():
            with class_cols[idx % 4]:
                st.metric(
                    row["Class"],
                    f"{int(row['Responses']):,}"
                )

        fig_class_response = px.bar(
            class_profile,
            x="Class",
            y="Responses",
            text="Responses",
            title="Passenger Class Responses",
            color="Class",
            color_discrete_sequence=[
                DASHING_YELLOW,
                FLAMBOYANT_PINK,
                JAGGER,
                "#7A4E9D"
            ]
        )

        fig_class_response.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside"
        )

        fig_class_response.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=PLOT_BG,
            font_color="white",
            xaxis_title="Class",
            yaxis_title="Responses",
            showlegend=False,
            height=420
        )

        st.plotly_chart(fig_class_response, width="stretch")


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
        st.subheader("Nationalities Map")

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
                        f"{', '.join(selected_months)}"
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
                    font_color="white",
                    geo=dict(
                        bgcolor=DARK_BG,
                        showland=True,
                        landcolor="#2b2b2b",
                        showcountries=True,
                        countrycolor="#666666",
                        showocean=True,
                        oceancolor="#111827",
                        lakecolor="#111827",
                        coastlinecolor="#666666",
                        projection_scale=1.05
                    ),
                    margin=dict(l=10, r=10, t=60, b=10),
                    coloraxis_colorbar=dict(title="Share (%)"),
                    height=620
                )

                st.plotly_chart(fig_nationality_map, width="stretch")

        with nat_col2:
            st.markdown("### Nationalities Summary")

            display_nat = nationality_plot.sort_values(
                "Count",
                ascending=False
            )

            st.dataframe(
                display_nat.style.format({
                    "Count": "{:,.0f}",
                    "Percent": "{:.2f}%"
                }),
                width="stretch",
                height=420
            )


# -----------------------------
# SUMMARY DATA
# -----------------------------
summary = (
    filtered_df
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

summary = summary.sort_values("Average Rating", ascending=False)

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
    st.subheader("Class")

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
            font_color="white",
            legend=dict(orientation="h", y=-0.2)
        )

        st.plotly_chart(fig_class, width="stretch")

with chart_col2:
    st.subheader("Best Touchpoints")

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
        textfont_color="white",
        texttemplate="%{text:.2f}"
    )

    fig_best.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color="white",
        xaxis_title="Average Rating",
        yaxis_title="",
        yaxis=dict(categoryorder="total ascending")
    )

    st.plotly_chart(fig_best, width="stretch")

with chart_col3:
    st.subheader("Low Touchpoints")

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
        textfont_color="white",
        texttemplate="%{text:.2f}"
    )

    fig_low.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color="white",
        xaxis_title="Average Rating",
        yaxis_title="",
        yaxis=dict(categoryorder="total descending")
    )

    st.plotly_chart(fig_low, width="stretch")


# -----------------------------
# STACKED BAR
# -----------------------------
st.subheader("Touchpoint Satisfaction Rating")

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
            color=DASHING_YELLOW,
            size=16
        ),
        showlegend=False,
        hoverinfo="skip"
    )
)

fig_stack.update_layout(
    barmode="stack",
    height=560,
    paper_bgcolor=DARK_BG,
    plot_bgcolor=PLOT_BG,
    font_color="white",
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

fig_stack.update_xaxes(tickangle=-45)

st.plotly_chart(fig_stack, width="stretch")


# -----------------------------
# STATION SATISFACTION MAP + STATIONS SCORE
# -----------------------------
st.subheader("Station Satisfaction Map")

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
                    font_color="white",
                    geo=dict(
                        bgcolor=DARK_BG,
                        showland=True,
                        landcolor="#2b2b2b",
                        showcountries=True,
                        countrycolor="#666666",
                        showocean=True,
                        oceancolor="#111827",
                        lakecolor="#111827",
                        coastlinecolor="#666666",
                        projection_scale=1.05
                    ),
                    margin=dict(l=10, r=10, t=60, b=10),
                    coloraxis_colorbar=dict(
                        title="Sat 5-4 (%)"
                    ),
                    height=680
                )

                st.plotly_chart(fig_station_map, width="stretch")

        with map_col2:
            st.markdown("### Station Summary")

            if not station_total_row.empty:
                total_row = station_total_row.iloc[0]

                score_col1, score_col2, score_col3, score_col4 = st.columns(4)

                with score_col1:
                    st.metric(
                        "Stations 5-4",
                        f"{total_row['Satisfaction 5-4']:.2f}%"
                    )

                with score_col2:
                    st.metric(
                        "Stations 3",
                        f"{total_row['Neutral 3']:.2f}%"
                    )

                with score_col3:
                    st.metric(
                        "Stations 2-1",
                        f"{total_row['Dissatisfaction 2-1']:.2f}%"
                    )

                with score_col4:
                    st.metric(
                        "Stations RSP",
                        f"{int(total_row['RSP']):,}"
                    )
            else:
                st.info("No Stations summary row found from Appendix.")

            display_station_summary = station_detail_summary.drop(columns=["StationKey"])

            st.dataframe(
                display_station_summary.style.format({
                    "Satisfaction 5-4": "{:.2f}%",
                    "Neutral 3": "{:.2f}%",
                    "Dissatisfaction 2-1": "{:.2f}%",
                    "RSP": "{:,.0f}"
                }),
                width="stretch",
                height=440
            )

            if not missing_coord_df.empty:
                st.markdown("### Missing Coordinates")
                st.caption(
                    "ยังมีบาง Station ที่ไม่พบพิกัด กรุณาเพิ่มชื่อด้านล่างเข้า STATION_COORDINATES"
                )

                st.dataframe(
                    missing_coord_df[["Station"]]
                    .drop_duplicates()
                    .sort_values("Station"),
                    width="stretch",
                    height=220
                )
            else:
                st.success("All station coordinates found.")


# -----------------------------
# YEAR-OVER-YEAR TREND BY TOUCHPOINT
# -----------------------------
st.subheader("Average Rating Trend: Year over Year by Touchpoint")

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

trend_summary["Year"] = trend_summary["Year"].astype(int).astype(str)
trend_summary["Average Rating"] = trend_summary["Average Rating"].round(2)
trend_summary["CSAT"] = trend_summary["CSAT"].round(2)

trend_topics = sorted(trend_summary["Topic"].dropna().unique())

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

            fig_topic_trend.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=PLOT_BG,
                font_color="white",
                xaxis_title="Month",
                yaxis_title="Average Rating",
                height=380,
                legend_title_text="Year",
                margin=dict(l=40, r=40, t=70, b=60)
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
# COMPLAINT COUNT CHART FROM SUMMARY COMPLAINT
# Latest vs Previous by TCSS Topic + Complaint Topic
# KPI Cards show every TCSS Topic together
# Detail chart uses selectbox
# YoY Trend as Line Chart
# -----------------------------
st.subheader("Complaint Count by Topic")

if complaint_summary_df.empty:
    st.info(
        "ยังไม่พบไฟล์ Summary Complaint.xlsx หรืออ่านข้อมูลไม่ได้ "
        "หากต้องการแสดงกราฟจำนวน complaint ให้วางไฟล์ไว้ในโฟลเดอร์เดียวกับ app.py "
        "และใช้ sheet ชื่อ Summary"
    )

else:
    complaint_all = complaint_summary_df.copy()

    complaint_all["MonthDate"] = pd.to_datetime(
        complaint_all["MonthDate"],
        errors="coerce"
    )

    complaint_all = complaint_all[
        complaint_all["MonthDate"].notna()
    ].copy()

    if complaint_all.empty:
        st.info("Complaint data is empty after parsing MonthDate.")

    else:
        available_month_dates = (
            complaint_all["MonthDate"]
            .dropna()
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        latest_month_date = available_month_dates[-1]

        previous_month_date = (
            available_month_dates[-2]
            if len(available_month_dates) >= 2
            else None
        )

        latest_month_text = latest_month_date.strftime("%Y-%m")

        previous_month_text = (
            previous_month_date.strftime("%Y-%m")
            if previous_month_date is not None
            else None
        )

        previous_month_label = (
            previous_month_text
            if previous_month_text is not None
            else "Previous Month"
        )

        def calculate_change_percent(row):
            previous_value = row["Previous Month"]
            current_value = row["Current Month"]

            if previous_value == 0 and current_value == 0:
                return 0

            if previous_value == 0 and current_value > 0:
                return None

            return (
                (current_value - previous_value) /
                previous_value *
                100
            )

        def format_delta(change_value, change_percent):
            change_value = int(change_value)

            if pd.isna(change_percent):
                return f"{change_value:+,} (New)"

            return f"{change_value:+,} ({change_percent:+.1f}%)"

        latest_topic_df = (
            complaint_all[
                complaint_all["MonthDate"] == latest_month_date
            ]
            .groupby("Topic", as_index=False)
            .agg({"Complaint Count": "sum"})
            .rename(columns={"Complaint Count": "Current Month"})
        )

        if previous_month_date is not None:
            previous_topic_df = (
                complaint_all[
                    complaint_all["MonthDate"] == previous_month_date
                ]
                .groupby("Topic", as_index=False)
                .agg({"Complaint Count": "sum"})
                .rename(columns={"Complaint Count": "Previous Month"})
            )
        else:
            previous_topic_df = pd.DataFrame(
                columns=["Topic", "Previous Month"]
            )

        latest_vs_previous = latest_topic_df.merge(
            previous_topic_df,
            on="Topic",
            how="outer"
        ).fillna(0)

        latest_vs_previous["Current Month"] = (
            latest_vs_previous["Current Month"]
            .astype(int)
        )

        latest_vs_previous["Previous Month"] = (
            latest_vs_previous["Previous Month"]
            .astype(int)
        )

        latest_vs_previous["Change"] = (
            latest_vs_previous["Current Month"] -
            latest_vs_previous["Previous Month"]
        )

        latest_vs_previous["Change %"] = latest_vs_previous.apply(
            calculate_change_percent,
            axis=1
        )

        latest_vs_previous = latest_vs_previous.sort_values(
            "Current Month",
            ascending=False
        )

        ordered_topics = latest_vs_previous["Topic"].tolist()

        st.markdown(
            f"### Complaint Count: {latest_month_text}"
            + (
                f" vs {previous_month_text}"
                if previous_month_text is not None
                else ""
            )
        )

        total_current = int(latest_vs_previous["Current Month"].sum())
        total_previous = int(latest_vs_previous["Previous Month"].sum())
        total_change = total_current - total_previous

        if total_previous > 0:
            total_change_pct = total_change / total_previous * 100
            total_delta_text = f"{total_change:+,} ({total_change_pct:+.1f}%)"
        elif total_current > 0:
            total_delta_text = f"{total_change:+,} (New)"
        else:
            total_delta_text = "0 (0.0%)"

        overview_kpi_1, overview_kpi_2, overview_kpi_3 = st.columns(3)

        with overview_kpi_1:
            st.metric(
                f"Total Complaints {latest_month_text}",
                f"{total_current:,}",
                total_delta_text,
                delta_color="inverse"
            )

        with overview_kpi_2:
            if not latest_vs_previous.empty:
                highest_row = latest_vs_previous.iloc[0]

                st.metric(
                    "Highest TCSS Topic",
                    highest_row["Topic"],
                    format_delta(
                        highest_row["Change"],
                        highest_row["Change %"]
                    ),
                    delta_color="inverse"
                )

        with overview_kpi_3:
            improved_df = latest_vs_previous.sort_values(
                "Change",
                ascending=True
            )

            if not improved_df.empty:
                best_improve_row = improved_df.iloc[0]

                st.metric(
                    "Most Improved TCSS Topic",
                    best_improve_row["Topic"],
                    format_delta(
                        best_improve_row["Change"],
                        best_improve_row["Change %"]
                    ),
                    delta_color="inverse"
                )

        latest_detail_df = (
            complaint_all[
                complaint_all["MonthDate"] == latest_month_date
            ]
            .groupby(["Topic", "Complaint Topic"], as_index=False)
            .agg({"Complaint Count": "sum"})
            .rename(columns={"Complaint Count": "Current Month"})
        )

        if previous_month_date is not None:
            previous_detail_df = (
                complaint_all[
                    complaint_all["MonthDate"] == previous_month_date
                ]
                .groupby(["Topic", "Complaint Topic"], as_index=False)
                .agg({"Complaint Count": "sum"})
                .rename(columns={"Complaint Count": "Previous Month"})
            )
        else:
            previous_detail_df = pd.DataFrame(
                columns=[
                    "Topic",
                    "Complaint Topic",
                    "Previous Month"
                ]
            )

        detail_compare_df = latest_detail_df.merge(
            previous_detail_df,
            on=["Topic", "Complaint Topic"],
            how="outer"
        ).fillna(0)

        detail_compare_df["Current Month"] = (
            detail_compare_df["Current Month"]
            .astype(int)
        )

        detail_compare_df["Previous Month"] = (
            detail_compare_df["Previous Month"]
            .astype(int)
        )

        detail_compare_df["Change"] = (
            detail_compare_df["Current Month"] -
            detail_compare_df["Previous Month"]
        )

        detail_compare_df["Change %"] = detail_compare_df.apply(
            calculate_change_percent,
            axis=1
        )

        st.markdown("### Complaint KPI Summary by TCSS Topic")

        for topic in ordered_topics:
            topic_detail = detail_compare_df[
                detail_compare_df["Topic"] == topic
            ].copy()

            topic_summary = latest_vs_previous[
                latest_vs_previous["Topic"] == topic
            ].copy()

            if topic_detail.empty or topic_summary.empty:
                continue

            topic_detail = topic_detail.sort_values(
                "Current Month",
                ascending=False
            )

            topic_summary_row = topic_summary.iloc[0]
            top_detail_row = topic_detail.iloc[0]

            highest_increase_row = topic_detail.sort_values(
                "Change",
                ascending=False
            ).iloc[0]

            st.markdown(f"#### {topic}")

            topic_kpi_1, topic_kpi_2, topic_kpi_3 = st.columns(3)

            with topic_kpi_1:
                st.metric(
                    f"{topic} Complaints",
                    f"{int(topic_summary_row['Current Month']):,}",
                    format_delta(
                        topic_summary_row["Change"],
                        topic_summary_row["Change %"]
                    ),
                    delta_color="inverse"
                )

            with topic_kpi_2:
                st.metric(
                    "Top Complaint Topic",
                    str(top_detail_row["Complaint Topic"])[:70],
                    format_delta(
                        top_detail_row["Change"],
                        top_detail_row["Change %"]
                    ),
                    delta_color="inverse"
                )

            with topic_kpi_3:
                st.metric(
                    "Highest Increase",
                    str(highest_increase_row["Complaint Topic"])[:70],
                    format_delta(
                        highest_increase_row["Change"],
                        highest_increase_row["Change %"]
                    ),
                    delta_color="inverse"
                )

        comparison_long = latest_vs_previous.melt(
            id_vars=["Topic", "Change", "Change %"],
            value_vars=["Previous Month", "Current Month"],
            var_name="Period",
            value_name="Complaint Count"
        )

        comparison_long["Month"] = comparison_long["Period"].replace({
            "Previous Month": previous_month_label,
            "Current Month": latest_month_text
        })

        fig_latest_compare = px.bar(
            comparison_long,
            x="Topic",
            y="Complaint Count",
            color="Period",
            barmode="group",
            text="Complaint Count",
            hover_data={
                "Topic": True,
                "Month": True,
                "Complaint Count": ":,",
                "Change": ":,",
                "Change %": ":.1f"
            },
            title=f"TCSS Topic Overview: {latest_month_text} vs {previous_month_label}",
            color_discrete_map={
                "Previous Month": DASHING_YELLOW,
                "Current Month": FLAMBOYANT_PINK
            }
        )

        fig_latest_compare.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside"
        )

        fig_latest_compare.update_layout(
            paper_bgcolor=DARK_BG,
            plot_bgcolor=PLOT_BG,
            font_color="white",
            xaxis_title="TCSS Topic",
            yaxis_title="Complaint Count",
            height=560,
            legend_title_text="Period",
            margin=dict(l=40, r=40, t=80, b=130)
        )

        fig_latest_compare.update_xaxes(tickangle=-35)

        st.plotly_chart(fig_latest_compare, width="stretch")

        st.markdown("### Complaint Topic Detail")

        selected_complaint_topic = st.selectbox(
            "Select TCSS Topic for Complaint Detail Chart",
            options=ordered_topics,
            index=0,
            key="complaint_detail_topic_select"
        )

        topic_detail = detail_compare_df[
            detail_compare_df["Topic"] == selected_complaint_topic
        ].copy()

        topic_detail = topic_detail.sort_values(
            "Current Month",
            ascending=False
        )

        if topic_detail.empty:
            st.info(f"No complaint detail found for {selected_complaint_topic}.")

        else:
            selected_topic_current_total = int(
                topic_detail["Current Month"].sum()
            )

            selected_topic_previous_total = int(
                topic_detail["Previous Month"].sum()
            )

            selected_topic_change = (
                selected_topic_current_total -
                selected_topic_previous_total
            )

            if selected_topic_previous_total > 0:
                selected_topic_change_pct = (
                    selected_topic_change /
                    selected_topic_previous_total *
                    100
                )

                selected_topic_delta_text = (
                    f"{selected_topic_change:+,} "
                    f"({selected_topic_change_pct:+.1f}%)"
                )
            elif selected_topic_current_total > 0:
                selected_topic_delta_text = (
                    f"{selected_topic_change:+,} (New)"
                )
            else:
                selected_topic_delta_text = "0 (0.0%)"

            selected_kpi_1, selected_kpi_2, selected_kpi_3 = st.columns(3)

            with selected_kpi_1:
                st.metric(
                    f"{selected_complaint_topic} Complaints",
                    f"{selected_topic_current_total:,}",
                    selected_topic_delta_text,
                    delta_color="inverse"
                )

            with selected_kpi_2:
                selected_top_detail = topic_detail.iloc[0]

                st.metric(
                    "Top Complaint Topic",
                    str(selected_top_detail["Complaint Topic"])[:70],
                    format_delta(
                        selected_top_detail["Change"],
                        selected_top_detail["Change %"]
                    ),
                    delta_color="inverse"
                )

            with selected_kpi_3:
                selected_highest_increase = topic_detail.sort_values(
                    "Change",
                    ascending=False
                ).iloc[0]

                st.metric(
                    "Highest Increase",
                    str(selected_highest_increase["Complaint Topic"])[:70],
                    format_delta(
                        selected_highest_increase["Change"],
                        selected_highest_increase["Change %"]
                    ),
                    delta_color="inverse"
                )

            top_n_detail = topic_detail.head(12).copy()

            detail_long = top_n_detail.melt(
                id_vars=[
                    "Topic",
                    "Complaint Topic",
                    "Change",
                    "Change %"
                ],
                value_vars=[
                    "Previous Month",
                    "Current Month"
                ],
                var_name="Period",
                value_name="Complaint Count"
            )

            detail_long["Month"] = detail_long["Period"].replace({
                "Previous Month": previous_month_label,
                "Current Month": latest_month_text
            })

            fig_detail_compare = px.bar(
                detail_long,
                x="Complaint Count",
                y="Complaint Topic",
                color="Period",
                barmode="group",
                orientation="h",
                text="Complaint Count",
                hover_data={
                    "Topic": True,
                    "Complaint Topic": True,
                    "Month": True,
                    "Complaint Count": ":,",
                    "Change": ":,",
                    "Change %": ":.1f"
                },
                title=(
                    f"{selected_complaint_topic}: Complaint Topic Detail "
                    f"{latest_month_text} vs {previous_month_label}"
                ),
                color_discrete_map={
                    "Previous Month": DASHING_YELLOW,
                    "Current Month": FLAMBOYANT_PINK
                }
            )

            fig_detail_compare.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside"
            )

            fig_detail_compare.update_layout(
                paper_bgcolor=DARK_BG,
                plot_bgcolor=PLOT_BG,
                font_color="white",
                xaxis_title="Complaint Count",
                yaxis_title="Complaint Topic",
                height=620,
                legend_title_text="Period",
                margin=dict(l=40, r=80, t=80, b=50),
                yaxis=dict(categoryorder="total ascending")
            )

            st.plotly_chart(
                fig_detail_compare,
                width="stretch"
            )

            display_topic_detail = topic_detail.copy()

            display_topic_detail["Change %"] = (
                display_topic_detail["Change %"]
                .apply(
                    lambda x: "New"
                    if pd.isna(x)
                    else f"{x:.1f}%"
                )
            )

            with st.expander(
                f"Show {selected_complaint_topic} Complaint Topic Data"
            ):
                st.dataframe(
                    display_topic_detail[
                        [
                            "Topic",
                            "Complaint Topic",
                            "Previous Month",
                            "Current Month",
                            "Change",
                            "Change %"
                        ]
                    ],
                    width="stretch",
                    hide_index=True
                )

        st.markdown("### Complaint Count Trend: Year over Year by Topic")

        yearly_topic_total = (
            complaint_all
            .groupby(
                [
                    "Year",
                    "MonthNum",
                    "MonthName",
                    "Topic"
                ],
                as_index=False
            )
            .agg({"Complaint Count": "sum"})
        )

        top_detail_by_period = (
            complaint_all
            .sort_values("Complaint Count", ascending=False)
            .drop_duplicates(
                subset=[
                    "Year",
                    "MonthNum",
                    "Topic"
                ],
                keep="first"
            )
            [
                [
                    "Year",
                    "MonthNum",
                    "Topic",
                    "Complaint Topic",
                    "Complaint Count"
                ]
            ]
            .rename(columns={
                "Complaint Topic": "Top Complaint Detail",
                "Complaint Count": "Top Detail Count"
            })
        )

        yearly_topic_total = yearly_topic_total.merge(
            top_detail_by_period,
            on=[
                "Year",
                "MonthNum",
                "Topic"
            ],
            how="left"
        )

        yearly_topic_total["Year"] = (
            yearly_topic_total["Year"]
            .astype(int)
            .astype(str)
        )

        yearly_topic_total["MonthName"] = pd.Categorical(
            yearly_topic_total["MonthName"],
            categories=MONTH_ORDER,
            ordered=True
        )

        yearly_topic_total = yearly_topic_total.sort_values(
            [
                "Topic",
                "Year",
                "MonthNum"
            ]
        )

        yoy_topics = sorted(
            yearly_topic_total["Topic"]
            .dropna()
            .unique()
        )

        for i in range(0, len(yoy_topics), 2):
            trend_col_1, trend_col_2 = st.columns(2)

            for chart_col, topic in zip(
                [trend_col_1, trend_col_2],
                yoy_topics[i:i + 2]
            ):
                topic_yoy = yearly_topic_total[
                    yearly_topic_total["Topic"] == topic
                ].copy()

                with chart_col:
                    fig_yoy_complaint = px.line(
                        topic_yoy,
                        x="MonthName",
                        y="Complaint Count",
                        color="Year",
                        markers=True,
                        category_orders={
                            "MonthName": MONTH_ORDER
                        },
                        hover_data={
                            "Year": True,
                            "MonthName": True,
                            "Complaint Count": ":,",
                            "Top Complaint Detail": True,
                            "Top Detail Count": ":,"
                        },
                        title=f"{topic} - Complaint Count YoY",
                        color_discrete_map={
                            "2025": DASHING_YELLOW,
                            "2026": FLAMBOYANT_PINK
                        }
                    )

                    for trace in fig_yoy_complaint.data:
                        if trace.name == "2025":
                            trace.update(
                                line=dict(
                                    dash="dash",
                                    width=1.5
                                ),
                                marker=dict(
                                    size=6
                                )
                            )
                        elif trace.name == "2026":
                            trace.update(
                                line=dict(
                                    dash="solid",
                                    width=3.2
                                ),
                                marker=dict(
                                    size=8
                                )
                            )
                        else:
                            trace.update(
                                line=dict(
                                    dash="solid",
                                    width=2.2
                                ),
                                marker=dict(
                                    size=7
                                )
                            )

                    fig_yoy_complaint.update_layout(
                        paper_bgcolor=DARK_BG,
                        plot_bgcolor=PLOT_BG,
                        font_color="white",
                        xaxis_title="Month",
                        yaxis_title="Complaint Count",
                        height=420,
                        legend_title_text="Year",
                        margin=dict(l=40, r=40, t=70, b=70)
                    )

                    fig_yoy_complaint.update_xaxes(
                        categoryorder="array",
                        categoryarray=MONTH_ORDER
                    )

                    st.plotly_chart(
                        fig_yoy_complaint,
                        width="stretch"
                    )

        with st.expander("Show Complaint YoY Data"):
            display_yoy = yearly_topic_total.copy()

            display_yoy["Complaint Count"] = (
                display_yoy["Complaint Count"]
                .astype(int)
            )

            display_yoy["Top Detail Count"] = pd.to_numeric(
                display_yoy["Top Detail Count"],
                errors="coerce"
            ).fillna(0).astype(int)

            st.dataframe(
                display_yoy,
                width="stretch",
                hide_index=True
            )


# -----------------------------
# TOP COMPLAINTS - ORIGINAL TEXT TABLE
# -----------------------------
st.subheader("Top Complaints")

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
    st.dataframe(
        complaint_df,
        width="stretch",
        hide_index=True
    )


# -----------------------------
# DATA TABLE
# -----------------------------
with st.expander("Show Data Table"):
    st.dataframe(filtered_df, width="stretch")