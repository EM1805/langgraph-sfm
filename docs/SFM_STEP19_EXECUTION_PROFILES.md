# SFM Step 19 — Execution profiles and enabled layers

Step 19 keeps the full SFM diagnostic stack, but makes execution explicit and selectable.

Before this step, `infer_final_cause(...)` always composed every available layer. That preserved power, but pushed the entry point toward a God Function. Step 19 adds a small execution contract:

```python
from amantia.causal_core.final import infer_final_cause

result = infer_final_cause({
    "execution_profile": "fast",
    "observed_action": "safe_answer",
    "candidate_goals": ["task_success"],
    "candidate_actions": [...],
    "scm_graph": {...},
})
```

The resolved plan is returned in every result:

```python
result["execution_profile_support"]
```

## Profiles

- `full`: preserves the pre-step19 behavior; all layers enabled.
- `fast`: low-latency intent screening; disables heavier governance, temporal and utility-bundle layers.
- `minimal`: SCM-ID + counterfactual + twin + identifiability + summary.
- `governance`: value/safety oriented stack: falsification, constraints, norms, recommendation and summary.
- `discovery`: historical/inverse-goal stack: goal discovery, empirical utility, policy learning, temporal/context.
- `recommendation`: forward action recommendation under goals, constraints and norms.

## Explicit overrides

Profiles can be narrowed or adjusted:

```python
payload = {
    "execution_profile": "full",
    "enabled_layers": ["identification", "counterfactual", "twin", "identifiability"],
}
```

`enabled_layers` narrows execution to the selected layers. `alignment_summary` is kept by default unless explicitly disabled, because it is the external governance contract.

```python
payload = {
    "execution_profile": "governance",
    "disabled_layers": ["normative", "alignment_summary"],
}
```

Disabled layers return a structured disabled report rather than disappearing:

```json
{
  "assessed": false,
  "evaluated": false,
  "compared": false,
  "disabled": true,
  "layer": "normative",
  "reason_codes": ["SFM_LAYER_DISABLED_NORMATIVE"]
}
```

## Public helper

```python
from amantia.causal_core.final import resolve_sfm_execution_plan

plan = resolve_sfm_execution_plan({"execution_profile": "fast"})
```

This lets a caller inspect the plan before running inference.

## Why this matters

Step 19 reduces call overhead and clarifies intent:

- product gates can use `governance`;
- latency-sensitive calls can use `fast`;
- research/debugging can use `full`;
- inverse-goal analysis can use `discovery`;
- action selection can use `recommendation`.

The default remains `full`, so existing behavior is preserved.
