import pandas as pd
import re

# -----------------------------
# READ STRUCTURED EXCEL
# -----------------------------
input_file = "structured_tcss.xlsx"
output_file = "clean_tcss_rating.xlsx"

df = pd.read_excel(input_file, dtype=str)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def extract_month_from_file(filename):
    """
    Example:
    TCSS_202501.pdf -> 2025-01
    TCSS_202512.pdf -> 2025-12
    """
    match = re.search(r"(\d{6})", str(filename))
    if match:
        ym = match.group(1)
        return f"{ym[:4]}-{ym[4:]}"
    return ""


def parse_percent(value):
    """
    Convert 34.62% -> 34.62
    """
    text = clean_text(value)
    text = text.replace("%", "").replace(",", "")
    try:
        return float(text)
    except:
        return None


def parse_number(value):
    """
    Convert 14,400 -> 14400
    """
    text = clean_text(value)
    text = text.replace(",", "")
    try:
        return int(float(text))
    except:
        return None


def detect_segment(value):
    text = clean_text(value).lower().replace(" ", "")

    if text.startswith("overall"):
        return "Overall"
    if text.startswith("first"):
        return "First"
    if text.startswith("business"):
        return "Business"
    if text.startswith("economyplus") or text.startswith("economyp"):
        return "Economy Plus"
    if text.startswith("economy"):
        return "Economy"

    return None


def detect_topic(value):
    text = clean_text(value).upper()

    topic_map = {
        "WEBSITE": "Website",
        "CALL": "Call Center",
        "MOBILE": "Mobile App",
        "TICKETING": "Ticketing",
        "CHECK": "Check-in",
        "LOUNGE": "Lounge",
        "BOARDING": "Boarding",
        "CABIN CREW": "Cabin Crew",
        "IFE": "In-flight Entertainment",
        "MEAL": "In-flight Meal",
        "BEVERAGE": "In-flight Beverage",
        "CABIN CLE": "Cabin Cleanliness",
        "LAVATORY": "Lavatory Cleanliness",
        "SEAT": "Seat",
        "ARRIVAL": "Arrival & Baggage",
        "IRREGULARITY": "Irregularity",
        "ROP": "ROP"
    }

    for key, topic in topic_map.items():
        if text.startswith(key) or key in text:
            return topic

    return None


# -----------------------------
# IDENTIFY COLUMN NAMES
# -----------------------------
columns = list(df.columns)

file_col = "File"
page_col = "Page"

# First 7 extracted table columns
col_topic = columns[0]
col_5 = columns[1]
col_4 = columns[2]
col_3 = columns[3]
col_2 = columns[4]
col_1 = columns[5]
col_rsp = columns[6]

# -----------------------------
# CLEAN DATA
# -----------------------------
records = []

current_topic = None

for _, row in df.iterrows():

    first_cell = clean_text(row[col_topic])

    # Detect topic header row
    detected_topic = detect_topic(first_cell)
    if detected_topic:
        current_topic = detected_topic

    # Detect segment row
    segment = detect_segment(first_cell)

    if segment and current_topic:

        very_satisfied = parse_percent(row[col_5])
        satisfied = parse_percent(row[col_4])
        acceptable = parse_percent(row[col_3])
        dissatisfied = parse_percent(row[col_2])
        very_dissatisfied = parse_percent(row[col_1])
        rsp = parse_number(row[col_rsp])

        # Only keep rows with real percentage data
        if very_satisfied is not None and satisfied is not None:

            csat = very_satisfied + satisfied

            avg_rating = (
                (very_satisfied * 5)
                + (satisfied * 4)
                + (acceptable * 3 if acceptable is not None else 0)
                + (dissatisfied * 2 if dissatisfied is not None else 0)
                + (very_dissatisfied * 1 if very_dissatisfied is not None else 0)
            ) / 100

            records.append({
                "File": row[file_col],
                "Month": extract_month_from_file(row[file_col]),
                "Page": row[page_col],
                "Topic": current_topic,
                "Segment": segment,
                "Very satisfied": very_satisfied,
                "Satisfied": satisfied,
                "Acceptable": acceptable,
                "Dissatisfied": dissatisfied,
                "Very dissatisfied": very_dissatisfied,
                "RSP": rsp,
                "CSAT": round(csat, 2),
                "Average Rating": round(avg_rating, 2)
            })


# -----------------------------
# EXPORT CLEAN DATA
# -----------------------------
clean_df = pd.DataFrame(records)

clean_df.to_excel(output_file, index=False)

print("Done!")
print(f"Created file: {output_file}")
print(f"Total rows: {len(clean_df)}")