"""
Layer 1 — Raw input integrity.

Tests the real raw/ directory. Fails fast so a malformed export is caught
before the pipeline runs. Does not import pipeline code.
"""

import csv
import re

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "raw"

RAW_REQUIRED_COLS = {
    "Category",
    "Started",
    "Stopped",
    "Start odometer (km)",
    "Distance (km)",
    "Fuel consumption (litres)",
}

# Both the old DD/MM/YYYY HH:MM and new ISO YYYY-MM-DD HH:MM formats are valid
DATE_PATTERN = re.compile(
    r"^(\d{2}/\d{2}/\d{4} \d{2}:\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2})$"
)


def _sniff_delimiter(path: Path) -> str:
    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        return dialect.delimiter
    except csv.Error:
        return ";"


def _real_raw_files():
    if not RAW_DIR.exists():
        return []
    return sorted(RAW_DIR.glob("*.csv"))


# ---------------------------------------------------------------------------
# Structure guards — run without parametrization so they fail clearly
# ---------------------------------------------------------------------------

def test_raw_dir_exists():
    assert RAW_DIR.exists(), f"raw/ directory not found at {RAW_DIR}"


def test_raw_dir_not_empty():
    files = _real_raw_files()
    assert len(files) > 0, "No CSV files found in raw/"


# ---------------------------------------------------------------------------
# Per-file tests — parametrized over every file in raw/
# ---------------------------------------------------------------------------

@pytest.fixture(params=_real_raw_files(), ids=lambda p: p.name)
def raw_file(request):
    return request.param


def test_raw_file_parseable(raw_file):
    delim = _sniff_delimiter(raw_file)
    with open(raw_file, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=delim))
    assert len(rows) > 0, f"{raw_file.name}: file is empty"


def test_raw_required_columns(raw_file):
    delim = _sniff_delimiter(raw_file)
    with open(raw_file, encoding="utf-8-sig") as f:
        header = set(csv.DictReader(f, delimiter=delim).fieldnames or [])
    missing = RAW_REQUIRED_COLS - header
    assert not missing, f"{raw_file.name}: missing columns {missing}"


def test_raw_date_format(raw_file):
    delim = _sniff_delimiter(raw_file)
    with open(raw_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for i, row in enumerate(reader, 2):
            for col in ("Started", "Stopped"):
                val = row.get(col, "").strip()
                if val:
                    assert DATE_PATTERN.match(val), (
                        f"{raw_file.name} row {i}: {col}='{val}' "
                        f"does not match DD/MM/YYYY HH:MM or YYYY-MM-DD HH:MM"
                    )


def test_raw_no_completely_empty_rows(raw_file):
    delim = _sniff_delimiter(raw_file)
    with open(raw_file, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for i, row in enumerate(reader, 2):
            assert any(v.strip() for v in row.values()), (
                f"{raw_file.name} row {i} is completely empty"
            )
