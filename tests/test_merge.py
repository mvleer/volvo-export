"""
Layer 2 — Merge & dedup.

Uses synthetic fixtures only (see conftest.py). Validates that combining
multiple overlapping exports produces a correctly deduplicated, sorted dataset
with no cross-year leakage between output files.
"""

import csv

import pytest


def test_no_duplicate_trips(merged_rows):
    keys = [(r["Started"], r["Start odometer (km)"]) for r in merged_rows]
    assert len(keys) == len(set(keys)), (
        f"Duplicate trips found after dedup: "
        f"{[k for k in keys if keys.count(k) > 1]}"
    )


def test_unique_count_matches_raw(raw_dir, merged_rows):
    """Total merged rows must equal the number of unique natural keys across all raw files."""
    from volvo_trips import read_raw_files
    raw_rows = read_raw_files(raw_dir)
    raw_unique_keys = {(r["Started"], r["Start odometer (km)"]) for r in raw_rows}
    assert len(merged_rows) == len(raw_unique_keys), (
        f"Merged has {len(merged_rows)} rows, "
        f"raw has {len(raw_unique_keys)} unique natural keys"
    )


def test_sorted_ascending_by_started(merged_rows):
    dates = [r["Started"] for r in merged_rows]
    assert dates == sorted(dates), "Merged rows are not sorted ascending by Started"


def test_no_cross_year_overlap(output_dir):
    """A trip's natural key must appear in exactly one year file."""
    year_files = sorted(output_dir.glob("volvo-trips-*.csv"))
    year_trips = {}
    for yf in year_files:
        year = int(yf.stem.split("-")[-1])
        with open(yf, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            year_trips[year] = {
                (r["Started"], r["Start odometer (km)"]) for r in reader
            }
    years = sorted(year_trips)
    for i, y in enumerate(years):
        for other_y in years[i + 1:]:
            overlap = year_trips[y] & year_trips[other_y]
            assert not overlap, (
                f"Trips appear in both {y} and {other_y}: {overlap}"
            )
