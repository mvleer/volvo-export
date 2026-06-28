# Data Contract — Volvo Trip Log Pipeline

## App export format versions

The Volvo app has two distinct export formats. The pipeline handles both transparently;
format is detected per file, not assumed globally.

| Characteristic | Legacy app format | Updated app format |
|---|---|---|
| Delimiter | `;` (semicolon) | `,` (comma) |
| Date format | `DD/MM/YYYY HH:MM` | `YYYY-MM-DD HH:MM` (ISO 8601) |
| Distance unit | Integer tenths-of-km (e.g. `378` = 37.8 km) | Decimal km (e.g. `5.5` = 5.5 km) |
| Distance suffix | Sometimes ` km` (e.g. `125,3 km`) | None |
| Fuel suffix | ` l` (e.g. `0,2 l`) | None (e.g. `0.2`) |
| Decimal separator | Comma (`,`) | Period (`.`) |

Detection is automatic: delimiter via `csv.Sniffer`; distance scaling via presence of a
unit suffix or absence of a decimal point in the value.

---

## Input: Volvo app CSV export

### Encoding & structure
- UTF-8 (with or without BOM)
- Delimiter: auto-detected per file — `;` (legacy app format) or `,` (updated app format)
- First row is the header

### Date/time fields
- Columns: `Started`, `Stopped`
- **Legacy app format**: `DD/MM/YYYY HH:MM`
- **Updated app format**: ISO 8601 `YYYY-MM-DD HH:MM`
- Both formats are handled transparently by the pipeline

### Numeric fields
- Decimal separator: comma (`,`) or period (`.`) — both accepted
- Example: `125,3` or `125.3`

### Distance
- Column: `Distance (km)`
- **Legacy app format**: integer tenths-of-km, no suffix (e.g. `378` → 37.8 km). Divided by 10.
- **Updated app format**: decimal km, no suffix (e.g. `5.5` → 5.5 km). Used as-is.
- Some legacy exports may include a ` km` suffix with EU decimal (e.g. `125,3 km`); these are also divided by 10.
- Detection rule: ÷10 applied when value had a unit suffix **or** is a pure integer (no decimal point).

### Fuel consumption
- Column: `Fuel consumption (litres)`
- Values carry a ` l` suffix (legacy app format) or no suffix (updated app format)
- Decimal separator may be comma or period — both handled
- Example: `0,2 l` or `0.2`

### Columns present in raw export

| Column | Kept |
|--------|------|
| Category | Yes |
| Started | Yes |
| Start odometer (km) | Yes |
| Start address | Yes |
| Stopped | Yes |
| End odometer (km) | Yes |
| End address | Yes |
| Duration | Yes |
| Distance (km) | Yes |
| Fuel consumption (litres) | Yes (renamed) |
| Title | No — discarded |
| User Notes | No — discarded |
| Column1 | No — discarded |

---

## Output: per-year XLSX workbook

### Format & location
- Excel workbook (`.xlsx`), one sheet per file named after the year
- Output directory: `volvo-trips/`
- One file per calendar year: `volvo-trips/volvo-trips-YYYY.xlsx`

### Date/time fields
- Format: ISO 8601 `YYYY-MM-DD HH:MM`
- Example: `2026-01-31 14:30`

### Numeric fields
- `Distance (km)` and `Fuel consumption (l)` are stored as native floating-point numbers
- `Start odometer (km)` and `End odometer (km)` are stored as native integers
- No unit suffixes in values; units appear in column headers only
- Excel applies locale-appropriate decimal formatting automatically

### Canonical column order

| # | Column | Notes |
|---|--------|-------|
| 1 | Category | Unchanged from input |
| 2 | Started | Converted to ISO 8601 |
| 3 | Start odometer (km) | Stored as integer |
| 4 | Start address | Unchanged |
| 5 | Stopped | Converted to ISO 8601 |
| 6 | End odometer (km) | Stored as integer |
| 7 | End address | Unchanged |
| 8 | Duration | Unchanged |
| 9 | Distance (km) | Value ÷ 10, suffix removed, stored as float |
| 10 | Fuel consumption (l) | Suffix removed, column renamed, stored as float |
| 11 | Year | Derived — format `YYYY-M`, no leading zero on month |
| 12 | l/100km | Derived — `Fuel consumption (l) / Odo delta (km) × 100`, rounded to 1 decimal; uses odometer delta as denominator (more reliable than the distance field); empty if odo delta is zero |
| 13 | Odo delta (km) | Derived — `End odometer − Start odometer`; integer km; cross-reference for detecting distance field anomalies in raw exports |

### Year column
- Derived from `Stopped` date
- Format: `YYYY-M` (numeric month, no leading zero)
- Example: `2026-2` for February 2026

### Category field
- Column: `Category`
- Default value from raw export: `Unassigned`
- May be manually overridden in the generated XLSX
- The pipeline preserves any non-`Unassigned` value on re-run, matched by dedup key `(Started, Start odometer (km))`

### Year file assignment
- A trip is assigned to the year of its `Stopped` date
- A trip that starts on Dec 31 and stops on Jan 1 belongs to the new year
