"""
e2e — Full pipeline tests.

Marked @pytest.mark.slow; excluded from the default pytest run.
Run explicitly with: pytest -m slow

Uses the output_dir fixture (tmp_path-based) to run the full pipeline
against synthetic fixture data, then validates the result end-to-end.
"""

import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def _read_xlsx_rows(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = list(rows[0])
    return [dict(zip(headers, row)) for row in rows[1:]]


@pytest.mark.slow
def test_pipeline_produces_year_files(output_dir):
    year_files = sorted(output_dir.glob("volvo-trips-*.xlsx"))
    assert len(year_files) == 2, f"Expected 2 year files, got {[f.name for f in year_files]}"
    names = {f.stem for f in year_files}
    assert "volvo-trips-2024" in names
    assert "volvo-trips-2025" in names


@pytest.mark.slow
def test_pipeline_known_rows(output_dir):
    """Spot-check three known rows from fixture data."""
    rows_2024 = _read_xlsx_rows(output_dir / "volvo-trips-2024.xlsx")

    # TRIP_2024_DEC: distance 125,3 km raw → 12,53 km after ÷10
    dec = next((r for r in rows_2024 if r["Started"] == "2024-12-15 10:00"), None)
    assert dec is not None, "2024-12-15 trip not found in 2024 file"
    assert dec["Distance (km)"] == 12.53
    assert dec["Fuel consumption (l)"] == 2.1
    assert dec["Year"] == "2024-12"

    # TRIP_2024_BOUNDARY: Dec 31 stays in 2024
    boundary = next((r for r in rows_2024 if r["Started"] == "2024-12-31 22:00"), None)
    assert boundary is not None, "Dec 31 boundary trip not found in 2024 file"
    assert boundary["Year"] == "2024-12"

    rows_2025 = _read_xlsx_rows(output_dir / "volvo-trips-2025.xlsx")

    # TRIP_2025_MIDNIGHT: starts Jan 31, Stopped Feb 1 → Year = "2025-2"
    midnight = next((r for r in rows_2025 if r["Started"] == "2025-01-31 23:50"), None)
    assert midnight is not None, "Midnight-spanning trip not found in 2025 file"
    assert midnight["Stopped"] == "2025-02-01 00:10"
    assert midnight["Year"] == "2025-2"


@pytest.mark.slow
def test_pipeline_dedup_count(raw_dir, output_dir):
    """Total output rows must equal the unique natural key count across all raw files."""
    from volvo_trips_cleanup import read_raw_files
    raw_rows = read_raw_files(raw_dir)
    unique_count = len({(r["Started"], r["Start odometer (km)"]) for r in raw_rows})

    total_output = sum(
        len(_read_xlsx_rows(yf))
        for yf in output_dir.glob("volvo-trips-*.xlsx")
    )

    assert total_output == unique_count, (
        f"Output has {total_output} rows, expected {unique_count} unique raw trips"
    )


@pytest.mark.slow
def test_pipeline_as_subprocess(tmp_path, raw_dir):
    """Run volvo_trips_cleanup.py as a subprocess via CLI args."""
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "volvo_trips_cleanup.py"),
            "--raw-dir", str(raw_dir),
            "--output-dir", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    year_files = list(tmp_path.glob("volvo-trips-*.xlsx"))
    assert len(year_files) > 0, "Subprocess produced no output files"
