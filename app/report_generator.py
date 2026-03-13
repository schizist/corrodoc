from pathlib import Path
from docxtpl import DocxTemplate

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = BASE_DIR / "templates" / "corrosivity_template.docx"
OUTPUT_DIR = BASE_DIR / "outputs"


def generate_report(data):
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = DocxTemplate(str(TEMPLATE))

    context = {
        "PROJECT_NAME": data.get("project_name") or "",
        "PROJECT_NUMBER": data.get("project_number") or "",
        "GEOTECH_COMPANY": data.get("geotech_company") or "",
    }

    doc.render(context)

    out = OUTPUT_DIR / "report.docx"
    doc.save(str(out))

    return out