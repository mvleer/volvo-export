# Volvo Trip Log Pipeline

Cleans and archives Volvo app trip exports as per-year Excel workbooks, combining multiple overlapping exports and deduplicating automatically.

## How it works

The Volvo app's export window is limited — older trips cannot be re-exported. This pipeline treats every export as an immutable raw archive and regenerates clean, per-year output files on demand.

```
raw/                         ← one file per year (never modified by the pipeline)
  volvo-export-2024.csv
  volvo-export-2025.csv
  volvo-export-2026.csv      ← add new year files as they come in

volvo-trips/                 ← generated output, one file per year
  volvo-trips-2024.xlsx
  volvo-trips-2025.xlsx
  volvo-trips-2026.xlsx
```

Each run reads all files in `raw/` (auto-detecting `;` or `,` delimiters), deduplicates across overlapping exports, and writes one `volvo-trips-YYYY.xlsx` per year under `volvo-trips/`. Years whose XLSX is already newer than the source raw file are skipped automatically.

## Usage

**Add a new export:**

Drop the CSV from the Volvo app into `raw/` with a descriptive filename, then run:

```bash
python volvo_trips_cleanup.py
```

**Override directories or force a full regeneration:**

```bash
python volvo_trips_cleanup.py --raw-dir path/to/raw --output-dir path/to/output
python volvo_trips_cleanup.py --force   # regenerate all years regardless of mtime
```

**Run the test suite:**

```bash
pytest tests/
```

End-to-end tests are excluded by default (they're slower). Run them with:

```bash
pytest tests/ -m slow
```

## Transformations applied

| Input (Volvo app) | Output |
|---|---|
| `31/01/2026 14:30` or `2026-01-31 14:30` | `2026-01-31 14:30` (ISO 8601) |
| `125,3 km` or `125.3 km` | `12.53` (÷10 correction, suffix removed, stored as float) |
| `0,2 l` or `0.2 l` | `0.2` (suffix removed, stored as float) |
| — | `Year` column added, e.g. `2026-1` |
| — | `l/100km` column added (fuel ÷ odo delta × 100; odo delta is the ground-truth distance) |
| — | `Odo delta (km)` column added (end − start odometer) |
| `Column1`, `Title`, `User Notes` | Dropped |

## Requirements

- Python 3.9+
- `openpyxl` (runtime, for XLSX output)
- `pytest` for tests only

## Project layout

```
volvo_trips_cleanup.py   Pipeline script
raw/                     Immutable raw exports from the Volvo app
volvo-trips/             Generated per-year XLSX workbooks
tests/
  conftest.py            Shared fixtures (synthetic data, no real files)
  test_raw_inputs.py     Layer 1 — raw file integrity
  test_merge.py          Layer 2 — dedup and sort correctness
  test_output.py         Layer 3 — per-year output quality
  test_pipeline_e2e.py   End-to-end pipeline tests (slow-marked)
doc/
  requirements.md        Functional and non-functional requirements
  specs/data-contract.md Input/output format specification
  ADR/arch-decisions.md  Architecture decision records
```

## License

Personal use.
