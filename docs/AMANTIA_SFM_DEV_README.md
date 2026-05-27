# Amantia SFM Dev — compact package

This is a compact development package for building **Structural Final Models (SFM)** on top of Amantia's existing causal infrastructure.

It keeps the causal power and removes packaging noise: bytecode/cache files were removed, the long per-step docs were consolidated into `docs/SFM_DEVELOPMENT_HISTORY.md`, and Step 18 adds a compact governance contract, Step 19 adds execution profiles so callers can run only the layers they need, Step 20 normalizes normative policies across audits and recommendations, Step 21 adds uncertainty-aware robustness stress tests, Step 22 adds human-readable audit reporting, Step 23 hardens epistemic claim authority with synthetic validation benchmarks, Step 24 consolidates execution/protection semantics while expanding the negative validation matrix, Step 25 adds a panel-backed external validation harness with graph ablations, negative controls, and protected-outcome checks, Step 26 adds a LangGraph-compatible SFM intent node, and Step 27 adds a run-level SFM Agent Monitor with timeline, risk events, and human-review routing.

## What is inside

Core causal layers:

- `scm_parts/`: SCM, DAG/ADMG, ID algorithm, do-calculus, structural counterfactual utilities.
- `amantia/causal_core/identification/`: identification adapter.
- `amantia/causal_core/counterfactual/`: action/outcome comparison adapter.
- `amantia/causal_core/estimation/` and `estimation_parts/`: estimation diagnostics, placebo, negative controls, sensitivity.

SFM layer:

- `amantia/causal_core/final/schema.py`: `FinalCauseQuery`, `GoalSpec`, `AgentModel`, `FinalCauseResult`.
- `twin_model.py`: goal-present vs goal-removed policy comparison.
- `belief_model.py`: real graph vs agent belief graph.
- `falsification.py`: negative-control, placebo, side-effect goal audits.
- `utility.py`, `empirical_utility.py`, `multi_goal.py`: utility and goal-bundle diagnostics.
- `do_star.py`: formal `do*(A = policy(S, B, G_bundle, U))` surface.
- `identifiability.py`: SFM authority classification.
- `goal_discovery.py`, `policy_learning.py`, `temporal.py`, `context_conditioning.py`: inverse/temporal/contextual goal inference.
- `hierarchical.py`, `constraint.py`, `normative.py`: means-end, constraints, and value policy layers. Step 20 adds `NormalizedNormativePolicy` so inline JSON policy and rich `NormativeRule` objects share one contract.
- `protection.py`: Step 24 canonicalizes protected outcomes, hard/soft constraints, side effects and normative protection/prohibition into one `SFMProtectionPolicy`.
- `recommendation.py`: SFM action recommendation under goals, constraints, norms and uncertainty.
- `robustness.py`: Step 21 robustness audit under uncertainty, evidence quality, margins and identifiability authority.
- `alignment_summary.py`: compact governance verdict added in Step 18.
- `execution.py` and `runner.py`: execution profiles, enabled/disabled layers, and a reusable `SFMExecutionRunner` added across Steps 19 and 24.
- `validation_benchmark.py`: deterministic synthetic cases added in Step 23 and expanded in Step 24 to test epistemic boundaries and negative cases.
- `external_validation.py`: Step 25 panel-backed validation harness for longitudinal action-event data, graph ablations, negative controls, and protected-outcome controls.

## Main APIs

Full diagnostic output:

```python
from amantia.causal_core.final import infer_final_cause

result = infer_final_cause(payload)
print(result["most_likely_goal"])
print(result["alignment_summary"])
```

Compact gate-facing output:

```python
from amantia.causal_core.final import infer_final_cause_compact

compact = infer_final_cause_compact(payload)
print(compact["alignment_summary"]["verdict"])
print(compact["alignment_summary"]["gate_status"])
```

Selectable execution profiles:

```python
from amantia.causal_core.final import infer_final_cause, resolve_sfm_execution_plan

plan = resolve_sfm_execution_plan({"execution_profile": "fast"})
result = infer_final_cause({**payload, "execution_profile": "fast"})

# Or narrow the stack explicitly:
result = infer_final_cause({
    **payload,
    "enabled_layers": ["identification", "counterfactual", "twin", "identifiability"],
})
```

Normalized normative policy:

```python
from amantia.causal_core.final import normalize_normative_policy

policy = normalize_normative_policy({
    "allowed_goals": [{"target": "task_success", "severity": 0.7}],
    "rules": [
        {"target": "unsafe_fast_answer", "target_type": "action", "status": "prohibited"}
    ],
})

print(policy.status_for_target("task_success", "goal"))
print(policy.status_for_target("unsafe_fast_answer", "action"))
```


Canonical protection policy:

```python
from amantia.causal_core.final import normalize_protection_policy

protection = normalize_protection_policy(payload)
print(protection.protected_outcomes)
print(protection.prohibited_actions)
```

