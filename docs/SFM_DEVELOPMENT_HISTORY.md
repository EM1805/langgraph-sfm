# SFM Development History (Steps 2-18)

This file consolidates the previous per-step markdown files to keep the package compact without removing technical history.


---

## SFM_STEP10_GOAL_DISCOVERY

# SFM Step 10 — Goal Discovery

Step 10 adds a conservative goal-discovery layer for Structural Final Model development.

Earlier steps required callers to supply `candidate_goals`. That is safer when the analyst already knows the plausible final causes, but it leaves the SFM layer unusable when the candidate goal set is unknown. The new module proposes goal hypotheses from evidence already present in the query.

## New module

```text
amantia/causal_core/final/goal_discovery.py
```

Public API:

```python
from amantia.causal_core.final import discover_candidate_goals

report = discover_candidate_goals(payload)
```

Main classes:

```text
GoalDiscoveryEngine
GoalDiscoveryReport
DiscoveredGoalCandidate
```

## Evidence used

The discovery layer ranks outcome-like variables from:

- `candidate_actions[*].expected_outcomes`, `goal_scores`, `utility_scores`, `effect_estimates`, etc.
- descendants of `action_variable` in `scm_graph`;
- descendants of `action_variable` in `agent.belief_graph`;
- `agent.utility_model` weights;
- empirical `outcome_records` when supplied;
- lightweight name priors such as `success`, `satisfaction`, `reward`, `helpful`, `resolved`.

Protected or side-effect-like variables such as `harm`, `risk`, `damage`, `latency`, `cost`, and the configured `protected_outcome` are penalized so they are not promoted to final causes too easily.

## Integration with `infer_final_cause`

If explicit `candidate_goals` are supplied, they are preserved. Goal discovery is still reported diagnostically in:

```text
goal_discovery_support
```

If no explicit goals are supplied, `FinalCauseEngine` uses the top discovered goals as candidate SFM hypotheses and records:

```text
goal_discovery_support.used_for_inference = true
```

The result also includes:

```text
SFM_GOAL_DISCOVERY_BOOTSTRAPPED_CANDIDATE_GOALS
```

and the limit:

```text
candidate_goals_were_discovered_not_user_supplied
```

## Important limitation

Goal discovery does **not** prove intention. It only constructs a candidate set for the existing SFM pipeline. The later layers — SCM-ID, twin-policy comparison, belief support, falsification, utility, empirical utility, do*, and identifiability — still decide whether the discovered goal can support a final-cause claim.

---

## SFM_STEP11_POLICY_LEARNING

# SFM Step 11 — Policy Learning / Inverse Goal Inference

Step 11 adds a sequence-level diagnostic for Structural Final Model development.
Instead of evaluating one observed action only, the SFM layer can now inspect a
history of decisions and ask:

> Which candidate goal best explains the actions the agent repeatedly selected?

## New module

```text
amantia/causal_core/final/policy_learning.py
```

Public API:

```python
from amantia.causal_core.final import evaluate_policy_learning

report = evaluate_policy_learning(payload)
```

Main classes:

- `PolicyLearningEngine`
- `PolicyLearningAudit`
- `PolicyGoalEvidence`

## Supported inputs

The evaluator reads any of these sequence keys:

- `policy_records`
- `decision_records`
- `action_records`
- `action_history`
- `decision_history`
- `trajectory_records`
- `trajectory`
- `trajectories`
- `outcome_records` as fallback

Each record can contain:

```json
{
  "selected_action": "ask_clarification",
  "candidate_actions": [
    {"action": "answer_directly", "expected_outcomes": {"task_success": 0.5}},
    {"action": "ask_clarification", "expected_outcomes": {"task_success": 0.86}}
  ]
}
```

If per-decision alternatives are unavailable, the module falls back to selected
action outcome records only and marks the result as weaker.

## Output added to `infer_final_cause`

`FinalCauseResult` now includes:

```json
{
  "policy_learning_support": {
    "assessed": true,
    "most_likely_goal": "task_success",
    "inferred_goal_bundle": [...],
    "goal_evidence": [...]
  }
}
```

## Interpretation

This layer is diagnostic, not proof.  It strengthens an SFM claim when the same
goal explains a sequence of observed action choices over time.  It weakens the
claim when the sequence favors another goal or when the sequence is too short.

Important reason codes:

- `SFM_POLICY_LEARNING_ASSESSED_SEQUENCE`
- `SFM_POLICY_LEARNING_FOUND_PLAUSIBLE_GOAL`
- `SFM_POLICY_LEARNING_SUPPORTS_CANDIDATE_GOAL`
- `SFM_POLICY_LEARNING_SEQUENCE_TOO_SHORT`
- `SFM_POLICY_LEARNING_NO_SEQUENCE_RECORDS`

## Why this matters for SFM

Earlier steps formalized `do*`, twin policies, utility functions, and goal
discovery for one decision.  Step 11 begins inverse goal inference across time:

```text
observed action sequence -> candidate goal likelihoods -> inferred goal bundle
```

This is the first step toward learning stable telic patterns from behavior.

---

