# AGENTS Policy (Token-Controlled LLM Usage)

This project uses LLM capabilities in a tightly scoped way.

## Hard Boundary
LLM is **never** part of the per-transaction runtime reconciliation loop.

Runtime reconciliation must remain deterministic and fully testable in Python.

## Allowed Agents

### 1) `parser-author` (Token use: allowed)
Purpose:
- Generate or patch parser modules for new/changed source export formats.

Inputs:
- New sample file(s)
- Header row/signature details
- Existing canonical schema contract

Required Outputs:
- New parser module (versioned, e.g., `leumi_v2.py`)
- Signature/detector registry update
- Parser tests (detection + schema + edge cases)
- Clear parse error handling (no silent row coercion)

Acceptance Criteria:
- Tests pass
- Canonical schema/dtypes valid
- Raw/original columns preserved

### 2) `format-detector-maintainer` (Token use: allowed)
Purpose:
- Update signature rules and detection logic when source formats evolve.

Inputs:
- Header signature diffs
- Known Hebrew keyword patterns
- Optional first-row pattern examples

Required Outputs:
- Registry/signature update
- Tests proving correct parser selection and non-regression

Acceptance Criteria:
- Deterministic parser selection
- No conflict with existing signatures

### 3) `report-writer` (Token use: optional)
Purpose:
- Generate short, calm narrative text from precomputed aggregates.

Inputs (aggregated only):
- totals, match rates, missing/major counts
- top missing/suspicious lists

Forbidden Input:
- Raw transaction tables
- any direct transaction-by-transaction decisioning

Required Outputs:
- Concise summary + practical tips
- No changes to match classifications or scores

## Forbidden Agent Behavior
- No per-transaction matching decisions by LLM
- No hidden data mutation
- No replacement of deterministic scoring with model inference
- No untested parser changes merged to main workflow

## Token Budget Rules (Practical)
- Default to no-token deterministic execution.
- Trigger token use only when:
  1) format detection fails or confidence is low due to unseen format
  2) parser update is required
  3) final narrative text is requested
- Prefer smallest possible prompt context:
  - header row + 10–30 representative rows (sanitized)
  - canonical schema + one existing parser example
  - specific failing test output

## Safe Change Workflow for New Format
1. Add fixture file under tests fixtures.
2. Run format detection tests.
3. If unknown format, call `parser-author`.
4. Add parser module + detection signature.
5. Add/extend tests for schema + edge cases.
6. Run tests; do not merge if failing.
7. Record parser version change in changelog/release notes.

## Auditability Requirements
Any LLM-assisted parser change must keep:
- source file identity (`source_file_id`)
- row-level traceability (`source_row_id`)
- original/raw fields preservation (`extras`/raw table)
- explicit parse error artifacts

## Decision Authority
- Deterministic Python engine is the source of truth.
- LLM outputs are draft code/text proposals that must pass tests and validation.
