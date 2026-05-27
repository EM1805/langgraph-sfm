# Step 25 — External panel validation harness

Step 25 adds a data-backed validation layer for Structural Final Models (SFM).  The existing synthetic benchmark remains the fast epistemic smoke test; the new panel benchmark checks whether the same claim-authority rules behave correctly on a longitudinal action-event panel.

## What changed

New module:

```python
from amantia.causal_core.final import run_sfm_external_panel_benchmark

report = run_sfm_external_panel_benchmark("data/action_event_panel.csv")
print(report["passed"])
print(report["false_positive_claims"])
```

The module is intentionally conservative.  It does **not** treat panel correlations as proof of final causality.  Instead, it converts a longitudinal operational panel into ordinary `infer_final_cause(...)` payloads and tests whether SFM claim authority changes under required epistemic conditions.

## Cases covered

The panel benchmark currently builds four deterministic cases:

1. `panel_throughput_claim_authorized_with_domain_graph`
   - Uses the panel-derived decision records plus a supplied domain graph.
   - Expected behavior: throughput-oriented final-cause claim is authorized.

2. `panel_missing_graph_withholds_claim_authority`
   - Uses the same panel evidence but removes the real SCM graph.
   - Expected behavior: diagnostic hypothesis may remain supported, but claim authority is withheld.

3. `panel_negative_control_not_promoted_to_final_cause`
   - Tests a negative-control outcome (`audit_noise`).
   - Expected behavior: no authorized terminal final-cause claim.

4. `panel_protected_harm_not_terminal_goal`
   - Tests a protected harm outcome (`user_or_system_harm`).
   - Expected behavior: harm is not promoted to a terminal final cause.

## Why this matters

This hardens SFM for causalità finale in a more realistic direction:

- repeated decisions over time are used as sequence-level evidence;
- real/domain graph authority is required for final-cause claim authorization;
- graph ablation checks prevent high utility or policy consistency from becoming a causal claim;
- negative-control and protected-outcome cases reduce false-positive intent claims.

## Verification

```text
317 passed
```

Panel benchmark result on the bundled development panel:

```text
4 / 4 panel cases passed
false_positive_claims = 0
false_negative_claims = 0
claim_authorization_accuracy = 1.0
```

## Limitations

This is still not a scientific validation study.  The bundled panel is a development fixture, not independent field evidence.  For stronger causal-final evidence, pass a domain-owned longitudinal dataset and a domain-reviewed SCM graph into the same harness.