## SFM_STEP12_TEMPORAL_GOAL_DRIFT

# SFM Step 12 — Temporal SFM / Goal Drift Detection

Step 12 adds a temporal diagnostic for Structural Final Model development.  The
SFM layer can now inspect an ordered sequence of decisions and ask:

> Did the dominant inferred goal remain stable, or did it drift over time?

## New module

```text
amantia/causal_core/final/temporal.py
```

Public API:

```python
from amantia.causal_core.final import evaluate_temporal_goal_drift

report = evaluate_temporal_goal_drift(payload)
```

Main classes:

- `TemporalGoalDriftDetector`
- `TemporalGoalDriftAudit`
- `TemporalGoalWindow`
- `GoalDriftEvent`

## Supported inputs

The detector reads ordered decision records from any of these keys:

- `temporal_records`
- `goal_drift_records`
- `policy_records`
- `decision_records`
- `action_records`
- `action_history`
- `decision_history`
- `trajectory_records`
- `trajectory`
- `trajectories`
- `outcome_records` as fallback

Records may include time fields such as `timestamp`, `time`, `date`, `datetime`,
`t`, `step`, or `index`.  If none are present, the detector uses input order.

## Windowing controls

```json
{
  "temporal_window_size": 3,
  "min_temporal_window_records": 3,
  "min_temporal_goal_support": 0.5
}
```

Each temporal window is passed through the Step 11 policy-learning engine.  The
Step 12 layer then compares dominant goals across adjacent windows.

## Output added to `infer_final_cause`

`FinalCauseResult` now includes:

```json
{
  "temporal_goal_drift_support": {
    "assessed": true,
    "drift_detected": true,
    "initial_goal": "task_success",
    "final_goal": "latency",
    "window_evidence": [...],
    "drift_events": [...]
  }
}
```

## Interpretation

This is still diagnostic, not proof.  A drift event means that adjacent temporal
windows have different dominant goals and both windows meet the minimum support
threshold.  Confidence shifts without a goal change are tracked separately as
`confidence_shift` events.

Important reason codes:

- `SFM_TEMPORAL_GOAL_DRIFT_DETECTED`
- `SFM_TEMPORAL_STABLE_GOAL_PATTERN`
- `SFM_TEMPORAL_WEAK_OR_UNSTABLE_GOAL_PATTERN`
- `SFM_TEMPORAL_GOAL_CHANGE_BETWEEN_STRONG_WINDOWS`
- `SFM_TEMPORAL_FINAL_WINDOW_SUPPORTS_CANDIDATE_GOAL`
- `SFM_TEMPORAL_INSUFFICIENT_RECORDS`

## Why this matters for SFM

Steps 10 and 11 infer plausible goals from actions and sequences.  Step 12 adds
time: it distinguishes a stable telic pattern from goal drift.

```text
ordered decisions -> inverse-goal windows -> stable goal or drift event
```

This is a first step toward SFM models that handle changing intentions, policy
updates, context shifts, and telic instability.

---

## SFM_STEP13_CONTEXT_CONDITIONING

# SFM Step 13 — Context-conditioned Structural Final Models

Step 13 adds a context-conditioned diagnostic layer for Structural Final Model development.

Earlier steps can detect temporal goal drift:

```text
window_1 -> task_success
window_2 -> latency
```

That pattern may mean the agent's goal changed over time.  But it may also mean the agent follows a stable context-conditioned policy:

```text
if ambiguity = high -> optimize task_success
if ambiguity = low  -> optimize latency / speed
```

This step distinguishes those two explanations.

## Added module

```text
amantia/causal_core/final/context_conditioning.py
```

Main API:

```python
from amantia.causal_core.final import evaluate_context_conditioning

report = evaluate_context_conditioning(payload)
```

Integrated API:

```python
from amantia.causal_core.final import infer_final_cause

result = infer_final_cause(payload)
context = result["context_conditioning_support"]
```

## What the audit does

1. Reads historical decision records from `context_records`, `policy_records`, `decision_records`, `action_history`, `trajectory`, or `outcome_records`.
2. Selects a context key from `context_key` / `context_keys`, or infers one from record-level `context` dictionaries.
3. Groups records by context value.
4. Runs inverse-goal / policy learning inside each context bucket.
5. Reports whether different context values support different dominant goals.

## Example interpretation

```json
{
  "context_key": "ambiguity",
  "dominant_goal_by_context": {
    "high": "task_success",
    "low": "latency"
  },
  "context_conditioning_detected": true,
  "policy_type": "context_conditioned_policy"
}
```

This means the apparent drift is plausibly a stable context-conditioned telic policy rather than a true change in the agent's final cause.

## New result field

`FinalCauseResult` now includes:

```text
context_conditioning_support
```

Important fields:

```text
assessed
context_key
context_conditioning_detected
policy_type
current_context_value
current_context_goal
dominant_goal_by_context
context_profiles
```

## Interaction with temporal drift

If `TemporalGoalDriftDetector` sees drift but `ContextConditioningEvaluator` explains that drift by context, `FinalCauseEngine` adds:

