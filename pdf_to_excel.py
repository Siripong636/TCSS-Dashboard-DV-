import os
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd

pdf_folder = "TCSS_PDF"

raw_records = []
table_records = []

for file in os.listdir(pdf_folder):

    if not file.lower().endswith(".pdf"):
        continue

    pdf_path = os.path.join(pdf_folder, file)

    print(f"Reading: {file}")

    # -----------------------------
    # 1) Extract text by PyMuPDF
    # -----------------------------
    try:
        doc = fitz.open(pdf_path)

        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text("text") or ""

            raw_records.append({
                "File": file,
                "Page": page_index + 1,
                "Content": text,
                "Source": "pymupdf"
            })

    except Exception as e:
        print(f"PyMuPDF failed for {file}: {e}")

    # -----------------------------
    # 2) Extract tables by pdfplumber
    # -----------------------------
    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):

                tables = page.extract_tables()

                for table_no, table in enumerate(tables, start=1):

                    if not table:
                        continue

                    cleaned_table = []

                    for row in table:
                        cleaned_row = [
                            "" if cell is None else str(cell).strip()
                            for cell in row
                        ]

                        if any(cell != "" for cell in cleaned_row):
                            cleaned_table.append(cleaned_row)

                    if not cleaned_table:
                        continue

                    temp_df = pd.DataFrame(cleaned_table)

                    temp_df["File"] = file
                    temp_df["Page"] = page_number
                    temp_df["TableNo"] = table_no

                    table_records.append(temp_df)

    except Exception as e:
        print(f"pdfplumber failed for {file}: {e}")


# -----------------------------
# Export raw text
# -----------------------------
raw_df = pd.DataFrame(raw_records)

raw_df.to_excel(
    "master_tcss.xlsx",
    index=False
)

print("Done! master_tcss.xlsx created.")

# -----------------------------
# Export structured tables
# -----------------------------
if table_records:
    structured_df = pd.concat(table_records, ignore_index=True)

    structured_df.to_excel(
        "structured_tcss.xlsx",
        index=False
    )

    print("Done! structured_tcss.xlsx created.")
else:
    print("No structured tables found.")