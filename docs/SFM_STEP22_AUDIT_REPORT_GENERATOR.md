# Step 22 — SFM Audit Report Generator

Step 22 adds a human-readable reporting layer on top of the structured SFM result.
It is intended for safety reviewers, product teams, governance workflows, and incident review.

## New module

```text
amantia/causal_core/final/reporting.py
```

Exports:

- `SFMReportSection`
- `SFMAuditReport`
- `SFMAuditReportGenerator`
- `render_sfm_audit_report(...)`

## What it does

The report generator converts the already-computed SFM evidence into a markdown report with:

- executive summary
- machine verdict
- governance verdict
- intent evidence
- falsification and side-effect checks
- constraints and normative alignment
- robustness and uncertainty
- recommendation
- temporal/context/hierarchy diagnostics when available
- epistemic note

It does **not** create new evidence or upgrade the epistemic status of an SFM claim. It narrates the existing layers.

## New result field

`FinalCauseResult` now includes:

```json
{
  "audit_report": {
    "generated": true,
    "format": "markdown",
    "executive_summary": "...",
    "machine_summary": {...},
    "markdown": "# SFM Audit Report\n..."
  }
}
```

## Execution layer

New layer name:

```text
audit_report
```

Aliases:

```text
report
audit
human_report
```

Example:

```python
from amantia.causal_core.final import infer_final_cause

result = infer_final_cause({
    **payload,
    "execution_profile": "governance"
})
print(result["audit_report"]["markdown"])
```

Or run it standalone on an existing SFM result:

```python
from amantia.causal_core.final import infer_final_cause, render_sfm_audit_report

result = infer_final_cause(payload)
report = render_sfm_audit_report(result)
```

## Why this matters

`alignment_summary` is optimized for machine gates.
`audit_report` is optimized for humans.

Together they form two contracts:

```text
alignment_summary -> allow / block / review / escalate
 audit_report      -> explain the verdict to humans
```
