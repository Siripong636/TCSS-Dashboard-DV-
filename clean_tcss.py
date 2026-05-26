#!/usr/bin/env python3
"""
clean_tcss.py

Build clean_tcss_rating.xlsx from master_tcss.xlsx.

This version parses the satisfaction rating tables from page text instead of relying only
on pdfplumber table cell positions. That makes it more stable when PDF table extraction
shifts columns or merges cells.

Outputs columns:
  File, Month, Page, Topic, Segment,
  Very satisfied, Satisfied, Acceptable, Dissatisfied, Very dissatisfied, RSP,
  CSAT, Average Rating, Scale Total, Validation

Usage:
  python clean_tcss.py
  python clean_tcss.py --master-file master_tcss.xlsx --output-file clean_tcss_rating.xlsx
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


MONTH_RE = re.compile(r"(?P<ym>20\d{2}(?:0[1-9]|1[0-2]))")

TOPIC_HEADERS: list[tuple[str, str]] = [
    ("Contact Center", r"CALL\s+CENTER"),
    ("Mobile App", r"MOBILE\s+APP\.?"),
    ("THAI Website", r"(?<!THAI\s)WEBSITE"),
    ("Ticketing", r"TICKETING"),
    ("Check-in", r"CHECK\s*-\s*IN"),
    ("Lounge", r"LOUNGE(?:\s+BANGKOK)?"),
    ("Boarding", r"BOARDING"),
    ("Cabin Crew", r"CABIN\s+CREW"),
    ("Cabin Cleanliness", r"CABIN\s+CLEANLINESS(?:\s*\(\s*BANGKOK\s*\))?"),
    ("Lavatory Cleanliness", r"LAVATORY\s+CLEANLINESS"),
    ("Seat Feature", r"SEAT"),
    ("In-flight Entertainment", r"IFE"),
    ("In-flight Meal", r"MEALS?"),
    ("In-flight Beverage", r"BEVERAGES?"),
    ("Arrival / Baggage", r"ARRIVAL\s*&?\s*BAGGAGE(?:\s*\(\s*BANGKOK\s*\))?"),
    ("Irregularity Care", r"IRREGULARITY"),
    ("ROP", r"ROP"),
]

SEGMENT_RE = re.compile(
    r"\b(?P<segment>Overall|First|Business|Economy\s+Plus|Economy)\b\s+"
    r"(?P<very_satisfied>\d+(?:\.\d+)?%|100%)\s+"
    r"(?P<satisfied>\d+(?:\.\d+)?%|100%)\s+"
    r"(?P<acceptable>\d+(?:\.\d+)?%|100%)\s+"
    r"(?P<dissatisfied>\d+(?:\.\d+)?%|100%)\s+"
    r"(?P<very_dissatisfied>\d+(?:\.\d+)?%|100%)\s+"
    r"(?P<rsp>\d[\d,]*)\b",
    flags=re.IGNORECASE,
)

HEADER_SUFFIX_RE = r"\s+(?:VERY\s+)?(?:SATISFIED|Satisfied)"


EXPECTED_TOPIC_ORDER = [topic for topic, _ in TOPIC_HEADERS]
EXPECTED_SEGMENT_ORDER = ["Overall", "First", "Business", "Economy Plus", "Economy"]


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u200b", " ")).strip()


def extract_month_from_file(filename: object) -> str:
    match = MONTH_RE.search(str(filename))
    if not match:
        return ""
    ym = match.group("ym")
    return f"{ym[:4]}-{ym[4:]}"


def parse_percent(value: object) -> Optional[float]:
    text = clean_text(value).replace("%", "").replace(",", "")
    if not text:
        return None
    try:
        return round(float(text), 2)
    except Exception:
        return None


def parse_int(value: object) -> Optional[int]:
    text = clean_text(value).replace(",", "")
    if not text:
        return None
    try:
        return int(round(float(text)))
    except Exception:
        return None


def normalize_segment(value: str) -> str:
    text = clean_text(value).lower()
    if text == "economy plus":
        return "Economy Plus"
    if text == "business":
        return "Business"
    if text == "economy":
        return "Economy"
    if text == "first":
        return "First"
    return "Overall"


def normalized_page_text(value: object) -> str:
    """Single-line text for regex parsing while preserving text order."""
    return clean_text(value)


def build_topic_regex(topic_pattern: str) -> re.Pattern:
    return re.compile(rf"(?P<header>{topic_pattern}){HEADER_SUFFIX_RE}", flags=re.IGNORECASE)


def find_topic_sections(text: str) -> list[dict]:
    """Find actual table headers, not titles, by requiring the header to be followed by 'Very satisfied'."""
    matches: list[dict] = []
    for topic, pattern in TOPIC_HEADERS:
        regex = build_topic_regex(pattern)
        for match in regex.finditer(text):
            matches.append({"topic": topic, "start": match.start(), "end": match.end(), "header": match.group("header")})

    matches.sort(key=lambda item: item["start"])

    # Remove overlaps: keep the longest/earliest meaningful header at the same position.
    deduped: list[dict] = []
    for item in matches:
        if deduped and item["start"] < deduped[-1]["end"]:
            # Prefer the earlier item unless this one is more specific and starts at same place.
            if item["start"] == deduped[-1]["start"] and len(item["header"]) > len(deduped[-1]["header"]):
                deduped[-1] = item
            continue
        deduped.append(item)

    sections: list[dict] = []
    for idx, item in enumerate(deduped):
        section_end = deduped[idx + 1]["start"] if idx + 1 < len(deduped) else len(text)
        sections.append({**item, "section_text": text[item["end"] : section_end]})

    return sections


def compute_metrics(vs: float, sat: float, acc: float, dis: float, vdis: float, rsp: Optional[int]) -> tuple[Optional[float], Optional[float], float, str]:
    scale_total = round(vs + sat + acc + dis + vdis, 2)
    flags: list[str] = []

    if rsp is None:
        flags.append("missing_rsp")
    elif rsp == 0:
        flags.append("zero_rsp")

    if scale_total == 0:
        return None, None, scale_total, ";".join(flags or ["empty_scale"])

    if not (98.5 <= scale_total <= 101.5):
        flags.append("scale_total_not_100")

    csat = round(vs + sat, 2)
    avg_rating = round(((vs * 5) + (sat * 4) + (acc * 3) + (dis * 2) + (vdis * 1)) / scale_total, 2)
    return csat, avg_rating, scale_total, ";".join(flags or ["ok"])


def extract_rating_records(raw_df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []

    for _, row in raw_df.iterrows():
        file_name = clean_text(row.get("File", ""))
        month = clean_text(row.get("Month", "")) or extract_month_from_file(file_name)
        page = row.get("Page", "")
        text = normalized_page_text(row.get("Content", ""))

        if not file_name or not month or not text:
            continue

        # Fast skip to avoid matching non-rating pages.
        if "#RSP" not in text.upper() or "SATISFIED" not in text.upper():
            continue

        for section in find_topic_sections(text):
            topic = section["topic"]
            section_text = section["section_text"]

            for seg_match in SEGMENT_RE.finditer(section_text):
                segment = normalize_segment(seg_match.group("segment"))
                vs = parse_percent(seg_match.group("very_satisfied"))
                sat = parse_percent(seg_match.group("satisfied"))
                acc = parse_percent(seg_match.group("acceptable"))
                dis = parse_percent(seg_match.group("dissatisfied"))
                vdis = parse_percent(seg_match.group("very_dissatisfied"))
                rsp = parse_int(seg_match.group("rsp"))

                if None in (vs, sat, acc, dis, vdis):
                    continue

                csat, avg_rating, scale_total, validation = compute_metrics(vs, sat, acc, dis, vdis, rsp)

                records.append(
                    {
                        "File": file_name,
                        "Month": month,
                        "Page": page,
                        "Topic": topic,
                        "Segment": segment,
                        "Very satisfied": vs,
                        "Satisfied": sat,
                        "Acceptable": acc,
                        "Dissatisfied": dis,
                        "Very dissatisfied": vdis,
                        "RSP": rsp,
                        "CSAT": csat,
                        "Average Rating": avg_rating,
                        "Scale Total": scale_total,
                        "Validation": validation,
                        "Source": "raw_page_text",
                        "TopicHeader": clean_text(section.get("header", "")),
                    }
                )

    clean_df = pd.DataFrame(records)
    if clean_df.empty:
        return pd.DataFrame(
            columns=[
                "File",
                "Month",
                "Page",
                "Topic",
                "Segment",
                "Very satisfied",
                "Satisfied",
                "Acceptable",
                "Dissatisfied",
                "Very dissatisfied",
                "RSP",
                "CSAT",
                "Average Rating",
                "Scale Total",
                "Validation",
                "Source",
                "TopicHeader",
            ]
        )

    clean_df["TopicOrder"] = clean_df["Topic"].map({topic: idx for idx, topic in enumerate(EXPECTED_TOPIC_ORDER)})
    clean_df["SegmentOrder"] = clean_df["Segment"].map({segment: idx for idx, segment in enumerate(EXPECTED_SEGMENT_ORDER)})
    clean_df["Page"] = pd.to_numeric(clean_df["Page"], errors="coerce")

    # Important: duplicates usually come from BANGKOK sub-tables on the same page. Keep the first main table.
    clean_df = clean_df.sort_values(["Month", "Page", "TopicOrder", "SegmentOrder"], na_position="last")
    clean_df = clean_df.drop_duplicates(subset=["Month", "Topic", "Segment"], keep="first")

    numeric_cols = [
        "Very satisfied",
        "Satisfied",
        "Acceptable",
        "Dissatisfied",
        "Very dissatisfied",
        "RSP",
        "CSAT",
        "Average Rating",
        "Scale Total",
    ]
    for col in numeric_cols:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    clean_df = clean_df.drop(columns=["TopicOrder", "SegmentOrder"])
    clean_df = clean_df.sort_values(["Month", "Page", "Topic", "Segment"], na_position="last").reset_index(drop=True)
    return clean_df


def build_summary(clean_df: pd.DataFrame) -> pd.DataFrame:
    if clean_df.empty:
        return pd.DataFrame(columns=["Month", "Topic", "Rows", "OverallRows", "MinScaleTotal", "MaxScaleTotal"])
    return (
        clean_df.groupby(["Month", "Topic"], as_index=False)
        .agg(
            Rows=("Segment", "count"),
            OverallRows=("Segment", lambda x: int((x == "Overall").sum())),
            MinScaleTotal=("Scale Total", "min"),
            MaxScaleTotal=("Scale Total", "max"),
        )
        .sort_values(["Month", "Topic"])
    )


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
    parser = argparse.ArgumentParser(description="Clean TCSS satisfaction rating tables.")
    parser.add_argument("--master-file", default="master_tcss.xlsx", help="Input from pdf_to_excel.py")
    parser.add_argument("--output-file", default="clean_tcss_rating.xlsx", help="Output Excel file")
    args = parser.parse_args()

    master_path = Path(args.master_file)
    if not master_path.exists():
        raise SystemExit(f"Input not found: {master_path}. Run pdf_to_excel.py first.")

    raw_df = pd.read_excel(master_path, dtype=str)
    raw_df.columns = raw_df.columns.astype(str).str.strip()

    for required in ["File", "Page", "Content"]:
        if required not in raw_df.columns:
            raise SystemExit(f"Column '{required}' not found in {master_path}")

    if "Month" not in raw_df.columns:
        raw_df["Month"] = raw_df["File"].apply(extract_month_from_file)

    print("Extracting satisfaction rating tables from raw page text...")
    clean_df = extract_rating_records(raw_df)
    summary_df = build_summary(clean_df)

    output_path = Path(args.output_file)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        clean_df.to_excel(writer, sheet_name="ratings", index=False)
        summary_df.to_excel(writer, sheet_name="summary", index=False)

    autosize_excel_columns(output_path)

    print(f"Created: {output_path}")
    print(f"Total rating rows: {len(clean_df):,}")
    if not clean_df.empty:
        print("Rows by month:")
        print(clean_df.groupby("Month").size().to_string())

        warnings = clean_df[clean_df["Validation"].astype(str).ne("ok")]
        if not warnings.empty:
            print(f"Validation warnings: {len(warnings):,} row(s). Check the 'Validation' column.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
