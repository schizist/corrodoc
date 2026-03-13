from docxtpl import DocxTemplate
from pathlib import Path

TEMPLATE = Path("templates/corrosivity_template.docx")


def generate_report(data):

    doc = DocxTemplate(TEMPLATE)

    context = {
        "PROJECT_NAME": data.get("project_name"),
        "PROJECT_NUMBER": data.get("project_number"),
        "GEOTECH_COMPANY": data.get("geotech_company"),
    }

    doc.render(context)

    out = Path("outputs/report.docx")
    doc.save(out)

    return out