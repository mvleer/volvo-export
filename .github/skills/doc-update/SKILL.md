---
name: doc-update
description: 'Update project documentation after code changes. Use when: pipeline behaviour changes, new output format, new input handling, directory layout changes, dependency changes, new ADR needed. Covers README.md, doc/requirements.md, doc/specs/data-contract.md, doc/ADR/arch-decisions.md.'
argument-hint: 'Describe what changed in the code'
---

# Doc Update — Volvo Trip Log Pipeline

## When to Use

Invoke this skill after any code change that affects observable behaviour.
Type `/doc-update` and describe what changed, or let the agent trigger it automatically.

## Doc Map — What to Update and When

| Change | README | requirements.md | data-contract.md | arch-decisions.md |
|--------|--------|-----------------|------------------|-------------------|
| Output format (e.g. CSV → XLSX) | Yes | FR-5, NFR-2 | Output section | New ADR |
| Output directory | Yes | FR-5 | Output section | New ADR |
| Input delimiter handling | No | FR-3 | Input section | New ADR |
| New/removed columns | Yes (transformations table) | FR-3 | Input & Output tables | — |
| New raw input format | No | FR-1, FR-3 | Input section | New ADR if significant |
| Deduplication key change | No | FR-2 | — | Update ADR-001 |
| Year assignment change | No | FR-4 | Year column section | Update ADR-002 |
| New CLI flag | Yes (usage section) | FR-6 | — | — |
| New/removed dependency | Yes (requirements) | NFR-2 | — | Update ADR-004 |
| Directory restructure | Yes (layout section) | — | — | New ADR |
| New test layer | Yes (layout section) | NFR-1 | — | — |

## Procedure

### 1. Identify what changed

Read the diff or the user's description. Map each change to the rows in the Doc Map above.

### 2. Update README.md

- **Description line** (first paragraph): reflects current output format and purpose.
- **Directory tree**: matches actual workspace layout (`raw/`, `trip-logs/`, etc.).
- **Pipeline description**: accurate delimiter/format/directory details.
- **Transformations table**: reflects current column handling.
- **Requirements section**: lists current runtime dependencies.
- **Project layout**: lists all significant directories and files.

### 3. Update doc/requirements.md

- **FR sections**: update affected functional requirements.
- **NFR sections**: update affected non-functional requirements (especially NFR-2 for dependencies).
- Do not rewrite unaffected requirements.

### 4. Update doc/specs/data-contract.md

- **Input section**: encoding, delimiter, column table, date/numeric formats.
- **Output section**: format, directory, filename pattern, column table, encoding.
- Only update sections touched by the change.

### 5. Update doc/ADR/arch-decisions.md

- **Amend an existing ADR** if the decision was revised (e.g. ADR-004 when dependencies change).
  - Update the **Decision** and **Rationale** paragraphs.
  - Do not change the ADR number or date.
- **Append a new ADR** for new architectural decisions.
  - Number sequentially (ADR-00N).
  - Include: Date, Decision, Rationale, and (if relevant) Trigger to revisit / Consequence.

## ADR Template

```markdown
## ADR-00N — <short title>

**Date:** YYYY-MM

**Decision:** <one-sentence decision statement>

**Rationale:** <why this was the right call; what alternatives were considered>

**Consequence / Trigger to revisit:** <optional>
```

## Conventions

- Docs use present tense, active voice.
- ADR decisions are stated as facts, not proposals.
- README code blocks use `bash` or plain fenced blocks.
- Do not create new doc files — only edit the four listed above.
- Do not add sections to docs that are not already present unless the change clearly warrants it.
