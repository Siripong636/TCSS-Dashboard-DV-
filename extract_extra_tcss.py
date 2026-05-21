import os
import re
import pandas as pd


MASTER_FILE = "master_tcss.xlsx"
STRUCTURED_FILE = "structured_tcss.xlsx"
OUTPUT_FILE = "extra_tcss.xlsx"

STATION_TOPICS = [
    "Arrival & Baggage",
    "Boarding",
    "Lounge",
    "Irregularity",
]

MONTH_WORDS = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
    "SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def extract_month_from_file(filename):
    match = re.search(r"(\d{6})", str(filename))
    if match:
        ym = match.group(1)
        return f"{ym[:4]}-{ym[4:]}"
    return ""


def normalize_page(value):
    if pd.isna(value):
        return ""

    text = clean_text(value)

    try:
        return str(int(float(text)))
    except Exception:
        return text


def normalize_key(value):
    text = clean_text(value).upper()
    return re.sub(r"[^A-Z0-9]", "", text)


def parse_number(value):
    if pd.isna(value):
        return None

    text = clean_text(value)
    text = text.replace(",", "").replace("%", "").strip()

    if text == "":
        return None

    try:
        return float(text)
    except Exception:
        return None


def parse_percent(value):
    number = parse_number(value)

    if number is None:
        return None

    if 0 <= number <= 1:
        number = number * 100

    if 0 <= number <= 100:
        return round(number, 2)

    return None


def parse_rsp(value):
    if pd.isna(value):
        return None

    text = clean_text(value)

    if "%" in text:
        return None

    text = text.replace(",", "").strip()

    if text == "":
        return None

    try:
        number = float(text)
        if number >= 0:
            return int(round(number))
    except Exception:
        return None

    return None


def standard_topic(text):
    compact = normalize_key(text)

    if "ARRIVAL" in compact or "BAGGAGE" in compact:
        return "Arrival & Baggage"
    if "BOARDING" in compact:
        return "Boarding"
    if "LOUNGE" in compact:
        return "Lounge"
    if "IRREGULARITY" in compact:
        return "Irregularity"

    return None


def looks_like_station_table_page(text):
    upper = clean_text(text).upper()
    compact = normalize_key(text)

    has_station_word = "STATION" in upper or "STATION" in compact
    has_scale = "5-4" in upper or "2-1" in upper or "#RSP" in upper or "RSP" in upper
    has_satisfaction_title = "SATISFACTION" in upper or "SATISFACTION" in compact

    return has_station_word and has_scale and has_satisfaction_title


