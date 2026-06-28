# Copilot Instructions — Volvo Trip Log Pipeline

## Project purpose

Single-script Python pipeline that cleans and archives Volvo app trip exports.
Raw CSVs go into `raw/`; the pipeline produces one `volvo-trips-YYYY.xlsx` per year under `volvo-trips/`.

## Key files

| File/Dir | Role |
|---|---|
| `volvo_trips_cleanup.py` | The entire pipeline — one module, no sub-packages |
| `raw/` | Immutable raw exports — never modified by the pipeline |
| `volvo-trips/` | Generated XLSX output — safe to delete and regenerate |
| `tests/` | pytest suite; `conftest.py` holds all synthetic fixtures |
| `.github/skills/doc-update/SKILL.md` | Which docs to update after code changes |
| `doc/requirements.md` | Functional and non-functional requirements |
| `doc/specs/data-contract.md` | Input/output format specification |
| `doc/ADR/arch-decisions.md` | Architecture decision records |

## Pipeline structure

```
read_raw_files()             # reads all CSVs from raw/, auto-detects delimiter
  └─ read_raw_file()         # sniffs delimiter per file, applies clean_row()
       └─ clean_row()        # dates → ISO 8601, distance ÷ 10, units stripped, Year derived
merge_and_dedup()            # dedup key: (Started, Start odometer (km)), sort ascending
split_by_year()              # bucket by year of Stopped date
load_category_overrides()    # reads back non-Unassigned Category values from existing XLSX
write_year_file()            # one .xlsx per year via openpyxl; annotations re-applied
```

## Definition of Done

Every code change to `volvo_trips_cleanup.py` is only complete when **all three** are done:

1. **Tests** — new or changed logic has test coverage in the appropriate test file. Run `pytest tests/` and confirm it passes before finishing.
2. **Docs** — use `/doc-update` to update `README.md`, `doc/requirements.md`, `doc/specs/data-contract.md`, and/or `doc/ADR/arch-decisions.md` as applicable.
3. **Instructions** — if the pipeline structure or a key behavioural rule changed, update the Pipeline structure section above.

Do not consider a task finished if any of these three are outstanding.

## Conventions

Architecture constraints, deduplication rules, and format details are the authoritative sources:
- Architectural decisions → `doc/ADR/arch-decisions.md`
- Functional and non-functional requirements → `doc/requirements.md`
- Input/output format specification → `doc/specs/data-contract.md`

Read the relevant doc before making any change that could affect these areas.

## Docs discipline

After any change that affects behaviour, use the `/doc-update` skill to update:
- `README.md`
- `doc/requirements.md`
- `doc/specs/data-contract.md`
- `doc/ADR/arch-decisions.md`

New architectural decisions get a new ADR (numbered sequentially). Revisions to existing decisions amend the relevant ADR in place.

## Test layout

| File | What it covers |
|---|---|
| `tests/test_raw_inputs.py` | Raw file reading and cleaning |
| `tests/test_merge.py` | Dedup and sort correctness |
| `tests/test_output.py` | Per-year output quality |
| `tests/test_pipeline_e2e.py` | Full end-to-end (marked `slow`) |

Run: `pytest tests/` — e2e tests excluded by default. Run with `-m slow` to include them.
