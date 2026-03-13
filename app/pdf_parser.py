from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
import pdfplumber

from app.models import (
    BoringTestResult,
    ConfidenceLevel,
    ExtractedTable,
    ExtractionLogEntry,
    GeotechReport,
)

LOGGER = logging.getLogger(__name__)

PROJECT_NAME_PATTERNS = [
    re.compile(r"Project\s+Name\s*[:\-]\s*(?P<value>[^\n\r]+)", re.IGNORECASE),
    re.compile(r"Project\s*[:\-]\s*(?P<value>[^\n\r]+)", re.IGNORECASE),
]
PROJECT_NUMBER_PATTERNS = [
    re.compile(r"Project\s+(?:No\.?|Number)\s*[:\-]\s*(?P<value>[A-Z0-9\-_./]+)", re.IGNORECASE),
    re.compile(r"(?:Job|Reference)\s+(?:No\.?|Number)\s*[:\-]\s*(?P<value>[A-Z0-9\-_./]+)", re.IGNORECASE),
]
COMPANY_PATTERNS = [
    re.compile(
        r"(?P<value>[A-Z][A-Za-z0-9&.,'()\- ]+(?:Geotechnical|Engineering|Engineers|Consultants|Associates))",
        re.IGNORECASE,
    ),
]


def parse_geotech_pdf(pdf_path: str | Path, debug_dir: str | Path | None = None) -> GeotechReport:
    pdf_file = Path(pdf_path)
    report = GeotechReport(source_pdf=str(pdf_file))
    output_dir = Path(debug_dir) if debug_dir is not None else Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_text: list[str] = []

    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            all_text.append(_format_page_dump(page_number, text))
            if text:
                report.raw_text = f"{report.raw_text}\n\n{text}".strip()

            for table_index, raw_table in enumerate(page.extract_tables() or [], start=1):
                extracted_table = _table_to_model(raw_table, page_number, table_index)
                if extracted_table is None:
                    continue
                report.extracted_tables.append(extracted_table)

    (output_dir / "pdf_text_dump.txt").write_text("\n".join(all_text), encoding="utf-8")

    _extract_metadata(report)
    _extract_boring_results(report)

    LOGGER.info(
        "Parsed %s with %d boring rows and %d extracted tables.",
        pdf_file.name,
        len(report.boring_results),
        len(report.extracted_tables),
    )
    return report


def _format_page_dump(page_number: int, text: str) -> str:
    divider = "=" * 80
    return f"\n{divider}\nPAGE {page_number}\n{divider}\n{text}\n"


def _table_to_model(raw_table: list[list[str | None]], page_number: int, table_index: int) -> ExtractedTable | None:
    cleaned_rows = [[_clean_cell(cell) for cell in row] for row in raw_table if any(_clean_cell(cell) for cell in row)]
    if len(cleaned_rows) < 2:
        return None

    width = max(len(row) for row in cleaned_rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in cleaned_rows]
    headers = [_normalize_header(value) or f"column_{index + 1}" for index, value in enumerate(normalized_rows[0])]
    rows = [dict(zip(headers, row, strict=False)) for row in normalized_rows[1:]]
    return ExtractedTable(page_number=page_number, index_on_page=table_index, headers=headers, rows=rows)


def _clean_cell(cell: str | None) -> str:
    return re.sub(r"\s+", " ", (cell or "")).strip()