def detect_station_topic_from_text(text):
    text = clean_text(text)
    upper = text.upper()
    compact = normalize_key(text)

    if not looks_like_station_table_page(text):
        return None

    patterns = [
        rf"SATISFACTION\s+BY\s+STATION\s+FOR\s+(.+?)\s+OF\s+({MONTH_WORDS})\s+\d{{4}}",
        rf"SATISFACTION\s+FOR\s+(.+?)\s+OF\s+({MONTH_WORDS})\s+\d{{4}}",
        r"SATISFACTION\s+BY\s+STATION\s+FOR\s+(.+?)(?=\s+SCALE|\s+STATION|\s*$)",
        r"SATISFACTION\s+FOR\s+(.+?)(?=\s+SCALE|\s+STATION|\s*$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, upper, flags=re.IGNORECASE)
        if match:
            topic = standard_topic(match.group(1))
            if topic in STATION_TOPICS:
                return topic

    if "SATISFACTIONFORARRIVAL" in compact or "SATISFACTIONFORBAGGAGE" in compact:
        return "Arrival & Baggage"

    if "SATISFACTIONBYSTATIONFORARRIVAL" in compact or "SATISFACTIONBYSTATIONFORBAGGAGE" in compact:
        return "Arrival & Baggage"

    if "SATISFACTIONFORIRREGULARITY" in compact or "SATISFACTIONBYSTATIONFORIRREGULARITY" in compact:
        return "Irregularity"

    if "SATISFACTIONFORBOARDING" in compact or "SATISFACTIONBYSTATIONFORBOARDING" in compact:
        return "Boarding"

    if "SATISFACTIONFORLOUNGE" in compact or "SATISFACTIONBYSTATIONFORLOUNGE" in compact:
        return "Lounge"

    return None


def load_master():
    if not os.path.exists(MASTER_FILE):
        print(f"Warning: {MASTER_FILE} not found.")
        return pd.DataFrame(columns=["File", "Page", "Content", "Month"])

    raw_df = pd.read_excel(MASTER_FILE)
    raw_df.columns = raw_df.columns.astype(str).str.strip()

    for col in ["File", "Page", "Content"]:
        if col not in raw_df.columns:
            raw_df[col] = ""

    raw_df["File"] = raw_df["File"].astype(str).str.strip()
    raw_df["Page"] = raw_df["Page"].apply(normalize_page)
    raw_df["Content"] = raw_df["Content"].astype(str)
    raw_df["Month"] = raw_df["File"].apply(extract_month_from_file)

    return raw_df


def load_structured():
    if not os.path.exists(STRUCTURED_FILE):
        print(f"Warning: {STRUCTURED_FILE} not found.")
        return pd.DataFrame()

    return pd.read_excel(STRUCTURED_FILE, header=None)


def load_old_extra_sheets():
    old_sheets = {}

    if not os.path.exists(OUTPUT_FILE):
        return old_sheets

    try:
        xls = pd.ExcelFile(OUTPUT_FILE)
        for sheet in xls.sheet_names:
            old_sheets[sheet] = pd.read_excel(OUTPUT_FILE, sheet_name=sheet)
    except Exception:
        old_sheets = {}

    return old_sheets


def row_find_file_page(row_values):
    found_file = ""
    found_page = ""

    for idx, value in enumerate(row_values):
        text = clean_text(value)

        match = re.search(r"(TCSS_\d{6}\.pdf)", text, flags=re.IGNORECASE)

        if match:
            found_file = match.group(1)

            for j in range(idx + 1, min(idx + 8, len(row_values))):
                possible_page = normalize_page(row_values[j])
                if possible_page and possible_page.isdigit():
                    found_page = possible_page
                    break

            break

    return found_file, found_page


def build_structured_rows(structured_df):
    rows = []

    current_file = ""
    current_page = ""

    if structured_df.empty:
        return pd.DataFrame(columns=["File", "Page", "Month", "RowValues", "RowText"])

    for _, row in structured_df.iterrows():
        row_values = row.tolist()

        row_file, row_page = row_find_file_page(row_values)

        if row_file:
            current_file = row_file

        if row_page:
            current_page = row_page

        if not current_file or not current_page:
            continue

        month = extract_month_from_file(current_file)

        row_text = " ".join(
            clean_text(v)
            for v in row_values
            if clean_text(v)
        )

        rows.append({
            "File": current_file,
            "Page": normalize_page(current_page),
            "Month": month,
            "RowValues": row_values,
            "RowText": row_text,
        })

    return pd.DataFrame(rows)


def build_page_topic_lookup(raw_df, structured_rows_df):
    page_topic_lookup = {}

    for _, row in raw_df.iterrows():
        file = clean_text(row.get("File", ""))
        page = normalize_page(row.get("Page", ""))
        content = clean_text(row.get("Content", ""))

        if not file or not page:
            continue

        topic = detect_station_topic_from_text(content)

        if topic:
            page_topic_lookup[(file, page)] = topic

    if not structured_rows_df.empty:
        page_text_df = (
            structured_rows_df
            .groupby(["File", "Page"], as_index=False)
            .agg({
                "RowText": lambda x: " ".join(clean_text(v) for v in x)
            })
        )

        for _, row in page_text_df.iterrows():
            file = clean_text(row["File"])
            page = normalize_page(row["Page"])
            text = clean_text(row["RowText"])

            topic = detect_station_topic_from_text(text)

            if topic:
                page_topic_lookup[(file, page)] = topic

    return page_topic_lookup


def get_topic_for_page(file, page, page_topic_lookup):
    file = clean_text(file)
    page = normalize_page(page)

    if (file, page) in page_topic_lookup:
        return page_topic_lookup[(file, page)]

    return None


def extract_nationalities(raw_df):
    records = []

    group_patterns = {
        "European": [r"EUROPEAN"],
        "British": [r"BRITISH"],
        "American": [r"AMERICAN"],
        "Asian": [r"ASIAN", r"ASIA"],
        "Thai": [r"THAI"],
        "Middle Eastern": [r"MIDDLE\s+EASTERN", r"MIDDLE\s+EAST"],
        "African": [r"AFRICAN"],
        "AUS & NZ": [
            r"AUS\s*&\s*NZ",
            r"AUSTRALIAN\s*&\s*NEW\s+ZEALANDER",
            r"AUSTRALIA"
        ],
        "Others": [r"OTHERS", r"OTHER"],
    }

    for _, row in raw_df.iterrows():
        content = clean_text(row["Content"])
        content_upper = content.upper()
        month = row["Month"]

        if not month:
            continue

        if "NATIONALIT" not in content_upper and "THAI CUSTOMER SATISFACTION SURVEY" not in content_upper:
            continue

        for group, patterns in group_patterns.items():
            for pattern in patterns:
                match = re.search(
                    rf"{pattern}\s+([0-9]+(?:\.[0-9]+)?)%\s*\(?\s*([0-9,]+)\s*\)?",
                    content_upper,
                    flags=re.IGNORECASE,
                )

                if match:
                    records.append({
                        "Month": month,
                        "Nationality Group": group,
                        "Percent": float(match.group(1)),
                        "Count": int(match.group(2).replace(",", "")),
                    })
                    break

                match = re.search(
                    rf"{pattern}\s*[=:]\s*([0-9,]+)",
                    content_upper,
                    flags=re.IGNORECASE,
                )

                if match:
                    records.append({
                        "Month": month,
                        "Nationality Group": group,
                        "Percent": None,
                        "Count": int(match.group(1).replace(",", "")),
                    })
                    break

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=["Month", "Nationality Group", "Percent", "Count"])

    df = (
        df.groupby(["Month", "Nationality Group"], as_index=False)
        .agg({
            "Percent": "max",
            "Count": "max",
        })
    )

    for month in df["Month"].dropna().unique():
        mask = df["Month"] == month

        if df.loc[mask, "Percent"].isna().all():
            total = df.loc[mask, "Count"].sum()

            if total > 0:
                df.loc[mask, "Percent"] = df.loc[mask, "Count"] / total * 100

    df["Percent"] = pd.to_numeric(df["Percent"], errors="coerce").round(2)
    df["Count"] = pd.to_numeric(df["Count"], errors="coerce")

    return df