```text
SFM_CONTEXT_CONDITIONING_MAY_EXPLAIN_TEMPORAL_DRIFT
temporal_drift_may_be_context_conditioned_policy
```

The score cap for a non-final temporal goal is relaxed only when the current context specifically supports the candidate goal.

## Conservative limits

This is still diagnostic, not proof of intention.  The module requires at least two usable context buckets and candidate goals.  If context labels are missing or too sparse, it returns an unassessed report rather than guessing.

---

## SFM_STEP14_HIERARCHICAL_GOALS

# SFM Step 14: Hierarchical goals

Step 14 adds a conservative hierarchical SFM audit that distinguishes **instrumental goals** from more terminal **final goals**.

Example:

```text
response_speed -> user_satisfaction
```

Here `response_speed` may be a means. `user_satisfaction` is the higher-level telos that the means-end path supports.

## New module

```text
amantia/causal_core/final/hierarchical.py
```

Public API:

```python
from amantia.causal_core.final import evaluate_hierarchical_goals
```

Main classes:

- `GoalHierarchyEdge`
- `HierarchicalGoalProfile`
- `HierarchicalGoalAudit`
- `HierarchicalGoalEvaluator`

## Inputs

The evaluator accepts explicit hierarchy formats such as:

```json
{
  "goal_hierarchy_edges": [
    {"instrumental_goal": "response_speed", "final_goal": "user_satisfaction"}
  ]
}
```

It also recognizes `goal_hierarchy`, `telos_edges`, `instrumental_edges`, `means_end_edges`, `goal_edges`, `instrumental_goals`, and `means_to_ends`.

If `infer_goal_hierarchy_from_graph` is true, the evaluator can derive goal-to-goal edges from `scm_graph` or `agent.belief_graph`, but such edges are marked as requiring domain validation.

## Output

`infer_final_cause(...)` now includes:

```json
{
  "hierarchical_goal_support": {
    "assessed": true,
    "instrumental_goals": ["response_speed"],
    "terminal_goals": ["user_satisfaction"],
    "selected_ultimate_goal": "user_satisfaction"
  }
}
```

The audit remains diagnostic. It does not prove ultimate final causality; it prevents the SFM layer from too quickly promoting a means to the status of final cause.

---

## SFM_STEP15_CONSTRAINT_AWARE

# SFM Step 15 — Constraint-aware SFM

Step 15 adds a conservative constraint-aware diagnostic layer for Structural Final Model development.

The point of this layer is to prevent the model from confusing:

```text
final goals
instrumental goals
protected outcomes
hard constraints
soft constraints
side effects
```

A constrained telic policy can now ask:

```text
Which action best serves the final goal after hard/protected constraints are enforced?
```

This is different from unconstrained goal maximization. For example, `answer_directly` may maximize `task_success`, but if it violates a hard constraint on `user_or_system_harm`, the constraint-aware policy can select `ask_clarification` instead.

## New module

```text
amantia/causal_core/final/constraint.py
```

Exports:

```python
SFMConstraintSpec
ConstraintEvaluation
ConstraintActionAssessment
ConstraintAwareAudit
ConstraintAwareEvaluator
evaluate_constraint_aware_sfm
```

## Supported inputs

Constraints can be supplied as:

```json
{
  "constraints": {
    "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}],
    "soft": [{"outcome": "latency", "direction": "decrease", "threshold": 0.40, "weight": 0.2}],
    "side_effects": ["latency"]
  }
}
```

or via top-level keys:

```json
{
  "hard_constraints": [...],
  "soft_constraints": [...],
  "protected_constraints": [...],
  "side_effect_constraints": [...]
}
```

The existing `protected_outcome` is automatically treated as a protected constraint.

## New final-cause output

`FinalCauseResult` now includes:

```json
{
  "constraint_support": {
    "assessed": true,
    "selected_action": "ask_clarification",
    "selected_action_matches_observed": true,
    "observed_feasible": true,
    "final_goals": ["task_success"],
    "protected_constraints": ["user_or_system_harm"],
    "hard_constraints": ["user_or_system_harm"],
    "soft_constraints": ["latency"],
    "side_effect_outcomes": ["latency"]
  }
}
```

## Conservative behavior

If a candidate goal overlaps with a protected, hard, or side-effect outcome, the SFM result adds:

```text
SFM_CANDIDATE_GOAL_CLASSIFIED_AS_CONSTRAINT_NOT_FINAL_GOAL
```

and caps the final-cause score. This keeps outcomes such as `harm`, `risk`, or monitored side effects from being promoted to final causes merely because they are causally affected by the action.

## Tests

```text
tests/test_sfm_constraint_step15.py
```

---

## SFM_STEP16_NORMATIVE_ALIGNMENT

# SFM Step 16 — Normative / value-alignment layer

Step 16 adds a diagnostic layer that separates two questions:

1. **Teleological inference**: what goal does the agent appear to pursue?
2. **Normative classification**: is that pursued goal/action allowed, prohibited, protected, monitored, or escalation-worthy under an explicit policy?

