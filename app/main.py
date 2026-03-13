from pathlib import Path
from pdf_parser import parse_geotech_pdf
from report_generator import generate_report

def main():

    pdf_path = input("Path to geotech report: ").strip()

    data = parse_geotech_pdf(pdf_path)

    print("\nExtracted data:")
    for k, v in data.items():
        print(f"{k}: {v}")

    confirm = input("\nContinue with report generation? (y/n): ")

    if confirm.lower() != "y":
        print("Cancelled.")
        return

    output = generate_report(data)

    print(f"\nReport created: {output}")


if __name__ == "__main__":
    main()