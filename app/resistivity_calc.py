from __future__ import annotations

from statistics import mean


def calculate_average_resistivity(readings: list[float]) -> float:
    if not readings:
        raise ValueError("At least one field resistivity reading is required.")
    return mean(readings)