Standalone alignment summary from already-computed layer outputs:

```python
from amantia.causal_core.final import summarize_sfm_alignment

summary = summarize_sfm_alignment(layer_payload)
```

Synthetic validation benchmark:

```python
from amantia.causal_core.final import run_sfm_validation_benchmark

report = run_sfm_validation_benchmark()
print(report["passed"])
print(report["false_positive_claims"])
```

Panel-backed validation benchmark:

```python
from amantia.causal_core.final import run_sfm_external_panel_benchmark

report = run_sfm_external_panel_benchmark("data/action_event_panel.csv")
print(report["passed"])
print(report["claim_authorization_accuracy"])
```

Step 23 also splits epistemic flags in the full and compact outputs:

- `intent_hypothesis_supported`: diagnostic evidence passes threshold.
- `intent_claim_authorized`: identifiability authorizes an SFM intent claim.
- `governance_execution_allowed`: the gate allows execution.

## Step 18 verdicts, Step 19 profiles, Step 20 policy normalization, and Step 21 robustness

`SFMAlignmentSummary` emits a compact verdict:

- `aligned_supported`
- `diagnostic_only`
- `plausible_but_unidentified`
- `supported_but_prohibited`
- `supported_but_constraint_blocked`
- `requires_escalation`
- `falsification_failed`
- `unsupported`
- `insufficient_evidence`

And a gate status:

- `allow`
- `review`
- `block`
- `escalate`
- `observe`

Important: the alignment summary does **not** erase underlying evidence. A goal can be plausibly pursued and still be prohibited or blocked by constraints.

Step 21 adds `robustness_support` and compact fields `robustness_status` / `robust_to_uncertainty`. Explicit high uncertainty or fragile pessimistic support can route the summary to `supported_but_uncertain` with gate status `review`.

Step 19 execution profiles:

- `full`
- `fast`
- `minimal`
- `governance`
- `discovery`
- `recommendation`

## Test

```bash
python -m pip install -e .
python -m pytest
```

Current verification for this package:

```text
317 passed
```


## Current SFM development status

Latest step: **Step 27 — SFM Agent Monitor for LangGraph workflows**.

The package now exposes both:

- `alignment_summary`: compact machine contract for allow/block/review/escalate gates.
- `audit_report`: human-readable markdown report for governance, safety review, and product teams.

```python
from amantia.causal_core.final import infer_final_cause

result = infer_final_cause(payload)
print(result["alignment_summary"]["gate_status"])
print(result["audit_report"]["markdown"])
```



## Step 24 consolidation note

Step 24 adds a reusable execution runner and a canonical `SFMProtectionPolicy`. This keeps the stack powerful but reduces semantic drift between protected outcomes, constraints, side effects and normative policy rules. The built-in benchmark now contains nine deterministic cases and keeps `false_positive_claims == 0`.




## Step 27: SFM Agent Monitor

Step 27 adds `SFMAgentMonitor`, a LangGraph-compatible run monitor layered on top of `SFMIntentAnalyzerNode`:

```python
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor

analyzer = SFMIntentAnalyzerNode()
monitor = SFMAgentMonitor()
state.update(analyzer(state))
state.update(monitor(state))
```

The monitor emits `sfm_monitor_events`, a run-level `sfm_monitor` report, `requires_human_review`, and `sfm_gate_status`. It converts SFM analyses into governance events such as `allow`, `claim_withheld`, `deception_alert`, `side_effect_alert`, and `blocked`. See `docs/SFM_STEP27_AGENT_MONITOR.md` and `examples/langgraph_sfm_agent_monitor_demo.py`.

## Step 26: LangGraph SFM intent monitor

Step 26 adds `sfm_langgraph`, a dependency-light LangGraph integration for SFM final-cause monitoring. The main entry point is a callable node:

```python
from sfm_langgraph import SFMIntentAnalyzerNode

node = SFMIntentAnalyzerNode()
update = node({
    "sfm_query": {...},
    "stated_goal": "task_throughput",
})
```

When LangGraph is installed, the same node can be added with `StateGraph.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())`. It returns `sfm_analysis` with `primary_intent`, `intentionality_score`, `final_cause_claim_level`, intended vs side-effect fields, deception risk, gate status, and claim-blocking reasons. See `docs/SFM_STEP26_LANGGRAPH_INTEGRATION.md` and `examples/langgraph_sfm_monitor_demo.py`.


## Step 25 external panel validation note

Step 25 adds `external_validation.py` and `run_sfm_external_panel_benchmark(...)`. The bundled action-event panel benchmark currently passes 4/4 cases with `false_positive_claims == 0` and `false_negative_claims == 0`. It is a validation harness, not a claim that panel correlations alone prove causalità finale: the positive case requires a supplied domain graph, and a graph-ablation case confirms that claim authority is withheld without it.
