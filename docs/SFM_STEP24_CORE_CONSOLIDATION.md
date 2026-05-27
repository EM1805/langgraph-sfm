# Step 24 — Core consolidation and negative validation matrix

Step 24 consolidates the SFM stack instead of adding a new teleological layer.
It addresses three engineering risks that appeared after Step 23:

1. `infer_final_cause(...)` was becoming a God-function.
2. Protected outcomes, constraints and normative rules had overlapping but separate semantics.
3. The synthetic benchmark needed more negative cases to guard against false positive intent claims.

## Added modules

- `layer_protocol.py`
  - `SFMLayerResult`
  - `SFMLayerEvaluator`
  - `layer_result_to_dict(...)`

- `runner.py`
  - `SFMExecutionRunner`
  - centralizes enabled/disabled layer execution and disabled reports.

- `protection.py`
  - `SFMProtectionSpec`
  - `SFMProtectionPolicy`
  - `normalize_protection_policy(...)`

## Protection policy normalization

The new protection contract unifies evidence from:

- `FinalCauseQuery.protected_outcome`
- `GoalSpec.protected_outcomes`
- `GoalSpec.side_effect_outcomes`
- `constraint_model.hard_constraints`
- `constraint_model.soft_constraints`
- `constraint_model.side_effects`
- `normative_policy.protected_outcomes`
- rich `NormativeRule` entries with `protected`, `prohibited`, `discouraged`, or `escalation_required` status.

`ConstraintAwareAudit` now exposes:

```json
{
  "normalized_protection_policy": {
    "protected_outcomes": [...],
    "hard_constraints": [...],
    "side_effect_outcomes": [...],
    "prohibited_goals": [...],
    "prohibited_actions": [...]
  }
}
```

`FinalCauseEngine` uses this normalized protection view when deciding whether a candidate goal overlaps a protected outcome, hard constraint, or side effect.

## Expanded validation matrix

The built-in benchmark is now `synthetic_sfm_epistemic_safety_v2` and includes nine deterministic cases.

New negative cases include:

- `belief_graph_supports_goal_but_real_graph_zero_effect_with_controls`
- `utility_high_without_scm_claim_withheld`
- `protected_outcome_candidate_not_terminal_goal`
- `goal_discovery_avoids_protected_outcome`

These cases guard against confusing:

```text
belief support / utility support / goal discovery
```

with:

```text
authorized SFM claim under real SCM support
```

## Compatibility

No public API was removed. Existing calls to:

```python
infer_final_cause(payload)
infer_final_cause_compact(payload)
run_sfm_validation_benchmark()
```

continue to work.

## Verification

```text
313 passed
```
