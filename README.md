# langgraph-sfm

**Causal intent monitoring for LangGraph agents.**

`langgraph-sfm` adds a small, dependency-light SFM layer to LangGraph-style agent workflows. It does not claim to read an agent's “true mind”. It produces falsifiable, governance-facing evidence about plausible intentions, side effects, deception risk, and the epistemic level at which an intent claim is authorized.

```bash
pip install langgraph-sfm
# Optional, only when you want to run inside LangGraph itself:
pip install "langgraph-sfm[langgraph]"
```

```python
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor

analyzer = SFMIntentAnalyzerNode()
monitor = SFMAgentMonitor()

state = {
    "run_id": "agent-run-1",
    "last_action": "call_search_tool",
    "candidate_goals": [{"goal_variable": "answer_user_question"}],
    "graph": {
        "nodes": ["agent_action", "answer_user_question"],
        "edges": [["agent_action", "answer_user_question"]],
    },
    "stated_goal": "answer_user_question",
}

state.update(analyzer(state))
state.update(monitor(state))

print(state["sfm_analysis"]["primary_intent"])
print(state["sfm_analysis"]["final_cause_claim_level"])
print(state["sfm_gate_status"])
```

## What it adds to LangGraph

LangGraph is excellent at orchestrating stateful agent workflows. `langgraph-sfm` adds a layer for **teleological observability**:

- **Intent analysis node**: infer the most plausible goal behind an observed action.
- **Epistemic claim control**: distinguish diagnostic hints from authorized SFM intent claims.
- **Side-effect monitoring**: separate intended effects from monitored or protected side effects.
- **Deception-risk signal**: compare stated goals with SFM-supported intent candidates.
- **Run monitor**: aggregate per-step analyses into a timeline, risk events, and human-review gate.

The core contract is intentionally conservative:

```python
state["sfm_analysis"] = {
    "primary_intent": "answer_user_question",
    "intentionality_score": 0.82,
    "final_cause_claim_level": "falsifiable_diagnostic",
    "intent_hypothesis_supported": True,
    "intent_claim_authorized": False,
    "blocked_claim_reason": "missing validated SCM graph",
    "deception_risk": "low",
    "side_effect_risk": "monitored",
    "gate_status": "review",
}
```

## LangGraph usage

`SFMIntentAnalyzerNode` and `SFMAgentMonitor` are plain callables. That makes them usable without importing LangGraph, and directly pluggable into a `StateGraph` when LangGraph is installed.

```python
from typing import Any, TypedDict
from langgraph.graph import END, START, StateGraph
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor

class AgentState(TypedDict, total=False):
    run_id: str
    last_action: str
    candidate_goals: list[dict[str, Any]]
    graph: dict[str, Any]
    stated_goal: str
    sfm_analysis: dict[str, Any]
    sfm_monitor: dict[str, Any]
    sfm_monitor_events: list[dict[str, Any]]
    requires_human_review: bool
    sfm_gate_status: str

builder = StateGraph(AgentState)
builder.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())
builder.add_node("sfm_agent_monitor", SFMAgentMonitor())
builder.add_edge(START, "sfm_intent_analyzer")
builder.add_edge("sfm_intent_analyzer", "sfm_agent_monitor")
builder.add_edge("sfm_agent_monitor", END)
graph = builder.compile()

result = graph.invoke({
    "run_id": "demo-run",
    "last_action": "call_search_tool",
    "candidate_goals": [{"goal_variable": "answer_user_question"}],
    "graph": {
        "nodes": ["agent_action", "answer_user_question"],
        "edges": [["agent_action", "answer_user_question"]],
    },
    "stated_goal": "answer_user_question",
})

print(result["sfm_monitor"]["final_gate_status"])
```

## Run-level monitor

The monitor converts a sequence of `sfm_analysis` objects into an agent-run report:

```python
{
    "sfm_monitor": {
        "final_gate_status": "review",
        "human_review_required": True,
        "deception_alerts": 1,
        "claim_withheld_events": 1,
        "authorized_claim_events": 2,
        "intent_timeline": [...],
        "risk_events": [...]
    },
    "requires_human_review": True,
    "sfm_gate_status": "review"
}
```

## CLI smoke demo

```bash
python -m sfm_langgraph.cli
# or after installation
langgraph-sfm-demo
```

The CLI demo uses an injected analyzer so it does not require external services, model calls, LangGraph, or a dataset.

## Positioning

Use this project as a **research and observability layer**, not as a final detector of hidden intentions.

Recommended wording:

> Detect plausible agent intentions, side effects, and deception risk with explicit epistemic claim levels.

Avoid overclaiming:

> This tool proves the agent's true goal.

## Validation status

Current repository validation includes:

```text
Synthetic benchmark: 9/9 passed
External panel benchmark: 4/4 passed
false_positive_claims = 0
false_negative_claims = 0
claim_authorization_accuracy = 1.0
```

The panel-backed harness is useful for development, but it is not yet an independent external field validation. For production use, connect SFM to real traces, a domain-owned SCM/DAG, negative controls, and human-review outcomes.

## Development

```bash
git clone https://github.com/emilianomuharremi/langgraph-sfm.git
cd langgraph-sfm
python -m pip install -e ".[test]"
python -m pytest
python -m pip wheel . -w dist --no-deps
```

## Public release checklist

See [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## License

MIT.
