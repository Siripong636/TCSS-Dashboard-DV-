#!/usr/bin/env python3
"""
extract_extra_tcss.py

Extract TCSS passenger profile and station-level satisfaction from master_tcss.xlsx.

Outputs extra_tcss.xlsx with sheets:
  - nationalities
  - gender
  - age_group
  - purpose
  - station
  - validation_summary

Key improvements:
  - Passenger profile is extracted only from page 2, preventing wrong values from charts on later pages
    (for example kiosk age charts on the Check-in page).
  - Month comes from filename TCSS_YYYYMM, not from text inside the PDF.
  - Nationality parser handles both old count-only format and newer percent + count format.
  - Purpose/Age/Gender parsers pair labels and percentages in sequence, which fixes pages where labels
    and percentages are visually arranged in separate columns/lines.
  - Station parser reads station pages from raw text using a state machine, so it can handle lines like
    '238 Tokyo' where an RSP value and next station name are merged.

Usage:
  python extract_extra_tcss.py
  python extract_extra_tcss.py --master-file master_tcss.xlsx --output-file extra_tcss.xlsx
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd


MONTH_RE = re.compile(r"(?P<ym>20\d{2}(?:0[1-9]|1[0-2]))")
MONTH_WORDS = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|"
    "SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)

STATION_TOPICS = {
    "ARRIVAL": "Arrival / Baggage",
    "BAGGAGE": "Arrival / Baggage",
    "BOARDING": "Boarding",
    "LOUNGE": "Lounge",
    "IRREGULARITY": "Irregularity Care",
}

INVALID_STATION_NAMES = {
    "",
    "STATION",
    "SCALE",
    "SATISFACTION",
    "SATISFIED",
    "DISSATISFIED",
    "ACCEPTABLE",
    "RSP",
    "FILE",
    "PAGE",
    "MONTH",
    "TOTAL",
    "PERCENT",
    "COMMENTS",
}


PROFILE_LABELS = {
    "gender": [
        ("Male", r"\bMALE\b"),
        ("Female", r"\bFEMALE\b"),
        ("Prefer not to say", r"\bP(?:RE)?FER\s+NO?T?\s+TO\s+SAY\b|\bPERFER\s+NO\s+TO\s+SAY\b"),
    ],
    "age_group": [
        ("Gen Alpha", r"\bGEN(?:ERATION)?\s+ALPHA\b"),
        ("Gen Z", r"\bGEN(?:ERATION)?\s+Z\b"),
        ("Gen Y", r"\bGEN(?:ERATION)?\s+Y\b"),
        ("Gen X", r"\bGEN(?:ERATION)?\s+X\b"),
        ("Baby boomer", r"\bBABY\s+BOOMER\b"),
        ("Silent Gen", r"\bSILENT\s+(?:GEN(?:ERATION)?)\b"),
    ],
    "purpose": [
        ("Leisure travel", r"\bLEISURE\s+TRAVEL\b"),
        ("Business travel", r"\bBUSINESS\s+TRAVEL\b"),
        ("Visit friend/relative", r"\bVISIT\s+FRIEND\s*/?\s*RELATIVE\b|\bFRIEND\s*/\s*RELATIVE\b|\bVISIT\s+FRIEND\b"),
        ("Others", r"\bOTHERS?(?:\s*\(PLEASE\s+SPECIFY\))?\b"),
    ],
}


NATIONALITY_PATTERNS = [
    ("AUS & NZ", r"\bAUS\s*&\s*NZ\b|\bAUSTRALIAN\s*&\s*NEW\s+ZEALANDER\b|\bAUSTRALIA(?:N)?\b"),
    ("Thai", r"\bTHAI\b"),
    ("Asian", r"\bASIAN\b|\bASIA\b"),
    ("American", r"\bAMERICAN\b"),
    ("Others", r"\bOTHERS?\b"),
    ("British", r"\bBRITISH\b"),
    ("European", r"\bEUROPEAN\b"),
    ("Middle Eastern", r"\bMIDDLE\s+EASTERN\b|\bMIDDLE\s+EAST\b"),
    ("African", r"\bAFRICAN\b"),
]


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u200b", " ")).strip()


def clean_lines(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [clean_text(line) for line in str(value).splitlines() if clean_text(line)]


def extract_month_from_file(filename: object) -> str:
    match = MONTH_RE.search(str(filename))
    if not match:
        return ""
    ym = match.group("ym")
    return f"{ym[:4]}-{ym[4:]}"


def normalize_page(value: object) -> str:
    text = clean_text(value)
    try:
        return str(int(float(text)))
    except Exception:
        return text


def normalize_key(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", clean_text(value).upper())


def parse_number(value: object) -> Optional[float]:
    text = clean_text(value).replace(",", "").replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def parse_percent_token(value: object) -> Optional[float]:
    text = clean_text(value)
    number = parse_number(text)
    if number is None:
        return None
    # If the original token includes %, 0.62% means 0.62, not 62.
    if "%" not in text and 0 <= number <= 1:
        number *= 100
    if 0 <= number <= 100:
        return round(number, 2)
    return None


def parse_int_token(value: object) -> Optional[int]:
    number = parse_number(value)
    if number is None or number < 0:
        return None
    return int(round(number))


def first_position(text: str, label_patterns: list[tuple[str, str]]) -> Optional[int]:
    positions = []
    for _, pattern in label_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            positions.append(match.start())
    return min(positions) if positions else None


def category_start_position(text: str, category: str) -> Optional[int]:
    labels = PROFILE_LABELS[category]
    # For purpose, do not use "Others" as a start anchor because nationality also has Others.
    # For gender, do not use "Prefer not to say" as a start anchor because it can be a tiny label above a chart.
    if category == "purpose":
        labels = [(name, pat) for name, pat in labels if name != "Others"]
    elif category == "gender":
        labels = [(name, pat) for name, pat in labels if name != "Prefer not to say"]
    return first_position(text, labels)


def first_position_after(text: str, start: int, categories: list[str]) -> Optional[int]:
    positions: list[int] = []
    sub = text[start:]
    for category in categories:
        pos = category_start_position(sub, category)
        if pos is not None and pos > 0:
            positions.append(start + pos)
    return min(positions) if positions else None


def extract_responses(profile_text: str) -> Optional[int]:
    match = re.search(r"\bResponses\s*=\s*([0-9,]+)", profile_text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r"response\s+from\s+([0-9,]+)\s+passengers", profile_text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def token_sequence_extract(region_text: str, labels: list[tuple[str, str]]) -> dict[str, float]:
    """Assign percentages to labels by visual/text order, robust to label columns and value columns."""
    if not region_text:
        return {}

    label_regex = "|".join(f"(?P<L{i}>{pattern})" for i, (_, pattern) in enumerate(labels))
    percent_regex = r"(?P<PCT>\d+(?:\.\d+)?\s*%)"
    token_re = re.compile(f"{label_regex}|{percent_regex}", flags=re.IGNORECASE)

    label_order: list[str] = []
    values: list[float] = []

    for match in token_re.finditer(region_text):
        if match.lastgroup == "PCT":
            pct = parse_percent_token(match.group("PCT"))
            if pct is not None:
                values.append(pct)
        elif match.lastgroup and match.lastgroup.startswith("L"):
            idx = int(match.lastgroup[1:])
            label_order.append(labels[idx][0])

    result: dict[str, float] = {}
    for label, value in zip(label_order, values):
        # Prefer first occurrence; later same label can belong to a different chart on the same page.
        result.setdefault(label, value)
    return result


def local_label_percent_extract(region_text: str, labels: list[tuple[str, str]], stop_labels: list[tuple[str, str]] | None = None) -> dict[str, float]:
    """Extract a percent close to each label without crossing into the next label/category."""
    result: dict[str, float] = {}
    all_boundaries = labels + (stop_labels or [])
    boundary_re = re.compile("|".join(f"(?:{pat})" for _, pat in all_boundaries), flags=re.IGNORECASE)
    pct_re = re.compile(r"\d+(?:\.\d+)?\s*%", flags=re.IGNORECASE)

    for label, pattern in labels:
        for match in re.finditer(pattern, region_text, flags=re.IGNORECASE):
            tail = region_text[match.end() : match.end() + 140]
            pct_match = pct_re.search(tail)
            if not pct_match:
                continue
            boundary_match = boundary_re.search(tail)
            if boundary_match and boundary_match.start() < pct_match.start():
                continue
            pct = parse_percent_token(pct_match.group(0))
            if pct is not None:
                result[label] = pct
                break

    # If exactly one item is missing and the visible values sum to < 100, infer the missing chart slice.
    missing = [label for label, _ in labels if label not in result]
    if len(missing) == 1 and result:
        remainder = round(100 - sum(result.values()), 2)
        if 0 <= remainder <= 100:
            result[missing[0]] = remainder
    return result


def extract_profile_category(profile_text: str, category: str, stop_categories: Optional[list[str]] = None) -> dict[str, float]:
    labels = PROFILE_LABELS[category]
    upper_text = profile_text.upper()
    start = category_start_position(upper_text, category)
    if start is None:
        return {}

    end = len(profile_text)
    stop_categories = stop_categories or []
    stop_pos = first_position_after(upper_text, start + 1, stop_categories)
    if stop_pos is not None:
        end = stop_pos

    region = profile_text[start:end]

    if category == "purpose":
        # Purpose sometimes has two labels before two values (e.g. Leisure, Business, 54.02%, 24.70%).
        return token_sequence_extract(region, labels)

    stop_labels: list[tuple[str, str]] = []
    for stop_category in stop_categories:
        stop_labels.extend(PROFILE_LABELS[stop_category])
    return local_label_percent_extract(region, labels, stop_labels=stop_labels)


def extract_nationalities_for_profile(profile_text: str, total_responses: Optional[int]) -> list[dict]:
    text = clean_text(profile_text)
    records: list[dict] = []

    for group, label_pattern in NATIONALITY_PATTERNS:
        pct: Optional[float] = None
        count: Optional[int] = None

        # Newer format: Label 12.34% (1,234), including cases where % is omitted: Thai 18.62 (2,533)
        match = re.search(
            rf"(?:{label_pattern})\s*(?:=|:)?\s*(?P<pct>\d+(?:\.\d+)?)\s*%?\s*\(\s*(?P<count>\d[\d,]*)\s*\)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            maybe_pct = float(match.group("pct"))
            maybe_count = int(match.group("count").replace(",", ""))
            if 0 <= maybe_pct <= 100:
                pct = round(maybe_pct, 2)
                count = maybe_count

        # Older format: Label = 1,234. Only use if no percent+count match was found.
        if count is None:
            match = re.search(
                rf"(?:{label_pattern})\s*(?:=|:)\s*(?P<count>\d[\d,]*)\b",
                text,
                flags=re.IGNORECASE,
            )
            if match:
                count = int(match.group("count").replace(",", ""))

        if count is not None:
            if pct is None and total_responses:
                pct = round(count / total_responses * 100, 2)
            records.append({"Nationality Group": group, "Percent": pct, "Count": count})

    return records


def load_master(master_file: str) -> pd.DataFrame:
    path = Path(master_file)
    if not path.exists():
        raise SystemExit(f"Input not found: {path}. Run pdf_to_excel.py first.")
    df = pd.read_excel(path, dtype=str)
    df.columns = df.columns.astype(str).str.strip()
    for required in ["File", "Page", "Content"]:
        if required not in df.columns:
            raise SystemExit(f"Column '{required}' not found in {path}")
    if "Month" not in df.columns:
        df["Month"] = df["File"].apply(extract_month_from_file)
    df["Page"] = df["Page"].apply(normalize_page)
    df["Content"] = df["Content"].fillna("").astype(str)
    return df


def profile_pages(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df[raw_df["Page"].apply(normalize_page).eq("2")].copy()
    # Keep rows that look like TCSS profile pages.
    mask = df["Content"].str.contains("Responses|Response ratio|Sampling|GENDER|AGE GROUP", case=False, regex=True, na=False)
    return df[mask].copy()


def extract_profiles(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nationality_records: list[dict] = []
    gender_records: list[dict] = []
    age_records: list[dict] = []
    purpose_records: list[dict] = []

    for _, row in profile_pages(raw_df).iterrows():
        file_name = clean_text(row.get("File", ""))
        month = clean_text(row.get("Month", "")) or extract_month_from_file(file_name)
        profile_text = str(row.get("Content", ""))
        if not month:
            continue

        total_responses = extract_responses(profile_text)

        for item in extract_nationalities_for_profile(profile_text, total_responses):
            nationality_records.append({"File": file_name, "Month": month, **item})

        for label, value in extract_profile_category(profile_text, "gender", stop_categories=["age_group", "purpose"]).items():
            gender_records.append({"File": file_name, "Month": month, "Gender": label, "Percent": value})

        for label, value in extract_profile_category(profile_text, "age_group", stop_categories=["gender", "purpose"]).items():
            age_records.append({"File": file_name, "Month": month, "Age Group": label, "Percent": value})

        for label, value in extract_profile_category(profile_text, "purpose", stop_categories=[]).items():
            # Do not let nationality 'Others' after the chart overwrite purpose Others.
            purpose_records.append({"File": file_name, "Month": month, "Purpose": label, "Percent": value})

    nationalities_df = pd.DataFrame(nationality_records)
    gender_df = pd.DataFrame(gender_records)
    age_group_df = pd.DataFrame(age_records)
    purpose_df = pd.DataFrame(purpose_records)

    if not nationalities_df.empty:
        nationalities_df = (
            nationalities_df.groupby(["File", "Month", "Nationality Group"], as_index=False)
            .agg({"Percent": "first", "Count": "first"})
            .sort_values(["Month", "Nationality Group"])
        )
        nationalities_df["Percent"] = pd.to_numeric(nationalities_df["Percent"], errors="coerce").round(2)
        nationalities_df["Count"] = pd.to_numeric(nationalities_df["Count"], errors="coerce").astype("Int64")
    else:
        nationalities_df = pd.DataFrame(columns=["File", "Month", "Nationality Group", "Percent", "Count"])

    if not gender_df.empty:
        gender_df = gender_df.drop_duplicates(["Month", "Gender"], keep="first").sort_values(["Month", "Gender"])
    else:
        gender_df = pd.DataFrame(columns=["File", "Month", "Gender", "Percent"])

    if not age_group_df.empty:
        age_group_df = age_group_df.drop_duplicates(["Month", "Age Group"], keep="first").sort_values(["Month", "Age Group"])
    else:
        age_group_df = pd.DataFrame(columns=["File", "Month", "Age Group", "Percent"])

    if not purpose_df.empty:
        purpose_df = purpose_df.drop_duplicates(["Month", "Purpose"], keep="first").sort_values(["Month", "Purpose"])
    else:
        purpose_df = pd.DataFrame(columns=["File", "Month", "Purpose", "Percent"])

    return nationalities_df, gender_df, age_group_df, purpose_df


def detect_station_topic(text: str) -> Optional[str]:
    upper = clean_text(text).upper()
    if "STATION" not in upper or "5-4" not in upper or "#RSP" not in upper:
        return None

    # Prefer title-based detection.
    title_patterns = [
        rf"SATISFACTION\s+(?:BY\s+STATION\s+)?FOR\s+(?P<topic>.+?)\s+OF\s+(?:{MONTH_WORDS})\s+20\d{{2}}",
        r"SATISFACTION\s+(?:BY\s+STATION\s+)?FOR\s+(?P<topic>ARRIVAL\s*&?\s*BAGGAGE|BOARDING|LOUNGE|IRREGULARITY)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, upper, flags=re.IGNORECASE)
        if match:
            topic_text = match.group("topic")
            for key, topic in STATION_TOPICS.items():
                if key in topic_text:
                    return topic

    for key, topic in STATION_TOPICS.items():
        if key in upper:
            return topic
    return None


def is_percent_line(line: str) -> bool:
    return re.fullmatch(r"\d+(?:\.\d+)?%", clean_text(line)) is not None


def split_count_and_station(line: str) -> tuple[Optional[int], str]:
    text = clean_text(line)
    match = re.fullmatch(r"(?P<count>\d[\d,]*)\s+(?P<station>.+)", text)
    if match:
        return int(match.group("count").replace(",", "")), clean_text(match.group("station"))
    if re.fullmatch(r"\d[\d,]*", text):
        return int(text.replace(",", "")), ""
    return None, text


def looks_like_station_text(text: str) -> bool:
    value = clean_text(text)
    if not value:
        return False
    key = normalize_key(value)
    if key in INVALID_STATION_NAMES:
        return False
    if re.fullmatch(r"[0-9,\.\-%]+", value):
        return False
    if any(word in key for word in ["SATISFACTION", "DISSATISFACTION", "ACCEPTABLE", "SCALE", "COMMENTS", "TOTALCOMMENT"]):
        return False
    if len(value) > 80:
        return False
    return bool(re.search(r"[A-Za-z]", value))


def finalize_station_record(file_name: str, month: str, page: str, topic: str, station_parts: list[str], pcts: list[float], rsp: int) -> Optional[dict]:
    station = clean_text(" ".join(station_parts))
    if not looks_like_station_text(station):
        return None
    if len(pcts) != 3:
        return None
    total = round(sum(pcts), 2)
    validation = "ok" if 98.5 <= total <= 101.5 else "scale_total_not_100"
    return {
        "File": file_name,
        "Month": month,
        "Page": page,
        "Topic": topic,
        "Station": station,
        "Satisfaction 5-4": round(pcts[0], 2),
        "Neutral 3": round(pcts[1], 2),
        "Dissatisfaction 2-1": round(pcts[2], 2),
        "RSP": int(rsp),
        "Scale Total": total,
        "Validation": validation,
        "Source": "raw_page_text_state_machine",
    }


def extract_station_records_from_text(file_name: str, month: str, page: str, topic: str, content: str) -> list[dict]:
    lines = clean_lines(content)
    records: list[dict] = []
    station_parts: list[str] = []
    pcts: list[float] = []
    started = False

    for raw_line in lines:
        line = clean_text(raw_line)
        key = normalize_key(line)

        if key in {"STATION", "54", "3", "21", "RSP"} or line in {"5-4", "2-1", "#RSP"}:
            started = True
            continue

        if not started:
            # Some pages have the title first, then header; wait for Station/5-4 area.
            continue

        if line.upper().startswith("SCALE 4-5") or line.upper().startswith("SATISFACTION "):
            # Usually footer/title after table. Continue only if an active record is incomplete.
            if not station_parts or len(pcts) == 0:
                continue
            # If text after an incomplete station row is not useful, reset.
            station_parts = []
            pcts = []
            continue

        pct = parse_percent_token(line) if is_percent_line(line) else None
        if pct is not None:
            if not station_parts:
                continue
            if len(pcts) < 3:
                pcts.append(pct)
            continue

        if station_parts and len(pcts) == 3:
            rsp, next_station = split_count_and_station(line)
            if rsp is not None:
                record = finalize_station_record(file_name, month, page, topic, station_parts, pcts, rsp)
                if record:
                    records.append(record)
                station_parts = []
                pcts = []
                if next_station and looks_like_station_text(next_station):
                    station_parts = [next_station]
                continue

        # Not a percent and not a completed RSP. Treat as station name continuation.
        if looks_like_station_text(line):
            if len(pcts) == 0:
                station_parts.append(line)
            else:
                # A new station appeared before the current record was complete; reset to avoid corrupt rows.
                station_parts = [line]
                pcts = []

    return records


def extract_station_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for _, row in raw_df.iterrows():
        file_name = clean_text(row.get("File", ""))
        month = clean_text(row.get("Month", "")) or extract_month_from_file(file_name)
        page = normalize_page(row.get("Page", ""))
        content = str(row.get("Content", ""))
        if not file_name or not month or not content:
            continue

        topic = detect_station_topic(content)
        if not topic:
            continue

        records.extend(extract_station_records_from_text(file_name, month, page, topic, content))

    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "File",
                "Month",
                "Page",
                "Topic",
                "Station",
                "Satisfaction 5-4",
                "Neutral 3",
                "Dissatisfaction 2-1",
                "RSP",
                "Scale Total",
                "Validation",
                "Source",
            ]
        )

    # Clean duplicate station rows that appear on page continuations; keep the latest identical month-topic-station.
    df["StationKey"] = df["Station"].apply(normalize_key)
    df = df[~df["StationKey"].isin(INVALID_STATION_NAMES)].copy()
    for col in ["Page", "Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP", "Scale Total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Month", "Topic", "Station", "Satisfaction 5-4", "Neutral 3", "Dissatisfaction 2-1", "RSP"])
    df = df.sort_values(["Month", "Topic", "Station", "Page"])
    df = df.drop_duplicates(subset=["Month", "Topic", "StationKey"], keep="last")
    df = df.drop(columns=["StationKey"])
    return df.sort_values(["Month", "Topic", "Station"]).reset_index(drop=True)


def build_validation_summary(nationalities_df: pd.DataFrame, gender_df: pd.DataFrame, age_df: pd.DataFrame, purpose_df: pd.DataFrame, station_df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    checks = [
        ("nationalities", nationalities_df, "Nationality Group"),
        ("gender", gender_df, "Gender"),
        ("age_group", age_df, "Age Group"),
        ("purpose", purpose_df, "Purpose"),
        ("station", station_df, "Station"),
    ]
    for sheet, df, key_col in checks:
        if df.empty:
            frames.append({"Sheet": sheet, "Month": "", "Rows": 0, "DistinctItems": 0, "PercentSum": None, "Warnings": "empty"})
            continue
        for month, group in df.groupby("Month"):
            percent_sum = None
            warnings = []
            if "Percent" in group.columns:
                percent_sum = round(pd.to_numeric(group["Percent"], errors="coerce").sum(), 2)
                if sheet in {"gender", "age_group", "purpose", "nationalities"} and not (98.0 <= percent_sum <= 102.0):
                    warnings.append("percent_sum_not_100")
            if "Validation" in group.columns and (group["Validation"].astype(str) != "ok").any():
                warnings.append("row_validation_warning")
            frames.append(
                {
                    "Sheet": sheet,
                    "Month": month,
                    "Rows": len(group),
                    "DistinctItems": group[key_col].nunique(dropna=True) if key_col in group.columns else None,
                    "PercentSum": percent_sum,
                    "Warnings": ";".join(warnings) if warnings else "ok",
                }
            )
    return pd.DataFrame(frames)


def autosize_excel_columns(path: Path) -> None:
    try:
        from openpyxl import load_workbook
    except Exception:
        return
    wb = load_workbook(path)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for col_cells in ws.columns:
            col_letter = col_cells[0].column_letter
            max_len = 0
            for cell in col_cells[:2000]:
                value = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, min(len(value), 60))
            ws.column_dimensions[col_letter].width = max(10, min(max_len + 2, 45))
    wb.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TCSS passenger profile and station data.")
    parser.add_argument("--master-file", default="master_tcss.xlsx", help="Input from pdf_to_excel.py")
    parser.add_argument("--output-file", default="extra_tcss.xlsx", help="Output Excel workbook")
    args = parser.parse_args()

    raw_df = load_master(args.master_file)

    print("Extracting passenger profile from page 2 only...")
    nationalities_df, gender_df, age_df, purpose_df = extract_profiles(raw_df)

    print("Extracting station-level satisfaction from station pages...")
    station_df = extract_station_data(raw_df)

    validation_df = build_validation_summary(nationalities_df, gender_df, age_df, purpose_df, station_df)

    output_path = Path(args.output_file)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        nationalities_df.to_excel(writer, sheet_name="nationalities", index=False)
        gender_df.to_excel(writer, sheet_name="gender", index=False)
        age_df.to_excel(writer, sheet_name="age_group", index=False)
        purpose_df.to_excel(writer, sheet_name="purpose", index=False)
        station_df.to_excel(writer, sheet_name="station", index=False)
        validation_df.to_excel(writer, sheet_name="validation_summary", index=False)

    autosize_excel_columns(output_path)

    print(f"Created: {output_path}")
    print(f"Nationalities rows: {len(nationalities_df):,}")
    print(f"Gender rows:        {len(gender_df):,}")
    print(f"Age group rows:     {len(age_df):,}")
    print(f"Purpose rows:       {len(purpose_df):,}")
    print(f"Station rows:       {len(station_df):,}")

    station_warnings = station_df[station_df.get("Validation", pd.Series(dtype=str)).astype(str).ne("ok")]
    if not station_warnings.empty:
        print(f"Station validation warnings: {len(station_warnings):,}. Check the station sheet Validation column.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
