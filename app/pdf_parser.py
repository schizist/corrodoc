import pdfplumber

def parse_geotech_pdf(pdf_path):

    results = {
        "project_name": None,
        "project_number": None,
        "geotech_company": None,
        "borings": [],
        "ph_values": [],
        "resistivity_values": [],
        "sulfates": [],
        "chlorides": []
    }

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            # crude detection example
            if "Project:" in text:
                line = [l for l in text.split("\n") if "Project:" in l][0]
                results["project_name"] = line.split("Project:")[-1].strip()

    return results