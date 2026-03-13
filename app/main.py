from pathlib import Path
from pdf_parser import parse_geotech_pdf
from report_generator import generate_report


def main():
    raw_path = input("Path to geotech report: ").strip().strip('"').strip("'")
    pdf_path = Path(raw_path)

    if not pdf_path.exists():
        print(f"\nFile not found: {pdf_path}")
        return

    data = parse_geotech_pdf(str(pdf_path))

    print("\nExtracted data:")
    for k, v in data.items():
        print(f"{k}: {v}")

    if not any([
        data.get("project_name"),
        data.get("project_number"),
        data.get("geotech_company"),
        data.get("borings"),
        data.get("ph_values"),
        data.get("resistivity_values"),
        data.get("sulfates"),
        data.get("chlorides"),
    ]):
        print("\nNo usable data was extracted yet. Parser logic still needs to be built.")
        return

    confirm = input("\nContinue with report generation? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    output = generate_report(data)
    print(f"\nReport created: {output}")


if __name__ == "__main__":
    main()