def _normalize_header(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized


def _extract_metadata(report: GeotechReport) -> None:
    report.project_name = _extract_first_match(report, "project_name", PROJECT_NAME_PATTERNS)
    report.project_number = _extract_first_match(report, "project_number", PROJECT_NUMBER_PATTERNS)
    report.geotechnical_company = _extract_first_match(report, "geotechnical_company", COMPANY_PATTERNS)


def _extract_first_match(
    report: GeotechReport,
    field_name: str,
    patterns: list[re.Pattern[str]],
) -> str | None:
    for pattern in patterns:
        match = pattern.search(report.raw_text)
        if not match:
            continue
        value = match.group("value").strip(" :-")
        report.extraction_log.append(
            ExtractionLogEntry(
                field_name=field_name,
                message=f"Matched '{value}' from report text.",
                confidence=ConfidenceLevel.MEDIUM,
                source="text",
            )
        )
        return value

    report.extraction_log.append(
        ExtractionLogEntry(
            field_name=field_name,
            message="No match found in report text.",
            confidence=ConfidenceLevel.LOW,
            source="text",
        )
    )
    return None


def _extract_boring_results(report: GeotechReport) -> None:
    results_by_id: dict[str, BoringTestResult] = {}

    for table in report.extracted_tables:
        dataframe = pd.DataFrame(table.rows)
        if dataframe.empty:
            continue

        boring_column = _find_matching_column(dataframe.columns, ["boring", "boring_id", "boring_no", "sample"])
        if boring_column is None:
            continue

        ph_column = _find_matching_column(dataframe.columns, ["ph", "soil_ph"])
        resistivity_column = _find_matching_column(
            dataframe.columns,
            ["resistivity", "soil_resistivity", "resistivity_ohm_cm", "resistivity_ohm-cm"],
        )
        sulfate_column = _find_matching_column(dataframe.columns, ["sulfate", "sulfates", "sulfate_ppm"])
        chloride_column = _find_matching_column(dataframe.columns, ["chloride", "chlorides", "chloride_ppm"])

        for _, row in dataframe.iterrows():
            boring_id = _clean_boring_id(str(row.get(boring_column, "")).strip())
            if not boring_id:
                continue

            result = results_by_id.setdefault(
                boring_id,
                BoringTestResult(boring_id=boring_id, source_page=table.page_number),
            )
            result.ph = _prefer_existing(result.ph, _parse_numeric_value(row.get(ph_column)) if ph_column else None)
            result.soil_resistivity_ohm_cm = _prefer_existing(
                result.soil_resistivity_ohm_cm,
                _parse_numeric_value(row.get(resistivity_column)) if resistivity_column else None,
            )
            result.sulfate_ppm = _prefer_existing(
                result.sulfate_ppm,
                _parse_numeric_value(row.get(sulfate_column)) if sulfate_column else None,
            )
            result.chloride_ppm = _prefer_existing(
                result.chloride_ppm,
                _parse_numeric_value(row.get(chloride_column)) if chloride_column else None,
            )

        if boring_column:
            report.extraction_log.append(
                ExtractionLogEntry(
                    field_name="boring_results",
                    message=f"Extracted boring rows from table {table.index_on_page} on page {table.page_number}.",
                    confidence=ConfidenceLevel.HIGH,
                    page_number=table.page_number,
                    source="table",
                )
            )

    report.boring_results = sorted(results_by_id.values(), key=lambda item: item.boring_id)

    if not report.boring_results:
        report.extraction_log.append(
            ExtractionLogEntry(
                field_name="boring_results",
                message="No boring table with expected columns was found.",
                confidence=ConfidenceLevel.LOW,
                source="table",
            )
        )


def _find_matching_column(columns: pd.Index, candidates: list[str]) -> str | None:
    for column in columns:
        normalized = _normalize_header(str(column))
        if any(candidate in normalized for candidate in candidates):
            return str(column)
    return None


def _clean_boring_id(value: str) -> str:
    match = re.search(r"\b(B[- ]?\d+[A-Z]?|BH[- ]?\d+[A-Z]?|Boring[- ]?\d+[A-Z]?)\b", value, re.IGNORECASE)
    if match:
        return match.group(1).replace(" ", "").upper()
    stripped = value.strip().upper()
    return stripped if stripped and any(character.isdigit() for character in stripped) else ""


def _parse_numeric_value(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _prefer_existing(current: float | None, candidate: float | None) -> float | None:
    return current if current is not None else candidate
