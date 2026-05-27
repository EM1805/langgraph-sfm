# SFM Step 20 — Normalized normative policy

Step 20 consolidates the normative/value policy contract.

Before this step, the package supported both compact inline policies:

```json
{
  "allowed_goals": ["task_success"],
  "prohibited_actions": ["unsafe_fast_answer"]
}
```

and richer rules:

```json
{
  "rules": [
    {
      "target": "task_success",
      "target_type": "goal",
      "status": "allowed",
      "severity": 0.8,
      "source": "safety_policy"
    }
  ]
}
```

But those two shapes were not treated as a single internal contract everywhere.
Step 20 introduces a canonical normalizer so both shapes become `NormativeRule`
objects before evaluation.

## New public API

```python
from amantia.causal_core.final import (
    NormalizedNormativePolicy,
    NormativeRule,
    normalize_normative_policy,
    normative_status_for_target,
)

normalized = normalize_normative_policy({
    "allowed_goals": [{"target": "task_success", "severity": 0.7}],
    "rules": [
        {"target": "manipulate_user", "target_type": "goal", "status": "prohibited"}
    ],
})

print(normalized.to_dict()["allowed_goals"])
print(normalized.status_for_target("task_success", "goal"))
```

## What changed

- Inline lists such as `allowed_goals`, `prohibited_goals`, `allowed_actions`, and `prohibited_actions` are now converted into `NormativeRule` rows.
- List items may be strings or rich dictionaries with `target`, `severity`, `reason`, `source`, and `metadata`.
- Explicit `rules`, `action_rules`, `outcome_rules`, and `constraint_rules` use the same normalization path.
- `NormativeSFMAudit` now includes:
  - `normalized_policy`
  - `normalized_rule_count`
  - `goal_rule_severity`
  - `action_rule_severity`
  - `max_applicable_severity`
- `recommendation.py` now consumes the same normalized policy instead of reparsing normative fields independently.

## Why this matters

The normative layer and recommender now share the same semantics. A rich rule like:

```json
{
  "target": "unsafe_fast_answer",
  "target_type": "action",
  "status": "prohibited",
  "severity": 0.9
}
```

will both:

1. appear in `normative_support.applicable_rules`; and
2. block the same action inside `action_recommendation_support.rankings`.

This closes the gap between governance audit and operational recommendation.

## Tests

```text
tests/test_sfm_normative_normalization_step20.py
```
