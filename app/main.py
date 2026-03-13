from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.pdf_parser import parse_geotech_pdf
from app.report_generator import generate_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prototype CLI for generating cathodic protection soil corrosivity reports.",
    )
    parser.add_argument("pdf", type=Path, help="Path to the geotechnical report PDF.")
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Optional path to a DOCX template. Defaults to templates/corrosivity_template.docx.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for generated files and parser debug artifacts.",
    )
    parser.add_argument(
        "--report-name",
        default="corrosivity_report.docx",
        help="Filename for the generated DOCX report.",
    )
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="Print the parsed report payload as JSON.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    return parser


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(args.log_level)

    if not args.pdf.exists():
        parser.error(f"PDF not found: {args.pdf}")

    report = parse_geotech_pdf(args.pdf, debug_dir=args.output_dir)

    if args.dump_json:
        print(json.dumps(report.to_dict(), indent=2))

    output_path = generate_report(
        report=report,
        output_dir=args.output_dir,
        template_path=args.template,
        report_name=args.report_name,
    )

    print(f"Report created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
