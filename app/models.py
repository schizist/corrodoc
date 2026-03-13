from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class ExtractionLogEntry:
    field_name: str
    message: str
    confidence: ConfidenceLevel
    page_number: int | None = None
    source: str | None = None


@dataclass(slots=True)
class ExtractedTable:
    page_number: int
    index_on_page: int
    headers: list[str]
    rows: list[dict[str, str]]


@dataclass(slots=True)
class BoringTestResult:
    boring_id: str
    ph: float | None = None
    soil_resistivity_ohm_cm: float | None = None
    sulfate_ppm: float | None = None
    chloride_ppm: float | None = None
    source_page: int | None = None

    def to_report_row(self) -> dict[str, str]:
        return {
            "boring_id": self.boring_id,
            "ph": _format_number(self.ph),
            "soil_resistivity_ohm_cm": _format_number(self.soil_resistivity_ohm_cm),
            "sulfate_ppm": _format_number(self.sulfate_ppm),
            "chloride_ppm": _format_number(self.chloride_ppm),
        }


@dataclass(slots=True)
class GeotechReport:
    source_pdf: str
    project_name: str | None = None
    project_number: str | None = None
    geotechnical_company: str | None = None
    boring_results: list[BoringTestResult] = field(default_factory=list)
    extracted_tables: list[ExtractedTable] = field(default_factory=list)
    extraction_log: list[ExtractionLogEntry] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def ph_values(self) -> list[float]:
        return [result.ph for result in self.boring_results if result.ph is not None]

    @property
    def resistivity_values(self) -> list[float]:
        return [
            result.soil_resistivity_ohm_cm
            for result in self.boring_results
            if result.soil_resistivity_ohm_cm is not None
        ]

    @property
    def sulfates(self) -> list[float]:
        return [result.sulfate_ppm for result in self.boring_results if result.sulfate_ppm is not None]

    @property
    def chlorides(self) -> list[float]:
        return [
            result.chloride_ppm
            for result in self.boring_results
            if result.chloride_ppm is not None
        ]


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:g}"
