from __future__ import annotations

from pathlib import Path

from docxtpl import DocxTemplate

from app.models import GeotechReport

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = BASE_DIR / "templates" / "corrosivity_template.docx"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"


def generate_report(
    report: GeotechReport,
    output_dir: str | Path | None = None,
    template_path: str | Path | None = None,
    report_name: str = "corrosivity_report.docx",
) -> Path:
    template = Path(template_path) if template_path is not None else DEFAULT_TEMPLATE
    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")

    destination_dir = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)

    document = DocxTemplate(str(template))
    document.render(_build_context(report))

    output_path = destination_dir / report_name
    document.save(str(output_path))
    return output_path


def _build_context(report: GeotechReport) -> dict[str, object]:
    return {
        "PROJECT_NAME": report.project_name or "",
        "PROJECT_NUMBER": report.project_number or "",
        "GEOTECH_COMPANY": report.geotechnical_company or "",
        "BORING_RESULTS": [result.to_report_row() for result in report.boring_results],
        "PH_VALUES": ", ".join(f"{value:g}" for value in report.ph_values),
        "RESISTIVITY_VALUES": ", ".join(f"{value:g}" for value in report.resistivity_values),
        "SULFATE_VALUES": ", ".join(f"{value:g}" for value in report.sulfates),
        "CHLORIDE_VALUES": ", ".join(f"{value:g}" for value in report.chlorides),
        "EXTRACTION_LOG": [
            {
                "field_name": entry.field_name,
                "message": entry.message,
                "confidence": entry.confidence.value,
                "page_number": entry.page_number or "",
                "source": entry.source or "",
            }
            for entry in report.extraction_log
        ],
    }