This distinction is important because a prohibited goal can still be the goal an agent appears to pursue. The normative layer classifies value alignment without erasing the underlying SFM evidence.

## New module

```text
amantia/causal_core/final/normative.py
```

Public API:

```python
from amantia.causal_core.final import evaluate_normative_sfm

audit = evaluate_normative_sfm(payload)
```

## Input surface

The evaluator reads any of these policy keys:

```json
{
  "normative_policy": {
    "allowed_goals": ["task_success"],
    "prohibited_goals": ["manipulate_user"],
    "protected_goals": ["user_or_system_harm"],
    "escalation_goals": ["high_impact_decision"],
    "allowed_actions": ["safe_answer"],
    "prohibited_actions": ["unsafe_fast_answer"],
    "strict_goal_allowlist": true,
    "rules": [
      {"target": "task_success", "target_type": "goal", "status": "allowed"}
    ]
  }
}
```

Aliases are also accepted: `value_policy` and `alignment_policy`.

## Output surface

`infer_final_cause(...)` now includes:

```json
{
  "normative_support": {
    "assessed": true,
    "goal_status": "allowed",
    "action_status": "allowed",
    "alignment_status": "normatively_aligned",
    "normatively_aligned": true,
    "prohibited": false,
    "requires_escalation": false
  }
}
```

Possible goal/action statuses include:

```text
allowed
prohibited
required
protected
escalation_required
monitored
discouraged
not_on_allowlist
unspecified
```

## Design rule

This layer is deliberately conservative:

- It does **not** prove intent.
- It does **not** hide a bad/prohibited intent.
- It does prevent protected outcomes from being promoted as terminal final goals.
- It adds reason codes and limits for downstream governance.

Important reason codes:

```text
SFM_NORMATIVE_POLICY_ASSESSED
SFM_NORMATIVE_GOAL_ALLOWED
SFM_NORMATIVE_GOAL_PROHIBITED
SFM_NORMATIVE_GOAL_PROTECTED_NOT_FINAL
SFM_NORMATIVE_ESCALATION_REQUIRED
SFM_NORMATIVE_ALIGNMENT_PASS
SFM_NORMATIVE_ALIGNMENT_FAIL
```

---

## SFM_STEP17_ACTION_RECOMMENDATION

# SFM Step 17 — Intervention recommendation under SFM

Step 17 adds an operational recommendation layer on top of the SFM diagnostics.
It ranks candidate actions under:

- final goals / goal bundles;
- hard, protected, soft, and side-effect constraints;
- normative/value policy rules;
- risk penalties;
- causal or outcome uncertainty penalties.

The new public API is:

```python
from amantia.causal_core.final import recommend_sfm_action

result = recommend_sfm_action(payload)
```

The main output fields are:

- `recommended_action`
- `recommendation_status`
- `goal_bundle`
- `rankings`
- `feasible_actions`
- `blocked_actions`
- `escalation_actions`
- `recommended_intervention`

The recommendation is serialized as a conservative `do*`-style intervention:

```text
do*(agent_action=pi_sfm_recommendation_policy(S,B,G_bundle,U)->safe_answer | agent=assistant_agent, goals=[task_success,user_satisfaction])
```

This layer is not a proof that an action is objectively optimal.  It is an
auditable diagnostic recommendation under supplied assumptions.

## Integration with `infer_final_cause`

`FinalCauseResult` now includes:

```python
action_recommendation_support: dict
```

If the SFM recommender selects the observed action for a candidate goal bundle,
that adds weak diagnostic support to the final-cause score.  If the observed
action is blocked by constraints or normative policy, the final-cause score is
capped conservatively.

---

## SFM_STEP2_TWIN_MODEL

# SFM Step 2 — Twin-policy diagnostic

Questo step aggiunge il primo embrione operativo di twin model per Structural Final Model.

## Cosa è stato aggiunto

- `amantia/causal_core/final/twin_model.py`
  - `TwinPolicyComparator`
  - `TwinPolicyComparison`
  - `compare_twin_policies(payload, goal=None)`
- `FinalCauseResult.twin_support`
- integrazione in `FinalCauseEngine.infer(...)`
- test:
  - `tests/test_sfm_twin_model_step2.py`
- esempio:
  - `examples/inputs/sample_twin_policy_query.json`

## Logica implementata

Per ogni candidate goal `G`, il sistema confronta:

```text
policy_with_goal(G)
policy_without_goal(G)
```

Il segnale SFM è più forte quando:

1. `action -> goal` è causalmente identificabile nel grafo SCM.
2. L'azione osservata è preferita dal confronto controfattuale classico.
3. La policy con il goal seleziona l'azione osservata.
4. Rimuovendo il goal, la policy seleziona un'altra azione.
5. Il goal non coincide con outcome protetti o side-effect dichiarati.

## Caveat

Il twin model è ancora diagnostico e score-based. Non è ancora una rappresentazione strutturale completa delle equazioni controfattuali dell'agente. Il prossimo step consigliato è separare:

- grafo causale reale;
- grafo di credenze dell'agente;
- utility osservata/stimata;
- final-cause identification criteria.

---

## SFM_STEP3_AGENT_BELIEFS

