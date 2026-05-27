# Step 21 — Uncertainty-aware / robust SFM

Step 21 adds a conservative robustness layer for SFM diagnostics.

The new module is:

```text
amantia/causal_core/final/robustness.py
```

It exposes:

- `RobustSFMEvaluator`
- `RobustSFMAudit`
- `RobustnessScenario`
- `evaluate_sfm_robustness(...)`

## Purpose

A high SFM intent score can still be fragile when the evidence is uncertain. Step 21 stress-tests a candidate final-cause claim under:

- candidate-action uncertainty fields such as `uncertainty`, `causal_uncertainty`, `outcome_uncertainty`, `standard_error`, `ci`, or `confidence_interval`;
- evidence-quality labels such as `high`, `medium`, `low`, `weak`;
- weak recommendation top margins;
- weak identifiability authority;
- hard blocks from falsification, constraints, and normative policy.

The layer does **not** claim to be a formal sensitivity analysis. It is a governance-oriented robustness audit.

## Output

`infer_final_cause(...)` now includes:

```json
{
  "robustness_support": {
    "assessed": true,
    "robustness_status": "robust_supported",
    "robust_to_uncertainty": true,
    "uncertainty_review_required": false,
    "baseline_intent_score": 1.0,
    "pessimistic_intent_score": 0.97,
    "total_uncertainty_penalty": 0.03
  }
}
```

The compact API also exposes:

```json
{
  "robustness_status": "robust_supported",
  "robust_to_uncertainty": true
}
```

## Main statuses

- `robust_supported`
- `supported_but_uncertain`
- `fragile_support`
- `not_robust`
- `not_robust_due_to_hard_blocks`
- `not_applicable_intent_not_supported`

## Alignment summary integration

`SFMAlignmentSummary` now includes:

- `robustness_status`
- `robust_to_uncertainty`
- `uncertainty_review_required`
- `pessimistic_intent_score`

If explicit high uncertainty or fragile pessimistic support is detected, the governance verdict becomes:

```text
supported_but_uncertain
```

and the gate status becomes:

```text
review
```

This prevents Amantia from treating a high point estimate as deployment-ready when the claim collapses under conservative uncertainty penalties.

## Execution profile

Step 21 adds a new layer name:

```text
robustness
```

with aliases:

```text
robust
uncertainty
uncertainty_aware
sensitivity
```

It is included in the main profiles: `full`, `fast`, `minimal`, `governance`, `discovery`, and `recommendation`.

## Tests

```text
tests/test_sfm_robustness_step21.py
```