def extract_gender(raw_df):
    records = []

    gender_patterns = {
        "Male": r"MALE",
        "Female": r"FEMALE",
        "Prefer not to say": r"PREFER\s+NOT\s+TO\s+SAY",
    }

    for _, row in raw_df.iterrows():
        content_upper = clean_text(row["Content"]).upper()
        month = row["Month"]

        if not month:
            continue

        for gender, pattern in gender_patterns.items():
            match = re.search(
                rf"(?:{pattern})[,\s:=-]*([0-9]+(?:\.[0-9]+)?)%",
                content_upper,
                flags=re.IGNORECASE,
            )

            if match and match.group(1) is not None:
                records.append({
                    "Month": month,
                    "Gender": gender,
                    "Percent": float(match.group(1)),
                })

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=["Month", "Gender", "Percent"])

    df = df.groupby(["Month", "Gender"], as_index=False).agg({"Percent": "max"})
    df["Percent"] = pd.to_numeric(df["Percent"], errors="coerce").round(2)

    return df


def extract_age_group(raw_df):
    records = []

    age_patterns = {
        "Gen Alpha": r"GEN\s+ALPHA",
        "Gen Z": r"GEN\s+Z",
        "Gen Y": r"GEN\s+Y",
        "Gen X": r"GEN\s+X",
        "Baby boomer": r"BABY\s+BOOMER",
        "Silent Gen": r"SILENT\s+GEN",
    }

    for _, row in raw_df.iterrows():
        content_upper = clean_text(row["Content"]).upper()
        month = row["Month"]

        if not month:
            continue

        for group, pattern in age_patterns.items():
            match = re.search(
                rf"(?:{pattern}).*?([0-9]+(?:\.[0-9]+)?)%",
                content_upper,
                flags=re.IGNORECASE,
            )

            if match and match.group(1) is not None:
                records.append({
                    "Month": month,
                    "Age Group": group,
                    "Percent": float(match.group(1)),
                })

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=["Month", "Age Group", "Percent"])

    df = df.groupby(["Month", "Age Group"], as_index=False).agg({"Percent": "max"})
    df["Percent"] = pd.to_numeric(df["Percent"], errors="coerce").round(2)

    return df