# SFM Step 3 — Agent belief graph vs real SCM graph

Questo step separa esplicitamente due oggetti causali che uno Structural Final Model non dovrebbe confondere:

1. **real/system SCM graph**: il grafo usato per chiedere se l'azione ha davvero un percorso causale verso il goal;
2. **agent belief graph**: il grafo soggettivo dell'agente, usato per chiedere se l'agente poteva credere che l'azione avrebbe promosso quel goal.

## Cosa è stato aggiunto

- `amantia/causal_core/final/belief_model.py`
  - `AgentBeliefEvaluator`
  - `BeliefCausalAssessment`
  - `assess_agent_beliefs(payload, goal=None)`
- `FinalCauseResult.belief_support`
- integrazione in `FinalCauseEngine.infer(...)`
- test:
  - `tests/test_sfm_belief_model_step3.py`
- esempio:
  - `examples/inputs/sample_agent_belief_query.json`

## Logica implementata

Per ogni candidate goal `G`, il sistema controlla la raggiungibilità diretta/indiretta:

```text
real_graph:          action_variable -> ... -> G
agent_belief_graph:  action_variable -> ... -> G
```

Questo produce quattro casi importanti:

| Caso | Interpretazione SFM |
|---|---|
| real path sì, belief path sì | l'azione è plausibile sia causalmente sia intenzionalmente |
| real path no, belief path sì | l'agente può aver agito per il fine, ma sulla base di una credenza causale falsa |
| real path sì, belief path no | l'azione avrebbe funzionato, ma non è chiaro che l'agente la abbia scelta per quel fine |
| real path no, belief path no | attribuzione teleologica debole |

## Perché conta

Prima di questo step, Amantia poteva dire: "questa azione ottimizza questo outcome". Ora può dire qualcosa di più vicino a SFM:

```text
L'agente ha scelto A per G secondo il suo belief graph,
anche se il grafo reale conferma, nega o lascia incerto l'effetto A -> G.
```

## Caveat

Questo è ancora diagnostico: usa reachability su grafi diretti, non una teoria completa di identificazione teleologica. Tuttavia impedisce un errore importante: trattare il grafo reale come se fosse automaticamente il grafo mentale/decisionale dell'agente.

## Prossimo step consigliato

Aggiungere falsification tests per SFM:

- negative-control goals;
- placebo goals;
- side-effect goals;
- intention stability across contexts;
- confronto tra `policy_with_goal(G)` e policy con goal concorrenti.

---

## SFM_STEP4_FALSIFICATION

# SFM Step 4 — Falsification diagnostics

This step adds conservative falsification checks to the Structural Final Model development layer.

The core question remains:

```text
Did the agent choose action A because it was pursuing goal G?
```

Step 4 adds a second question:

```text
Would the same action also look intentional for goals that should not explain it?
```

If the answer is yes, Amantia reduces or blocks the final-cause claim.

## Added module

```text
amantia/causal_core/final/falsification.py
```

Exports:

```python
SFMFalsificationAuditor
FalsificationReport
FalsificationGoalAudit
audit_sfm_falsification
```

## Supported falsification goals

### Negative-control goals

Outcomes that should not be targeted by the observed action.

```json
"negative_control_goals": ["unrelated_metric"]
```

If a negative-control goal also makes the observed action look goal-dependent, the SFM interpretation is treated as suspicious.

### Placebo goals

Fake or irrelevant goals used to probe over-attribution.

```json
"placebo_goals": ["fake_placebo_goal"]
```

If the model can explain the action by a placebo goal, it is probably too eager to infer teleology.

### Side-effect goals

Outcomes that may be produced by the action but should not automatically be treated as the final cause.

```json
"side_effect_goals": ["engagement_spike"]
```

If a side effect explains the observed action as well as the candidate goal, the final-cause claim is blocked until stronger agent-belief evidence is available.

## Integration into FinalCauseEngine

`FinalCauseResult` now includes:

```json
{
  "falsification_support": {...},
  "falsification_passed": true
}
```

The final intent score is multiplied by the falsification report:

```text
high-severity negative-control/placebo failure -> multiplier 0.45
medium-severity side-effect ambiguity          -> multiplier 0.70
no falsification failure                       -> multiplier 1.00
```

A failed falsification check also prevents `inferred=true`.

## Important limitation

This is diagnostic, not a proof that an agent did or did not have an intention.  It is meant to make SFM development more conservative by asking whether the same action is also explained by implausible, fake, or merely side-effect goals.

---

## SFM_STEP5_UTILITY_FUNCTION

# SFM Step 5 — Explicit agent utility function

This step adds an auditable utility-function layer to the Structural Final Model development surface.

The SFM question remains:

```text
Did the agent choose action A because it was pursuing goal G?
```

Step 5 adds a policy-level diagnostic:

```text
Does an explicit utility function select the observed action once we separate
primary goals, protected constraints, side effects, auxiliary preferences, and risk?
```

## Added module

```text
amantia/causal_core/final/utility.py
```

Exports:

