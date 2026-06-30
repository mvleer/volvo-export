"""
Shared fixtures for Volvo trip pipeline tests.

All synthetic fixture data lives here. Tests must NOT use real project files
as input fixtures — use tmp_path-based helpers below instead.
"""

import csv
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Raw fixture header — matches the actual Volvo app export format
# ---------------------------------------------------------------------------
RAW_FIXTURE_HEADER = [
    "Category",
    "Started",
    "Start odometer (km)",
    "Start address",
    "Stopped",
    "End odometer (km)",
    "End address",
    "Duration",
    "Distance (km)",
    "Fuel consumption (litres)",
    "Title",
    "User Notes",
    "Column1",
]


def _trip(started, stopped, odometer_start, odometer_end, distance, fuel,
          category="Unassigned"):
    return {
        "Category": category,
        "Started": started,
        "Start odometer (km)": str(odometer_start),
        "Start address": "Test Start",
        "Stopped": stopped,
        "End odometer (km)": str(odometer_end),
        "End address": "Test End",
        "Duration": "30m",
        "Distance (km)": distance,
        "Fuel consumption (litres)": fuel,
        "Title": "",
        "User Notes": "",
        "Column1": "",
    }


# ---------------------------------------------------------------------------
# Fixture trips — raw format (DD/MM/YYYY, distance in tenths with " km" suffix)
# ---------------------------------------------------------------------------

# Normal 2024 trip: 125,3 raw → 12,53 km cleaned
TRIP_2024_DEC = _trip(
    "15/12/2024 10:00", "15/12/2024 10:30", 100000, 100125, "125,3 km", "2,1 l"
)

# Year-boundary trip: Dec 31, 2024
TRIP_2024_BOUNDARY = _trip(
    "31/12/2024 22:00", "31/12/2024 22:45", 100500, 100680, "180,0 km", "3,5 l"
)

# Midnight-spanning trip: starts Jan 31, stops Feb 1 (year remains 2025)
TRIP_2025_MIDNIGHT = _trip(
    "31/01/2025 23:50", "01/02/2025 00:10", 102000, 102040, "40,0 km", "0,8 l"
)

# Duplicate target: this exact trip appears in both export files
TRIP_2025_MARCH = _trip(
    "15/03/2025 14:00", "15/03/2025 14:45", 101500, 101650, "150,0 km", "3,0 l"
)

# Zero fuel consumption
TRIP_2025_JUNE = _trip(
    "10/06/2025 09:00", "10/06/2025 09:15", 103000, 103020, "20,0 km", "0,0 l"
)


def _write_raw_csv(path: Path, trips: list) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIXTURE_HEADER, delimiter=";")
        writer.writeheader()
        for trip in trips:
            writer.writerow(trip)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_dir(tmp_path):
    """
    Two overlapping export files in a temp raw/ directory.
    TRIP_2025_MARCH appears in both exports — the dedup test target.
    """
    rd = tmp_path / "raw"
    rd.mkdir()
    _write_raw_csv(
        rd / "export1.csv",
        [TRIP_2024_DEC, TRIP_2024_BOUNDARY, TRIP_2025_MIDNIGHT, TRIP_2025_MARCH],
    )
    _write_raw_csv(
        rd / "export2.csv",
        [TRIP_2025_MARCH, TRIP_2025_JUNE],  # TRIP_2025_MARCH is the duplicate
    )
    return rd


@pytest.fixture
def merged_rows(raw_dir):
    """Merged, deduplicated, sorted rows — result of the pipeline merge step."""
    from volvo_trips import merge_and_dedup, read_raw_files
    return merge_and_dedup(read_raw_files(raw_dir))


@pytest.fixture
def output_dir(tmp_path, raw_dir):
    """Run the full pipeline against fixture data; return the output directory."""
    from volvo_trips import run_pipeline
    out = tmp_path / "output"
    out.mkdir()
    run_pipeline(raw_dir, out)
    return out