def extract_purpose(raw_df):
    records = []

    purpose_patterns = {
        "Leisure travel": r"LEISURE\s+TRAVEL",
        "Business travel": r"BUSINESS\s+TRAVEL",
        "Visit friend/relative": r"VISIT\s+FRIEND|FRIEND/RELATIVE|FRIEND\s*/\s*RELATIVE|RELATIVE",
        "Others": r"OTHERS|OTHER",
    }

    for _, row in raw_df.iterrows():
        content_upper = clean_text(row["Content"]).upper()
        month = row["Month"]

        if not month:
            continue

        for purpose, pattern in purpose_patterns.items():
            match = re.search(
                rf"(?:{pattern}).*?([0-9]+(?:\.[0-9]+)?)%",
                content_upper,
                flags=re.IGNORECASE,
            )

            if match and match.group(1) is not None:
                try:
                    percent_value = float(match.group(1))
                except Exception:
                    continue

                records.append({
                    "Month": month,
                    "Purpose": purpose,
                    "Percent": percent_value,
                })

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=["Month", "Purpose", "Percent"])

    df = df.groupby(["Month", "Purpose"], as_index=False).agg({"Percent": "max"})
    df["Percent"] = pd.to_numeric(df["Percent"], errors="coerce").round(2)

    return df


INVALID_STATION_KEYS = {
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


def looks_like_station_name(value):
    text = clean_text(value)

    if not text:
        return False

    upper = text.upper()
    key = normalize_key(text)

    # สำคัญ: ไม่ตัด STATIONS เพราะเป็น row รวมจากต้นฉบับ
    if key in INVALID_STATION_KEYS:
        return False

    if "TCSS_" in upper or ".PDF" in upper:
        return False

    if re.fullmatch(r"[0-9,.\-%]+", text):
        return False

    if len(text) > 90:
        return False

    if not re.search(r"[A-Za-z]", text):
        return False

    bad_fragments = [
        "SATISFACTION",
        "DISSATISFACTION",
        "ACCEPTABLE",
        "VERY",
        "PERCENT",
        "SCALE",
        "RESPONSE",
        "PASSENGER",
        "SURVEY",
        "TOTAL",
        "AVERAGE",
    ]

    if any(fragment in upper for fragment in bad_fragments):
        return False

    return True


def extract_station_records_from_row(row_values, file, page, month, topic):
    records = []
    i = 0

    while i < len(row_values):
        station = clean_text(row_values[i])

        if not looks_like_station_name(station):
            i += 1
            continue

        numeric_values = []
        last_used_index = i
        found_record = False

        for j in range(i + 1, min(i + 12, len(row_values))):
            cell = row_values[j]
            cell_text = clean_text(cell)

            if not cell_text:
                continue

            if len(numeric_values) < 3:
                percent_value = parse_percent(cell)

                if percent_value is not None:
                    numeric_values.append(percent_value)
                    last_used_index = j
                    continue

                if looks_like_station_name(cell_text):
                    break

            else:
                rsp_value = parse_rsp(cell)

                if rsp_value is not None:
                    sat_54 = numeric_values[0]
                    neutral_3 = numeric_values[1]
                    dis_21 = numeric_values[2]

                    total_pct = sat_54 + neutral_3 + dis_21

                    if 80 <= total_pct <= 120:
                        records.append({
                            "File": file,
                            "Month": month,
                            "Page": page,
                            "Topic": topic,
                            "Station": station,
                            "Satisfaction 5-4": sat_54,
                            "Neutral 3": neutral_3,
                            "Dissatisfaction 2-1": dis_21,
                            "RSP": rsp_value,
                        })

                        last_used_index = j
                        found_record = True
                        break

                if looks_like_station_name(cell_text):
                    break

        if found_record:
            i = last_used_index + 1
        else:
            i += 1

    return records


def extract_station_data(structured_rows_df, page_topic_lookup):
    records = []

    if structured_rows_df.empty:
        return pd.DataFrame(columns=[
            "File",
            "Month",
            "Page",
            "Topic",
            "Station",
            "Satisfaction 5-4",
            "Neutral 3",
            "Dissatisfaction 2-1",
            "RSP",
        ])

    for _, row in structured_rows_df.iterrows():
        file = clean_text(row["File"])
        page = normalize_page(row["Page"])
        month = clean_text(row["Month"])
        row_values = row["RowValues"]

        if not file or not page or not month:
            continue

        topic = get_topic_for_page(
            file=file,
            page=page,
            page_topic_lookup=page_topic_lookup,
        )

        if topic not in STATION_TOPICS:
            continue

        row_records = extract_station_records_from_row(
            row_values=row_values,
            file=file,
            page=page,
            month=month,
            topic=topic,
        )

        records.extend(row_records)

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=[
            "File",
            "Month",
            "Page",
            "Topic",
            "Station",
            "Satisfaction 5-4",
            "Neutral 3",
            "Dissatisfaction 2-1",
            "RSP",
        ])

    df["Station"] = df["Station"].astype(str).str.strip()
    df["StationKey"] = df["Station"].apply(normalize_key)

    df = df[~df["StationKey"].isin(INVALID_STATION_KEYS)].copy()

    numeric_cols = [
        "Satisfaction 5-4",
        "Neutral 3",
        "Dissatisfaction 2-1",
        "RSP",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=[
            "Month",
            "Topic",
            "Station",
            "Satisfaction 5-4",
            "Neutral 3",
            "Dissatisfaction 2-1",
            "RSP",
        ]
    )

    df = df.drop_duplicates(
        subset=["Month", "Topic", "Station"],
        keep="last",
    )

    df = df.drop(columns=["StationKey"])
    df = df.sort_values(["Month", "Topic", "Station"])

    return df


