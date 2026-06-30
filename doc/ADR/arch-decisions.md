# Architecture Decision Records

---

## ADR-001 — Deduplication key

**Date:** 2026-06

**Decision:** Trips are deduplicated using the composite key
`(Started, Start odometer (km))`.

**Rationale:** No single field uniquely identifies a trip in the Volvo export.
`Started` alone is not unique (two short trips could start at the same minute).
The odometer reading at departure is stable and, combined with the start
timestamp, produces a key that is practically unique. Trip content fields
(distance, fuel) are intentionally excluded from the key so that a corrected
re-export of the same trip still deduplicates correctly.

**Consequence:** Two trips that genuinely start at the same time from the same
odometer reading would collapse to one. This is considered an acceptable edge
case — it is physically impossible for the same car to make two different trips
simultaneously.

---

## ADR-002 — Year assignment based on Stopped date

**Date:** 2026-06

**Decision:** A trip is assigned to the calendar year of its `Stopped`
(end) date, not its `Started` (begin) date.

**Rationale:** A trip that starts on Dec 31 and ends on Jan 1 should be
counted in the new year's totals because it completed in that year. Using
`Stopped` also makes the `Year` column trivially derivable from the same
field without ambiguity.

---

## ADR-003 — No hexagonal / ports-and-adapters architecture

**Date:** 2026-06

**Decision:** The pipeline is a single-module script without formal port/adapter
abstractions.

**Rationale:** There is currently one input format (Volvo CSV) and one output
format (XLSX workbook). The main benefit of hexagonal architecture — swapping
adapters without touching core logic — is achieved here through simpler means:
all I/O paths are injectable as `Path` arguments (`raw_dir`, `output_dir`),
which is sufficient for full test isolation. Introducing abstract base classes
and adapter layers would double the code size with no functional benefit at the
current scale.

**Trigger to revisit:** If a second input source (e.g. a Volvo API) or a second
output target (e.g. a database or spreadsheet service) is added, this decision
should be reconsidered.

---

## ADR-004 — Standard library only (no third-party runtime dependencies)

**Date:** 2026-06

**Decision:** The pipeline runtime uses the Python standard library
(`csv`, `re`, `datetime`, `pathlib`, `argparse`) plus `openpyxl` for XLSX
output. `pytest` is the only additional external dependency, scoped to testing
only.

**Rationale:** `openpyxl` is the de-facto standard for writing `.xlsx` files
in Python, has no transitive dependencies, and is widely pre-installed.
The previous constraint of zero runtime dependencies is relaxed to allow
`openpyxl` because the output format moved from CSV to XLSX (see ADR-006).
All other logic remains standard-library only.

---

## ADR-005 — Per-year output files instead of a single combined file

**Date:** 2026-06

**Decision:** The pipeline produces one `volvo-trips-YYYY.xlsx` file per year
under the `volvo-trips/` directory, not a single combined output file.

**Rationale:** A year is the natural unit of analysis — annual totals and
year-over-year comparisons are the primary use case. A per-year file is a
self-contained, named artifact (`volvo-trips-2024.xlsx`) that is unambiguous to
share, open in Excel, and reason about without filtering. The pipeline is fully
idempotent and raw files are always preserved, so durability is not a
concern — the split is purely about usability of the output.
---

## ADR-006 — XLSX output format instead of CSV

**Date:** 2026-06

**Decision:** Output files are written as Excel workbooks (`.xlsx`) using
`openpyxl`, replacing the previous semicolon-delimited CSV output.

**Rationale:** The primary consumer of these files is Excel. A native `.xlsx`
file opens without any import dialogs, delimiter guessing, or encoding issues.
The cost is one lightweight runtime dependency (`openpyxl`); the benefit is
zero friction for the end user. CSV is still used internally as the raw input
format because that is what the Volvo app exports.

---

## ADR-007 — Auto-detection of input delimiter via csv.Sniffer

**Date:** 2026-06

**Decision:** The delimiter of each raw input file is detected automatically
using `csv.Sniffer` rather than being hardcoded to `;`.

**Rationale:** The Volvo app changed its export format between 2025 and 2026,
switching from semicolon-delimited to comma-delimited CSV. Hardcoding the
delimiter would require a code change each time the export format drifts.
`csv.Sniffer` inspects the first 4 KB of each file independently, so mixed
batches (some `;`, some `,`) are handled transparently without user
intervention.

---

## ADR-008 — Dedicated `volvo-trips/` output directory

**Date:** 2026-06

**Decision:** Generated per-year files are written to `volvo-trips/` rather than
the workspace root.

**Rationale:** Placing output files in the root directory mixed generated
artifacts with source files (`volvo_trips.py`, `pytest.ini`, etc.),
making the workspace harder to navigate. A dedicated `volvo-trips/` directory
makes the distinction between source, raw data, and output explicit. The
directory is created automatically by the pipeline if it does not exist.

---

## ADR-009 — Category annotation round-trip via existing XLSX

**Date:** 2026-06

**Decision:** Manual `Category` values are preserved across pipeline re-runs by
reading them back from the existing output XLSX before overwriting it.
Any row whose `Category` differs from `Unassigned` is recorded in a dict keyed
by the dedup key `(Started, Start odometer (km))` and re-applied to the freshly
generated rows.

**Rationale:** Users assign driver names (or other categories) directly in the
generated XLSX — the natural place to do so since the full trip context is
visible there. A separate annotation sidecar file would require users to edit
two files and keep them in sync. The round-trip approach keeps the workflow to
one file: annotate in Excel, re-run the pipeline, annotations survive.

**Consequence:** Only non-`Unassigned` values are preserved. If a user resets a
Category back to `Unassigned`, that change is also preserved (the row is simply
not in the override dict, so it stays `Unassigned` from the raw data).

---

## ADR-010 — Numeric columns stored as floats, not formatted strings

**Date:** 2026-06

**Decision:** `Distance (km)`, `Fuel consumption (l)`, `Start odometer (km)`, and
`End odometer (km)` are written to XLSX as native numeric types (float or integer)
rather than locale-formatted strings.

**Rationale:** The previous approach stored these values as EU comma-decimal
strings (e.g. `"12,53"`). Excel flagged every cell with a "Number Stored as
Text" warning, making the output noisy and preventing arithmetic without manual
conversion. XLSX is a typed format — numeric cells should carry numeric values.
Excel then applies the user's locale for display (comma or period) automatically,
so EU users see `12,53` and US users see `12.53` without any data difference.
The EU-notation requirement was a workaround for CSV's lack of type metadata;
it does not apply to XLSX.