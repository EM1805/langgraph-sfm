# SFM cleanup manifest

## Tenuto

- SCM/ID/do-calculus/counterfactual core: `scm_parts/`
- Online causal adapters: `amantia/causal_core/`
- Nuovo scaffold SFM: `amantia/causal_core/final/`
- Action/outcome contracts: `amantia/contracts/`
- Decision/operational loop: `amantia/gate/`, `amantia/operational_brain/`
- Learning/outcome tracking: `amantia/learning/`
- Risk/action recommendation: `amantia/risk_policy/`, `amantia/action_recommender/`
- Estimation diagnostics: `estimation_parts/`
- Runtime compatibility needed by DecisionGate: `runtime/`, `path_parts/`, root YAML/JSONL config
- Focused examples and tests only

## Rimosso

- `.github/`, Docker/HuggingFace deployment files
- `amantia/agent/`, `agent_guard/`, `llm_interface/`, `mcp/`, `integrations/`, `scientific/`
- `pcmci_discovery_parts/`, `offline/`
- Long step-by-step package check docs and generated caches
- `__pycache__/`, `.pytest_cache/`, `.pyc`
- Broad non-SFM tests, demos and input fixtures

## Nota importante

`amantia/causal_core/final/` è uno scaffold conservativo: compone IdentificationEngine e CounterfactualEngine e produce un `do*` audit string. Non è ancora una prova formale di causalità finale.


## Step 4 additions

- `amantia/causal_core/final/falsification.py`
- `tests/test_sfm_falsification_step4.py`
- `examples/inputs/sample_sfm_falsification_query.json`
- `SFM_STEP4_FALSIFICATION.md`

## Step 7 additions

- `amantia/causal_core/final/multi_goal.py` — multi-goal / multi-objective SFM diagnostic layer.
- `tests/test_sfm_multi_goal_step7.py` — regression tests for weighted goal bundles and integration in `infer_final_cause`.
- `examples/inputs/sample_multi_goal_query.json` — sample query where a balanced action is selected by a goal bundle.
- `SFM_STEP7_MULTI_GOAL.md` — implementation notes for Step 7.



## Step 10 addition

Added goal discovery for SFM development:

- `amantia/causal_core/final/goal_discovery.py`
- `tests/test_sfm_goal_discovery_step10.py`
- `examples/inputs/sample_goal_discovery_query.json`
- `SFM_STEP10_GOAL_DISCOVERY.md`

This layer proposes candidate final causes when `candidate_goals` are absent, while preserving explicitly supplied goals.

## Step 12 addition

Added temporal SFM / goal drift detection:

- `amantia/causal_core/final/temporal.py` — temporal windows over decision sequences and goal drift diagnostics.
- `tests/test_sfm_temporal_drift_step12.py`
- `examples/inputs/sample_temporal_goal_drift_query.json`
- `SFM_STEP12_TEMPORAL_GOAL_DRIFT.md`

`FinalCauseResult` now exposes `temporal_goal_drift_support`, allowing `infer_final_cause(...)` to report stable, weak/unstable, or drifted goal patterns over time.

## Step 15 addition

Added constraint-aware SFM diagnostics:

- `amantia/causal_core/final/constraint.py` — separates final goals from hard constraints, soft constraints, protected outcomes, and side effects.
- `tests/test_sfm_constraint_step15.py`
- `examples/inputs/sample_constraint_aware_query.json`
- `SFM_STEP15_CONSTRAINT_AWARE.md`

`FinalCauseResult` now exposes `constraint_support`, and `infer_final_cause(...)` caps final-cause claims when the candidate goal overlaps with a hard/protected constraint or monitored side effect.

## Step 16 update

Added normative / value-alignment SFM diagnostics:

- `amantia/causal_core/final/normative.py`
- `FinalCauseQuery.normative_policy`
- `FinalCauseResult.normative_support`
- `evaluate_normative_sfm(...)`
- `tests/test_sfm_normative_step16.py`
- `examples/inputs/sample_normative_sfm_query.json`
- `SFM_STEP16_NORMATIVE_ALIGNMENT.md`

The layer classifies pursued goals/actions as allowed, prohibited, required, protected, monitored, escalation-required, unclassified, or outside an allowlist. It is diagnostic: it reports value-alignment status without hiding evidence that a prohibited goal may have been pursued.