def combine_with_old(old_sheets, sheet_name, new_df, subset_cols):
    old_df = old_sheets.get(sheet_name, pd.DataFrame())

    if old_df.empty:
        return new_df.copy()

    if new_df.empty:
        return old_df.copy()

    combined = pd.concat([old_df, new_df], ignore_index=True)

    for col in subset_cols:
        if col not in combined.columns:
            combined[col] = None

    combined = combined.drop_duplicates(
        subset=subset_cols,
        keep="last",
    )

    return combined


def main():
    print("Loading files...")

    raw_df = load_master()
    structured_df = load_structured()
    old_sheets = load_old_extra_sheets()

    print("Preparing structured rows...")
    structured_rows_df = build_structured_rows(structured_df)

    print("Building page topic lookup...")
    page_topic_lookup = build_page_topic_lookup(
        raw_df=raw_df,
        structured_rows_df=structured_rows_df,
    )

    print("")
    print("Detected station topic pages:")
    if page_topic_lookup:
        for key, topic in sorted(page_topic_lookup.items()):
            print(f"{key[0]} | page {key[1]} | {topic}")
    else:
        print("No station topic pages detected.")

    print("")
    print("Extracting nationalities...")
    nationalities_df = extract_nationalities(raw_df)

    print("Extracting gender...")
    gender_df = extract_gender(raw_df)

    print("Extracting age group...")
    age_group_df = extract_age_group(raw_df)

    print("Extracting purpose of journey...")
    purpose_df = extract_purpose(raw_df)

    print("Extracting station data...")
    station_df = extract_station_data(
        structured_rows_df=structured_rows_df,
        page_topic_lookup=page_topic_lookup,
    )

    # รวมข้อมูลเก่าเฉพาะ profile sheets
    # Station sheet สร้างใหม่ทุกครั้ง เพื่อไม่ให้ข้อมูลผิดเดิมปนกลับมา
    nationalities_df = combine_with_old(
        old_sheets=old_sheets,
        sheet_name="nationalities",
        new_df=nationalities_df,
        subset_cols=["Month", "Nationality Group"],
    )

    gender_df = combine_with_old(
        old_sheets=old_sheets,
        sheet_name="gender",
        new_df=gender_df,
        subset_cols=["Month", "Gender"],
    )

    age_group_df = combine_with_old(
        old_sheets=old_sheets,
        sheet_name="age_group",
        new_df=age_group_df,
        subset_cols=["Month", "Age Group"],
    )

    purpose_df = combine_with_old(
        old_sheets=old_sheets,
        sheet_name="purpose",
        new_df=purpose_df,
        subset_cols=["Month", "Purpose"],
    )

    print("")
    print(f"Writing {OUTPUT_FILE}...")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        nationalities_df.to_excel(writer, sheet_name="nationalities", index=False)
        gender_df.to_excel(writer, sheet_name="gender", index=False)
        age_group_df.to_excel(writer, sheet_name="age_group", index=False)
        purpose_df.to_excel(writer, sheet_name="purpose", index=False)
        station_df.to_excel(writer, sheet_name="station", index=False)

    print("Done!")
    print(f"Created / updated file: {OUTPUT_FILE}")

    print("")
    if not station_df.empty:
        print("Station data summary:")
        print(station_df.groupby(["Month", "Topic"]).size().to_string())

        print("")
        print("Stations summary rows:")
        station_total_check = station_df[
            station_df["Station"].astype(str).str.upper() == "STATIONS"
        ]
        if station_total_check.empty:
            print("No Stations row found.")
        else:
            print(station_total_check[[
                "Month",
                "Topic",
                "Station",
                "Satisfaction 5-4",
                "Neutral 3",
                "Dissatisfaction 2-1",
                "RSP"
            ]].to_string(index=False))
    else:
        print("No station data extracted.")


if __name__ == "__main__":
    main()