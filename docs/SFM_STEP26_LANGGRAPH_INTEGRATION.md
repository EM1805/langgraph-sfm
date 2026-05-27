# SFM Step 26 — LangGraph Integration

Step 26 adds a LangGraph-compatible node for using Structural Final Models as an intent monitor inside agentic workflows.

The integration is deliberately conservative:

- it does **not** claim to read an agent's real intentions directly;
- it returns a structured SFM diagnostic with explicit claim authority;
- it can run without LangGraph installed because LangGraph nodes are ordinary Python callables;
- it can be passed directly to `StateGraph.add_node(...)` when LangGraph is installed.

## Package surface

```python
from sfm_langgraph import SFMIntentAnalyzerNode

node = SFMIntentAnalyzerNode()
update = node(agent_state)
```

Compatibility re-export:

```python
from amantia.integrations.langgraph_sfm import SFMIntentAnalyzerNode
```

## State input

The node accepts either a fully formed SFM query under `sfm_query`:

```python
state = {
    "sfm_query": {
        "observed_action": "peer_review_gate",
        "candidate_actions": [...],
        "candidate_goals": [...],
        "scm_graph": {...},
        "outcome_records": [...],
    },
    "stated_goal": "task_throughput",
}
```

or common LangGraph/agent state keys:

```python
state = {
    "last_action": "ask_clarification",
    "candidate_actions": ["answer_directly", "ask_clarification"],
    "goals": [{"goal_variable": "task_success"}],
    "graph": {"nodes": [...], "edges": [...]},
    "user_goal": "task_success",
}
```

## State output

The node returns a partial state update:

```python
{
    "sfm_analysis": {
        "primary_intent": "task_throughput",
        "intentionality_score": 1.0,
        "final_cause_claim_level": "strong_diagnostic_sfm_support",
        "intent_hypothesis_supported": true,
        "intent_claim_authorized": true,
        "governance_execution_allowed": true,
        "intended_effects": ["task_throughput"],
        "side_effects": ["user_or_system_harm"],
        "side_effect_risk": "monitored",
        "deception_risk": "low",
        "gate_status": "allow",
        "blocked_claim_reason": "",
        "reason_codes": [...],
        "limits": [...]
    },
    "sfm_trace_events": [...]
}
```

The important field is `final_cause_claim_level`. It separates diagnostic evidence from authorized final-cause claims:

- `diagnostic_only`: SFM did not support a final-cause hypothesis above threshold.
- `falsifiable_diagnostic`: SFM supports a hypothesis, but causal claim authority is withheld.
- `strong_diagnostic_sfm_support` or another SFM authority status: the identifiability layer authorized a bounded final-cause claim.

## LangGraph usage

```python
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from sfm_langgraph import SFMIntentAnalyzerNode

class AgentState(TypedDict, total=False):
    sfm_query: dict
    stated_goal: str
    sfm_analysis: dict
    sfm_trace_events: list[dict]

builder = StateGraph(AgentState)
builder.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())
builder.add_edge(START, "sfm_intent_analyzer")
builder.add_edge("sfm_intent_analyzer", END)

graph = builder.compile()
result = graph.invoke({"sfm_query": {...}, "stated_goal": "task_throughput"})
```

## Failure behavior

By default, the node fails closed. If SFM raises an exception, the node returns:

```python
{
    "gate_status": "block",
    "final_cause_claim_level": "diagnostic_only",
    "blocked_claim_reason": "SFM node failed closed",
    "reason_codes": ["SFM_LANGGRAPH_NODE_FAILED_CLOSED"]
}
```

For debugging, pass `SFMIntentAnalyzerConfig(fail_closed=False)`.

## Demo

Plain callable demo:

```bash
python examples/langgraph_sfm_monitor_demo.py
```

LangGraph demo:

```bash
pip install langgraph
python examples/langgraph_sfm_monitor_demo.py --langgraph
```

## Validation added in Step 26

The new tests verify that:

1. the node returns a LangGraph-style partial state update;
2. a panel-backed authorized SFM claim becomes an `allow` gate status;
3. removing the SCM graph keeps the diagnostic hypothesis but withholds claim authority;
4. stated-goal mismatch is surfaced as deception risk;
5. the helper can attach the node to a LangGraph-like builder without importing LangGraph.

This makes SFM immediately demoable in agent graphs while preserving the core Step 23–25 epistemic boundary: an intent-looking pattern is not automatically a final-cause claim.