```python
UtilityComponent
ActionUtilityBreakdown
UtilityFunctionAudit
UtilityFunctionEvaluator
evaluate_utility_function
```

## Utility decomposition

Each action is decomposed into:

```text
primary_goal_utility
protected_penalty
side_effect_utility
auxiliary_utility
risk_penalty
total_utility
```

This makes final-cause attribution more conservative.  A candidate action can have the highest primary-goal score but still lose if it violates a protected outcome such as harm or risk.

## Example

```python
from amantia.causal_core.final import evaluate_utility_function

result = evaluate_utility_function({
    "observed_action": "ask_clarification",
    "action_variable": "agent_action",
    "candidate_goals": [{"goal_variable": "task_success"}],
    "candidate_actions": [
        {
            "action": "answer_directly",
            "expected_outcomes": {
                "task_success": 0.96,
                "user_or_system_harm": 0.80
            },
            "risk": "high",
            "harm_probability": 0.80
        },
        {
            "action": "ask_clarification",
            "expected_outcomes": {
                "task_success": 0.78,
                "user_or_system_harm": 0.02
            },
            "risk": "low",
            "harm_probability": 0.02
        }
    ],
    "protected_outcome": "user_or_system_harm"
})

print(result["selected_action"])
print(result["tradeoff_detected"])
```

The utility function selects `ask_clarification` even though `answer_directly` has higher raw task success, because the protected harm constraint dominates.

## Integration into FinalCauseEngine

`FinalCauseResult` now includes:

```json
{
  "utility_support": {
    "assessed": true,
    "selected_action": "ask_clarification",
    "selected_action_matches_observed": true,
    "tradeoff_detected": true,
    "rankings": [...]
  }
}
```

If the explicit utility audit selects the observed action, the SFM intent score receives additional support and the result includes:

```text
SFM_UTILITY_SUPPORTS_OBSERVED_ACTION
```

If the explicit utility audit does not select the observed action, the result adds:

```text
explicit_utility_function_does_not_select_observed_action
```

## Why this matters for SFM

Without an explicit utility decomposition, a model can confuse:

```text
main goal
protected constraint
side effect
auxiliary preference
```

Step 5 makes those roles inspectable.  This is required before implementing more mature multi-objective `do*` policies and agent-level structural equations.

## Important limitation

This layer is still diagnostic.  It ranks actions under a transparent utility function, but it does not yet identify the true utility function from behavior over time.  The next step should connect this layer to `OutcomeTracker` or observed action histories so utilities can be updated empirically.

---

## SFM_STEP6_EMPIRICAL_UTILITY

# SFM Step 6 — Empirical implicit-utility learning

Step 6 connects the Structural Final Model development layer to Amantia's outcome-tracking loop.

The previous SFM layers could already ask:

- does the real SCM support `action -> goal`?
- does the agent belief graph support `action -> goal`?
- does the twin-policy comparison select the observed action when the candidate goal is included?
- does the explicit utility function select the observed action?
- do placebo, negative-control, or side-effect goals falsify the intention claim?

This step adds a weaker but practical historical question:

> Given observed action/outcome records, which candidate action has empirically produced the candidate goal most reliably?

## New module

```text
amantia/causal_core/final/empirical_utility.py
```

Public surface:

```python
from amantia.causal_core.final import (
    EmpiricalUtilityLearner,
    EmpiricalUtilityAudit,
    EmpiricalActionEvidence,
    evaluate_empirical_utility,
)
```

## Input forms

The evaluator accepts either inline records:

```json
{
  "outcome_records": [
    {"selected_action": "ask_clarification", "success": true, "harm": false},
    {"selected_action": "answer_directly", "success": false, "harm": false}
  ]
}
```

or an Amantia learning log path:

```json
{
  "outcome_log_path": "out/learning/audit_log.jsonl"
}
```

The log path is read through `amantia.learning.outcome_tracker.OutcomeTracker`.

## Output

`FinalCauseResult` now includes:

```json
{
  "empirical_utility_support": {
    "assessed": true,
    "goal_variable": "task_success",
    "selected_action": "ask_clarification",
    "selected_action_matches_observed": true,
    "support_strength": 0.9,
    "action_evidence": []
  }
}
```

## Interpretation

This is not causal identification. It is historical consistency evidence.

A strong empirical audit means:

> the observed action is also the action that historically best served the candidate goal within the supplied action set.

A weak or failed empirical audit means:

> either there is not enough outcome history, or the observed action does not match the action with the best observed goal performance.

## Conservative design choices

- Requires at least two candidate actions with sufficient empirical goal evidence.
- Default minimum: `min_empirical_records_per_action = 2`.
- Uses action records only from the current candidate action set.
- Penalizes observed harm weakly when ranking empirical utility.
- Treats user satisfaction as weak auxiliary evidence unless it is the candidate goal.
- Adds at most a small increment to `intent_score`.

## Example

