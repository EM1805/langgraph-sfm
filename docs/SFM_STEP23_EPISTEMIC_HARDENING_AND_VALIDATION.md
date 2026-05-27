# Step 23 — Epistemic hardening and synthetic validation

Step 23 fixes the main overclaim risk in the SFM prototype.

## What changed

`FinalCauseResult` now separates three different decisions:

- `intent_hypothesis_supported`: the diagnostic evidence passes the configured score/falsification/side-effect constraints.
- `intent_claim_authorized`: the identifiability layer authorizes reporting the hypothesis as an SFM intent claim.
- `governance_execution_allowed`: the alignment summary allows operational execution.

`inferred` is now aligned with `intent_claim_authorized`, not merely with a high diagnostic score.

## Missing SCM graph behavior

A payload with strong action-outcome scores but no real `scm_graph` can still return:

```json
{
  "intent_hypothesis_supported": true,
  "intent_claim_authorized": false,
  "inferred": false,
  "alignment_summary": {
    "verdict": "plausible_but_unidentified",
    "gate_status": "review"
  }
}
```

This avoids treating heuristic action ranking as causal-intent identification.

## Stricter identifiability

Partial SFM identification now requires:

- real SCM graph supplied;
- non-zero action-goal effect identified;
- candidate action alternatives;
- twin-policy comparison selects the observed action with the goal;
- action changes when the goal is removed;
- side effects/protected outcomes excluded;
- falsification passes;
- at least one independent validation channel:
  - negative-control/placebo/side-effect controls,
  - agent belief graph supporting intent,
  - empirical outcome history.

Falsifiable diagnostics remain useful, but by themselves do not authorize a claim.

## Normative evidence no longer erases intent evidence

A prohibited goal can still be the goal pursued. Normative policy blocks governance execution, but does not erase the underlying intent evidence.

## Synthetic validation benchmark

New module:

```python
from amantia.causal_core.final import run_sfm_validation_benchmark

report = run_sfm_validation_benchmark()
print(report["passed"])
print(report["claim_authorization_accuracy"])
```

The built-in benchmark covers:

- true positive with real SCM graph, controls, and belief graph;
- high-score case with missing real SCM graph;
- side-effect/protected outcome not promoted to final cause;
- false-positive agent belief vs real zero-effect graph;
- prohibited intent blocked by governance.

The benchmark is deterministic and intended as a CI smoke test, not a scientific validation study.
