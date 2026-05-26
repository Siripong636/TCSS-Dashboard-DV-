#!/usr/bin/env python3
"""
pdf_to_excel.py

Robust TCSS PDF -> Excel extraction layer.

Outputs:
  1) master_tcss.xlsx      : one row per PDF page, using PyMuPDF text extraction
  2) structured_tcss.xlsx  : line-level structured text by default; pdfplumber tables if --extract-tables is used
  3) word_positions_tcss.xlsx (optional) : word-level coordinates for audit/debug

Why this version is safer than the original:
  - Finds PDFs from an input folder, current folder, TCSS_PDF, or /mnt/data.
  - Uses filename (TCSS_YYYYMM) as the canonical month, so PDF title typos do not shift the period.
  - Extracts page text, page dimensions, word counts, and optional word coordinates for traceability.
  - Creates a fast line-level structured file by default. Use --extract-tables for pdfplumber table extraction; --deep-tables adds extra strategies.
  - Keeps metadata columns consistently: File, Month, Year, MonthNo, Page, TableNo, Extractor, TableHash.

Usage examples:
  python pdf_to_excel.py
  python pdf_to_excel.py --pdf-dir TCSS_PDF --output-dir output
  python pdf_to_excel.py --no-word-positions
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyMuPDF. Install with: pip install pymupdf") from exc

try:
    import pdfplumber
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: pdfplumber. Install with: pip install pdfplumber") from exc


MONTH_RE = re.compile(r"(?P<ym>20\d{2}(?:0[1-9]|1[0-2]))")
DEFAULT_PDF_CANDIDATES = ["TCSS_PDF", ".", "/mnt/data"]


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"[ \t\r\f\v]+", " ", str(value)).strip()


def normalize_multiline_text(text: str) -> str:
    """Keep line breaks but remove noisy whitespace inside each line."""
    if not text:
        return ""
    lines = [clean_text(line) for line in text.replace("\x00", "").splitlines()]
    # Keep non-empty lines; TCSS pages use line breaks as useful separators.
    return "\n".join(line for line in lines if line)


def extract_ym_from_filename(filename: str) -> tuple[str, Optional[int], Optional[int]]:
    """Return (YYYY-MM, YYYY, MM) from filenames such as TCSS_202512(1).pdf."""
    match = MONTH_RE.search(str(filename))
    if not match:
        return "", None, None
    ym = match.group("ym")
    year = int(ym[:4])
    month_no = int(ym[4:])
    return f"{year:04d}-{month_no:02d}", year, month_no


def resolve_pdf_files(pdf_dir: Optional[str], pattern: str) -> List[Path]:
    candidates: list[Path]
    if pdf_dir:
        candidates = [Path(pdf_dir)]
    else:
        candidates = [Path(p) for p in DEFAULT_PDF_CANDIDATES]

    pdfs: list[Path] = []
    seen: set[Path] = set()

    for folder in candidates:
        folder = folder.expanduser().resolve()
        if not folder.exists() or not folder.is_dir():
            continue
        for pdf_path in sorted(folder.glob(pattern)):
            if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
                continue
            resolved = pdf_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            pdfs.append(resolved)

    # TCSS files first, then other PDFs if pattern is broad.
    pdfs.sort(key=lambda p: (0 if MONTH_RE.search(p.name) else 1, p.name.lower()))
    return pdfs


def table_hash(table: list[list[object]]) -> str:
    joined = "\n".join("\t".join(clean_text(cell) for cell in row) for row in table)
    return hashlib.sha1(joined.encode("utf-8", errors="ignore")).hexdigest()[:16]


def clean_table_rows(table: list[list[object]]) -> list[list[str]]:
    cleaned: list[list[str]] = []
    for row in table or []:
        values = [clean_text(cell) for cell in row]
        if any(values):
            cleaned.append(values)
    return cleaned


def pad_rows(rows: list[list[str]]) -> list[list[str]]:
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    return [r + [""] * (width - len(r)) for r in rows]


def extract_page_text_and_words(pdf_path: Path, keep_word_positions: bool) -> tuple[list[dict], list[dict]]:
    page_records: list[dict] = []
    word_records: list[dict] = []
    month, year, month_no = extract_ym_from_filename(pdf_path.name)

    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            raw_text = page.get_text("text") or ""
            content = normalize_multiline_text(raw_text)
            rect = page.rect
            words = page.get_text("words") or []

            page_records.append(
                {
                    "File": pdf_path.name,
                    "Month": month,
                    "Year": year,
                    "MonthNo": month_no,
                    "Page": page_index,
                    "Content": content,
                    "Source": "pymupdf_text",
                    "WordCount": len(words),
                    "CharCount": len(content),
                    "PageWidth": round(float(rect.width), 2),
                    "PageHeight": round(float(rect.height), 2),
                }
            )

            if keep_word_positions:
                for word_no, word in enumerate(words, start=1):
                    # PyMuPDF word tuple: x0, y0, x1, y1, text, block_no, line_no, word_no
                    x0, y0, x1, y1, text, block_no, line_no, word_in_line = word[:8]
                    word_records.append(
                        {
                            "File": pdf_path.name,
                            "Month": month,
                            "Page": page_index,
                            "WordNo": word_no,
                            "Text": clean_text(text),
                            "x0": round(float(x0), 2),
                            "y0": round(float(y0), 2),
                            "x1": round(float(x1), 2),
                            "y1": round(float(y1), 2),
                            "BlockNo": block_no,
                            "LineNo": line_no,
                            "WordInLine": word_in_line,
                        }
                    )

    return page_records, word_records


def pdfplumber_table_settings(deep_tables: bool = False) -> list[tuple[str, dict]]:
    """
    Default mode stays fast. Enable --deep-tables only when you need extra audit tables,
    because text-strategy table detection can be slow on slide-based PDFs.
    """
    settings: list[tuple[str, dict]] = [("pdfplumber_default", {})]
    if deep_tables:
        settings.extend([
            (
                "pdfplumber_lines",
                {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "intersection_tolerance": 5,
                    "text_tolerance": 3,
                },
            ),
            (
                "pdfplumber_text",
                {
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "text_tolerance": 3,
                },
            ),
        ])
    return settings


def build_line_structured_df(master_df: pd.DataFrame) -> pd.DataFrame:
    """Build a fast, deterministic structured file from PyMuPDF page lines."""
    rows: list[dict] = []
    if master_df.empty:
        return pd.DataFrame(columns=["File", "Month", "Year", "MonthNo", "Page", "LineNo", "LineText", "Source"])
    for _, row in master_df.iterrows():
        content = str(row.get("Content", "") or "")
        lines = [clean_text(line) for line in content.splitlines() if clean_text(line)]
        for line_no, line_text in enumerate(lines, start=1):
            rows.append(
                {
                    "File": row.get("File", ""),
                    "Month": row.get("Month", ""),
                    "Year": row.get("Year", ""),
                    "MonthNo": row.get("MonthNo", ""),
                    "Page": row.get("Page", ""),
                    "LineNo": line_no,
                    "LineText": line_text,
                    "Source": "pymupdf_line",
                }
            )
    return pd.DataFrame(rows)


def extract_tables(pdf_path: Path, deep_tables: bool = False) -> list[pd.DataFrame]:
    month, year, month_no = extract_ym_from_filename(pdf_path.name)
    table_frames: list[pd.DataFrame] = []
    seen_hashes: set[tuple[int, str]] = set()

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_table_no = 0
            for extractor_name, settings in pdfplumber_table_settings(deep_tables=deep_tables):
                try:
                    tables = page.extract_tables(table_settings=settings) or []
                except Exception as exc:
                    print(
                        f"  - pdfplumber warning: {pdf_path.name} page {page_number} "
                        f"strategy {extractor_name} failed: {exc}",
                        file=sys.stderr,
                    )
                    continue

                for table in tables:
                    cleaned = clean_table_rows(table)
                    if not cleaned:
                        continue

                    digest = table_hash(cleaned)
                    dedupe_key = (page_number, digest)
                    if dedupe_key in seen_hashes:
                        continue
                    seen_hashes.add(dedupe_key)

                    page_table_no += 1
                    rows = pad_rows(cleaned)
                    max_cols = max(len(row) for row in rows)
                    temp_df = pd.DataFrame(rows, columns=[f"Col{i}" for i in range(max_cols)])

                    temp_df.insert(0, "TableHash", digest)
                    temp_df.insert(0, "Extractor", extractor_name)
                    temp_df.insert(0, "TableNo", page_table_no)
                    temp_df.insert(0, "Page", page_number)
                    temp_df.insert(0, "MonthNo", month_no)
                    temp_df.insert(0, "Year", year)
                    temp_df.insert(0, "Month", month)
                    temp_df.insert(0, "File", pdf_path.name)
                    table_frames.append(temp_df)

    return table_frames


def autosize_excel_columns(path: Path) -> None:
    """Light formatting only; safe to skip if openpyxl is unavailable."""
    try:
        from openpyxl import load_workbook
    except Exception:
        return

    wb = load_workbook(path)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        for col_cells in ws.columns:
            header = col_cells[0].column_letter
            max_len = 0
            for cell in col_cells[:2000]:
                value = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, min(len(value), 80))
            ws.column_dimensions[header].width = max(10, min(max_len + 2, 60))
    wb.save(path)


def write_excel(df: pd.DataFrame, path: Path, sheet_name: str = "data") -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    autosize_excel_columns(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TCSS PDF text and tables to Excel.")
    parser.add_argument("--pdf-dir", default=None, help="Folder containing TCSS PDF files. Default: TCSS_PDF, current folder, then /mnt/data.")
    parser.add_argument("--pattern", default="*.pdf", help="PDF filename glob pattern. Default: *.pdf")
    parser.add_argument("--output-dir", default=".", help="Folder for output Excel files. Default: current folder")
    parser.add_argument("--master-file", default="master_tcss.xlsx", help="Raw page text output filename")
    parser.add_argument("--structured-file", default="structured_tcss.xlsx", help="Structured table output filename")
    parser.add_argument("--word-file", default="word_positions_tcss.xlsx", help="Word coordinate output filename")
    parser.add_argument("--no-word-positions", action="store_true", help="Skip word-level coordinate output")
    parser.add_argument("--extract-tables", action="store_true", help="Use pdfplumber to extract tables into structured_tcss.xlsx. Slower; line-level structured output is used by default.")
    parser.add_argument("--deep-tables", action="store_true", help="With --extract-tables, run additional pdfplumber table strategies. Slower, but useful for audits.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = resolve_pdf_files(args.pdf_dir, args.pattern)
    if not pdf_files:
        searched = args.pdf_dir if args.pdf_dir else ", ".join(DEFAULT_PDF_CANDIDATES)
        raise SystemExit(f"No PDF files found. Searched: {searched}")

    raw_records: list[dict] = []
    word_records: list[dict] = []
    table_frames: list[pd.DataFrame] = []
    errors: list[dict] = []

    print(f"Found {len(pdf_files)} PDF file(s).")
    for pdf_path in pdf_files:
        print(f"Reading: {pdf_path.name}")
        try:
            page_rows, word_rows = extract_page_text_and_words(
                pdf_path=pdf_path,
                keep_word_positions=not args.no_word_positions,
            )
            raw_records.extend(page_rows)
            word_records.extend(word_rows)
        except Exception as exc:
            errors.append({"File": pdf_path.name, "Step": "pymupdf", "Error": str(exc)})
            print(f"  - PyMuPDF failed: {exc}", file=sys.stderr)

        if args.extract_tables:
            try:
                table_frames.extend(extract_tables(pdf_path, deep_tables=args.deep_tables))
            except Exception as exc:
                errors.append({"File": pdf_path.name, "Step": "pdfplumber", "Error": str(exc)})
                print(f"  - pdfplumber failed: {exc}", file=sys.stderr)

    master_df = pd.DataFrame(raw_records)
    master_path = output_dir / args.master_file
    write_excel(master_df, master_path, sheet_name="raw_pages")
    print(f"Created: {master_path} ({len(master_df):,} page rows)")

    if args.extract_tables:
        if table_frames:
            structured_df = pd.concat(table_frames, ignore_index=True, sort=False)
        else:
            structured_df = pd.DataFrame(columns=["File", "Month", "Year", "MonthNo", "Page", "TableNo", "Extractor", "TableHash"])
        sheet_name = "tables"
        row_label = "table rows"
    else:
        structured_df = build_line_structured_df(master_df)
        sheet_name = "lines"
        row_label = "line rows"

    structured_path = output_dir / args.structured_file
    write_excel(structured_df, structured_path, sheet_name=sheet_name)
    print(f"Created: {structured_path} ({len(structured_df):,} {row_label})")

    if not args.no_word_positions:
        word_df = pd.DataFrame(word_records)
        word_path = output_dir / args.word_file
        write_excel(word_df, word_path, sheet_name="words")
        print(f"Created: {word_path} ({len(word_df):,} word rows)")

    if errors:
        error_path = output_dir / "tcss_extract_errors.xlsx"
        write_excel(pd.DataFrame(errors), error_path, sheet_name="errors")
        print(f"Created: {error_path} ({len(errors):,} error rows)")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