```python
from amantia.causal_core.final import evaluate_empirical_utility

result = evaluate_empirical_utility({
    "observed_action": "ask_clarification",
    "candidate_goals": ["task_success"],
    "candidate_actions": ["answer_directly", "ask_clarification"],
    "outcome_records": [
        {"selected_action": "ask_clarification", "success": True, "harm": False},
        {"selected_action": "ask_clarification", "success": True, "harm": False},
        {"selected_action": "answer_directly", "success": False, "harm": False},
        {"selected_action": "answer_directly", "success": True, "harm": True}
    ]
})
```

The result reports whether the historical implicit-utility ranking selects the observed action.

## Tests

```text
tests/test_sfm_empirical_utility_step6.py
```

Current verification after Step 6:

```text
251 passed
```

---

## SFM_STEP7_MULTI_GOAL

# SFM Step 7 — Multi-goal / multi-objective SFM

This step adds a diagnostic layer for cases where an agent is not plausibly acting for one isolated final cause, but for a weighted bundle of goals and constraints.

New module:

```text
amantia/causal_core/final/multi_goal.py
```

New public API:

```python
from amantia.causal_core.final import evaluate_multi_goal_utility

audit = evaluate_multi_goal_utility(payload)
```

The audit evaluates:

```text
weighted goal bundle
+ auxiliary agent utility
- protected constraint penalties
- risk penalties
```

It is useful when the observed action is not best for any single goal, but is best for the bundle. For example:

```text
maximize_task_success        best for task_success only
maximize_user_satisfaction   best for satisfaction only
balanced_policy              best for both together
```

The output includes:

- `goal_bundle`
- `selected_action`
- `selected_action_matches_observed`
- `best_single_goal_actions`
- `tradeoff_detected`
- `bundle_score_exceeds_best_single_goal_score`
- per-action rankings with contribution-level decomposition

`FinalCauseEngine.infer(...)` now also includes:

```json
{
  "multi_goal_support": { ... }
}
```

This remains diagnostic only. It does not yet perform full multi-objective SFM identification, but it gives the package an auditable surface for testing whether an action is better explained by a bundle of final causes than by a single candidate goal.

---

## SFM_STEP8_DO_STAR_OPERATOR

# SFM Step 8 — Formal `do*` operator API

This step adds a formal intentional-intervention surface for Structural Final Model development:

```text
do*(A = pi_policy(S, B, G_bundle, U) -> a*)
```

Where:

- `S` is the observed state / information set;
- `B` is the agent belief graph;
- `G_bundle` is the single-goal or multi-goal final-cause bundle;
- `U` is the explicit or derived utility function;
- `a*` is the action selected by the policy.

## New module

```text
amantia/causal_core/final/do_star.py
```

Exports:

- `DoStarOperator`
- `DoStarOperatorResult`
- `DoStarPolicyInputAudit`
- `evaluate_do_star_intervention(payload)`

## What it checks

The operator does not merely serialize a string. It also audits whether the policy induced by `S`, `B`, `G_bundle`, and `U` selects the observed action.

It reports:

- formal `do*` expression;
- policy signature;
- selected action;
- whether selected action matches the observed action;
- goal bundle;
- input availability audit;
- underlying utility or multi-goal policy audit;
- rankings of candidate actions;
- conservative limits and reason codes.

## Integration

`FinalCauseEngine.infer(...)` now includes:

```json
{
  "do_star_support": {
    "operator": "do_star",
    "policy_signature": "policy(S, B, G_bundle, U)",
    "selected_action_matches_observed": true
  }
}
```

It also enriches `intentional_intervention` with:

```json
{
  "formal_expression": "do*(agent_action=pi_policy(S,B,G_bundle,U)->balanced_policy | agent=assistant_agent, goals=[task_success,user_satisfaction])",
  "policy_signature": "policy(S, B, G_bundle, U)",
  "selected_by_policy": "balanced_policy"
}
```

## Status

This remains diagnostic, not full SFM identification. Its purpose is to make the intentional intervention explicit, serializable, testable, and composable with SCM-ID, belief graphs, twin-policy comparison, falsification tests, and utility diagnostics.

---

## SFM_STEP9_IDENTIFIABILITY

# SFM Step 9: Identifiability Layer

Step 9 adds a conservative identifiability/authority layer for Structural Final Model development.

The core question is no longer only:

```text
Does the SFM diagnostic score pass the intent threshold?
```

It also asks:

```text
What epistemic authority does that final-cause claim have?
```

## New module

```text
amantia/causal_core/final/identifiability.py
```

Exports:

```python
from amantia.causal_core.final import (
    SFMIdentifiabilityAssessment,
    SFMIdentifiabilityEvaluator,
    assess_sfm_identifiability,
)
```

## Classification tiers

The evaluator reports one of four conservative tiers:

```text
diagnostic_only
falsifiable_diagnostic
partially_identifiable
strongly_supported
```

Interpretation:

- `diagnostic_only`: useful scoring, but insufficient epistemic structure.
- `falsifiable_diagnostic`: the claim has alternatives, twin comparisons, or control goals that can falsify it.
- `partially_identifiable`: real action->goal support, goal-dependent twin-policy behavior, side-effect exclusion, and falsification checks align.
- `strongly_supported`: partial identifiability plus auxiliary support from agent beliefs, utility, empirical records, multi-goal policy, or `do*`.

