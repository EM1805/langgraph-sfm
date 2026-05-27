# Step 18 — SFM Alignment Summary

Step 18 adds a governance-facing contract over the diagnostic SFM stack.

The SFM stack still keeps every layer separate: twin policy, belief graph,
falsification, utility, empirical utility, multi-goal, do*, identifiability,
goal discovery, policy learning, temporal drift, context conditioning,
hierarchical goals, constraints, normative alignment, and action recommendation.

`SFMAlignmentSummary` folds those diagnostics into one compact verdict for
external gates:

```text
intent evidence
+ falsification
+ constraints
+ normative policy
+ identifiability authority
+ action recommendation
-> verdict + gate_status + reason codes
```

Main fields:

- `verdict`: `aligned_supported`, `diagnostic_only`, `plausible_but_unidentified`, `supported_but_prohibited`, `supported_but_constraint_blocked`, `requires_escalation`, `falsification_failed`, `unsupported`, `insufficient_evidence`.
- `gate_status`: `allow`, `review`, `block`, `escalate`, `observe`.
- `confidence_level`: `high`, `moderate`, `low`, `none`.
- `blocking_reasons`: operational reasons that should stop execution.
- `warnings`: non-blocking limitations and uncertainty notes.

APIs:

```python
from amantia.causal_core.final import infer_final_cause, infer_final_cause_compact

full = infer_final_cause(payload)
summary = full["alignment_summary"]

compact = infer_final_cause_compact(payload)
summary = compact["alignment_summary"]
```

Design rule:

> A goal can be teleologically plausible and still prohibited, constraint-blocked,
> escalation-required, or only diagnostically supported.

This keeps epistemic inference separate from governance authorization.
