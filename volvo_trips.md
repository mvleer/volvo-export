# Volvo Trips — User Guide

## What this tool does

The Volvo app lets you export your trip history as a CSV file, but only for a limited time window — older trips cannot be re-exported later. This tool takes those exports, cleans the data, removes duplicates, and produces one tidy Excel workbook per calendar year in `volvo-trips/`.

You can drop in a new export at any time and re-run. Only years whose source file has changed are regenerated; the others are left untouched.

---

## Quick start

**1. Install Python (3.9 or later) and the one required package:**

```bash
pip install openpyxl
```

**2. Drop your Volvo export into `raw/`:**

```
raw/
  volvo-export-2025.csv
```

**3. Run the tool:**

```bash
python volvo_trips_cleanup.py
```

**4. Open the result:**

```
volvo-trips/
  volvo-trips-2025.xlsx
```

That's it. Each subsequent run checks whether the source file has changed and skips years that are already up to date.

---

## Getting your data out of the Volvo app

1. Open the Volvo Cars app → **Trip statistics**
2. Tap the export icon and choose a date range
3. Save the `.csv` file to your computer
4. Copy it into the `raw/` folder next to this tool

The tool handles both the older app format (semicolon-separated, `DD/MM/YYYY` dates) and the current format (comma-separated, ISO dates) — no manual conversion needed.

---

## The `raw/` folder

`raw/` is the archive of your original Volvo exports. The tool **never modifies** these files.

**Naming convention** — use one file per calendar year so the tool can detect changes efficiently:

```
raw/volvo-export-2024.csv
raw/volvo-export-2025.csv
raw/volvo-export-2026.csv
```

If an export spans more than one year (e.g. Oct 2024 – Nov 2025), the tool splits it into the correct year workbooks automatically during processing. You can keep the file as-is; no manual splitting is needed.

**Overlapping exports are safe.** If two exports contain the same trip (same start time and start odometer reading), the duplicate is silently removed. You will never end up with the same trip counted twice.

---

## The `volvo-trips/` folder

This folder contains the generated Excel workbooks — one per calendar year:

```
volvo-trips/
  volvo-trips-2024.xlsx
  volvo-trips-2025.xlsx
  volvo-trips-2026.xlsx
```

Each workbook has a single sheet called **trips** with the following columns:

| Column | Description |
|---|---|
| Category | Unassigned by default; you can fill this in manually — it is preserved across re-runs |
| Started | Trip start time (ISO format: `YYYY-MM-DD HH:MM`) |
| Start odometer (km) | Odometer reading at departure |
| Start address | Address at departure |
| Stopped | Trip end time |
| End odometer (km) | Odometer reading at arrival |
| End address | Address at arrival |
| Duration | Trip duration (as reported by the app) |
| Distance (km) | Distance in km (decimal, unit suffix removed) |
| Fuel consumption (l) | Fuel used in litres (decimal) |
| Year | Year and month of the Stopped date, e.g. `2025-3` |
| l/100km | Fuel efficiency, calculated as Fuel ÷ Odo delta × 100 |
| Odo delta (km) | End odometer − Start odometer (ground-truth distance) |

> **Why two distance columns?**
> The Volvo app's Distance field has known inaccuracies in older export formats (up to ~11% short). `Odo delta (km)` is derived from the odometer readings, which are reliable, so `l/100km` is calculated using that column rather than Distance.

> **Before deleting these files:** any Category values you have assigned are stored inside them. Deleting a workbook permanently removes those annotations — they cannot be recovered on the next run. If you only want to force a rebuild, use `--force` instead of deleting.

---

## Annotating trips with categories

The **Category** column starts as `Unassigned` for every trip. You can fill it in directly in Excel to tag trips (e.g. `Business`, `Holiday`, `Commute`).

**Your annotations survive re-runs.** When the tool regenerates a year's workbook, it reads back any non-`Unassigned` Category values from the existing file before overwriting it, and re-applies them to the new output.

Workflow:
1. Open `volvo-trips-2025.xlsx`
2. Set the Category for trips you want to tag
3. Save and close the file
4. Run the tool again — your categories are preserved

> **Important:** close the Excel file before running the tool, otherwise the file is locked and the tool cannot update it.

---

## Command-line options

```
python volvo_trips_cleanup.py [--raw-dir DIR] [--output-dir DIR] [--force]
```

| Option | Default | Description |
|---|---|---|
| `--raw-dir` | `raw/` | Folder containing the Volvo CSV exports |
| `--output-dir` | `volvo-trips/` | Folder where the Excel workbooks are written |
| `--force` | off | Regenerate all year files even if they are already up to date |

### Examples

**Run with default folders:**
```bash
python volvo_trips_cleanup.py
```

**Use a different raw folder (e.g. exports on a shared drive):**
```bash
python volvo_trips_cleanup.py --raw-dir /Volumes/Shared/volvo-exports
```

**Force a full rebuild after manually editing a raw file:**
```bash
python volvo_trips_cleanup.py --force
```

**Write output to a different location:**
```bash
python volvo_trips_cleanup.py --output-dir ~/Documents/volvo
```

---

## What the tool protects you from

| Risk | Protection |
|---|---|
| Duplicate trips from overlapping exports | Deduplicated on (start time + start odometer) — each trip appears once |
| Categories lost when re-running | Non-Unassigned Category values are read back from the existing XLSX before overwriting |
| Unnecessary overwrites | Years whose XLSX is newer than the raw file are skipped |
| Accidental modification of raw exports | `raw/` is read-only — the tool never writes to it |
| Mixed export formats in the same folder | Delimiter and date format are auto-detected per file |

---

## Troubleshooting

**"No CSV files found in raw/"**
The `raw/` folder is empty or does not exist. Add your Volvo export CSV to it.

**All years show "Skipped (up to date)"**
The XLSX files are newer than the raw files. If you have genuinely updated a raw file, use `--force` to rebuild.

**Category annotations are gone after a re-run**
The Excel file was open in Excel when the tool ran. Close it first, then re-run with `--force`.

**The XLSX looks correct but a category did not come back**
The start time or odometer reading in the raw file differs from what was in the old XLSX. This can happen if you manually edited the raw CSV. Run `--force` and re-enter the category.