This still does **not** claim metaphysical proof of final causation.

## Main output field

`infer_final_cause(...)` now returns:

```json
{
  "sfm_identifiability_support": {
    "tier": "partially_identifiable",
    "authority_status": "partial_sfm_identification",
    "can_claim_intent": true,
    "is_falsifiable": true,
    "evidence_matrix": {
      "causal_action_goal_effect_identified": true,
      "twin_policy_changes_when_goal_removed": true,
      "side_effects_excluded": true,
      "falsification_passed": true
    }
  },
  "authority_status": "partial_sfm_identification"
}
```

## Why this matters

Before Step 9, a high intent score could be read too strongly. Now the system separates:

```text
score strength
vs
identifiability/authority strength
```

This prevents Amantia from saying “the agent intended G” when the stronger statement should be:

```text
The observed action is diagnostically consistent with goal G under the supplied SFM evidence.
```

## Important rule

A false real-world action->goal path blocks **partial identification**, but it can still allow a weaker diagnostic intent claim if the agent belief graph supports the action-goal link. This preserves the distinction between:

```text
The action really achieved G.
```

and

```text
The agent acted for G under its beliefs.
```

## Tests

```text
tests/test_sfm_identifiability_step9.py
```



## Step 19 — Execution profiles and enabled layers

Added `execution.py` with `SFMExecutionPlan`, public `EXECUTION_PROFILES`, `resolve_sfm_execution_plan(...)`, and explicit `enabled_layers` / `disabled_layers` support.

Default profile remains `full` to preserve existing behavior. New profiles (`fast`, `minimal`, `governance`, `discovery`, `recommendation`) reduce unnecessary layer execution while keeping each disabled layer auditable via structured disabled reports. `FinalCauseResult` now includes `execution_profile_support`, and compact inference exposes the same contract.


## Step 20 — Normative policy normalization

Added `NormalizedNormativePolicy`, `normalize_normative_policy(...)`, and `normative_status_for_target(...)`. Compact inline policies and rich `NormativeRule` objects now flow through the same rule normalizer.

`NormativeSFMAudit` now reports `normalized_policy`, rule counts, and applicable severity fields. `recommendation.py` consumes the same normalized policy, so governance audits and intervention recommendation share one normative semantics.

## Step 21 — Uncertainty-aware robustness

Added `robustness.py` with `RobustSFMEvaluator`, `RobustSFMAudit`, `RobustnessScenario`, and `evaluate_sfm_robustness(...)`. The layer stress-tests a candidate final-cause claim under candidate-action uncertainty, evidence quality, weak recommendation margins, identifiability authority, and hard-block penalties.

`FinalCauseResult` now includes `robustness_support`; `SFMAlignmentSummary` exposes `robustness_status`, `robust_to_uncertainty`, `uncertainty_review_required`, and `pessimistic_intent_score`. Explicit high uncertainty or fragile pessimistic support routes the governance verdict to `supported_but_uncertain` / `review` instead of `allow`.


## Step 22 — Audit report generator

Added `reporting.py` with `SFMAuditReportGenerator`, `SFMAuditReport`, `SFMReportSection`, and `render_sfm_audit_report(...)`.

The SFM result now includes `audit_report`, a markdown-first human report built from the structured evidence in `alignment_summary`, `robustness_support`, `normative_support`, `constraint_support`, `recommendation_support`, and related diagnostic layers.

This preserves the split between machine contract and human explanation:

```text
alignment_summary -> gate/governance systems
audit_report      -> reviewers, users, incident analysis, compliance notes
```


## Step 23 — Epistemic hardening and synthetic validation

- Added explicit split between diagnostic hypothesis support, authorized SFM claim, and governance execution allowance.
- `inferred` now tracks `intent_claim_authorized`, not raw diagnostic score.
- Missing real SCM graph blocks claim authority even when action ranking/twin evidence is strong.
- Partial identifiability now requires an independent validation channel: controls, belief graph, or empirical history.
- Normative prohibition blocks governance without erasing evidence that the prohibited goal may have been pursued.
- Added `validation_benchmark.py` and synthetic CI smoke tests for false positives, missing-graph cases, side effects, false beliefs, and prohibited goals.


## Step 24 — Core consolidation and negative validation matrix

- Added `layer_protocol.py` and `runner.py` to centralize layer-result coercion, enabled/disabled execution, and disabled reports.
- Added `protection.py` with `SFMProtectionSpec`, `SFMProtectionPolicy`, and `normalize_protection_policy(...)`.
- `ConstraintAwareAudit` now exposes `normalized_protection_policy` so downstream layers and external gates can inspect one canonical view of protected outcomes, hard constraints, side effects and normative protections/prohibitions.
- `FinalCauseEngine` now uses the normalized protection view when excluding protected outcomes and side effects from terminal final-cause promotion.
- Expanded the synthetic validation benchmark from five to nine cases, adding explicit negative cases for false-positive belief graphs, utility-without-SCM claims, protected-outcome candidates, and goal-discovery protection boundaries.
- Verification: `313 passed`.
