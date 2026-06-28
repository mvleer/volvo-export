# Requirements — Volvo Trip Log Pipeline

> Format details live in [specs/data-contract.md](specs/data-contract.md).
> Architecture decisions live in [ADR/arch-decisions.md](ADR/arch-decisions.md).

## Context

The Volvo app allows trip data to be exported as CSV, but the export window is
limited — older data cannot be re-downloaded. This pipeline preserves every
export as-is and produces clean, stable, per-year archives for analysis.

---

## FR-1 — Raw export archiving

**FR-1.1** Raw exports are stored unchanged. The pipeline must never modify
a raw file.

**FR-1.2** Multiple exports may cover overlapping date ranges. The system must
handle this without requiring the user to manually de-overlap files before
running.

---

## FR-2 — Merge and deduplication

**FR-2.1** All raw exports are combined into a single dataset on each pipeline
run.

**FR-2.2** Each trip must appear exactly once in the output, regardless of how
many raw exports contain it.

**FR-2.3** The merged dataset must be sorted in ascending chronological order.

---

## FR-3 — Data cleaning

**FR-3.1** Date/time fields must be standardised to ISO 8601 so that output
files sort and compare correctly across tools.

**FR-3.2** Distance values must be corrected to proper kilometres where needed.
The legacy app format stores distance as integer tenths-of-km (÷10 required); the
updated app format stores distance as decimal km already. The pipeline detects
which format applies per value.

**FR-3.3** Unit suffixes must be removed from numeric values; units belong in
column headers only.

**FR-3.4** Numeric output columns (`Distance (km)`, `Fuel consumption (l)`) must
be stored as native floating-point numbers in the XLSX output. Unit suffixes and
decimal notation differences in the source are normalised during cleaning.

**FR-3.5** Columns that carry no analytical value must be dropped from the
output.

---

## FR-7 — Category annotation persistence

**FR-7.1** A trip's `Category` field may be manually assigned by the user
directly in the generated XLSX file.

**FR-7.2** On re-run, the pipeline must preserve any `Category` value that
differs from `Unassigned`, identified by the deduplication key
`(Started, Start odometer (km))`. Newly added trips default to `Unassigned`.

---

## FR-4 — Year column

**FR-4.1** Every output row must include a `Year` field indicating the year
and month the trip ended, for use in time-based filtering and grouping.

---

## FR-5 — Per-year output

**FR-5.1** The pipeline must produce one output file per calendar year present
in the data. Output files are written to the `volvo-trips/` directory as
`volvo-trips-YYYY.xlsx`.

**FR-5.2** Once a year is complete (no further exports can add data to it),
its output file is considered frozen. Re-running the pipeline must not corrupt
a frozen year file.

**FR-5.3** Re-running the pipeline with the same inputs must always produce
identical output (idempotent).

---

## FR-6 — CLI

**FR-6.1** The pipeline must be runnable from the command line with no
arguments, using default input and output directories.

**FR-6.2** Input and output directories must be overridable via CLI flags to
support testing and alternative setups.

---

## NFR-1 — Testability

**NFR-1.1** All pipeline logic must be importable and independently testable
without file system side effects.

**NFR-1.2** The test suite must cover: raw input integrity, merge/dedup
correctness, per-year output quality, and full end-to-end execution.

**NFR-1.3** Tests must not depend on real export files — they must be
reproducible in any environment.

---

## NFR-2 — Runtime environment

**NFR-2.1** The pipeline must run on Python 3.9 or higher.

**NFR-2.2** Runtime dependencies must be minimal. Only `openpyxl` is permitted
as a third-party runtime dependency (required for XLSX output).

**NFR-2.3** `pytest` is the only additional external dependency, scoped to the
test suite.
