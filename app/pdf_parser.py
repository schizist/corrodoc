import pdfplumber
from pathlib import Path


def parse_geotech_pdf(pdf_path):
    results = {
        "project_name": None,
        "project_number": None,
        "geotech_company": None,
        "borings": [],
        "ph_values": [],
        "resistivity_values": [],
        "sulfates": [],
        "chlorides": [],
    }

    debug_dir = Path("outputs")
    debug_dir.mkdir(exist_ok=True)
    debug_file = debug_dir / "pdf_text_dump.txt"

    all_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            all_text.append(f"\n{'='*80}\nPAGE {i}\n{'='*80}\n{text}\n")

    debug_file.write_text("\n".join(all_text), encoding="utf-8")

    return results