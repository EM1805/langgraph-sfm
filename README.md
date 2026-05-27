# langgraph-sfm

**Causal intent monitoring for LangGraph agents using a bundled Structural Final Models core.**

`langgraph-sfm` adds an SFM intent-analysis node and run monitor to LangGraph-style agent workflows. This package now bundles the full relocated SFM core under a single `sfm/` package, so the default node uses the real core backend instead of a lightweight fallback.

## Install

```bash
pip install langgraph-sfm
# optional, only when running inside LangGraph itself
pip install "langgraph-sfm[langgraph]"
```

## Quickstart

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

print(state["sfm_analysis"])
print(state["sfm_monitor"])
```

## What is inside

```text
sfm_langgraph/   # LangGraph-compatible node, monitor and CLI
sfm/             # bundled full SFM core and its required support modules
tests/           # public smoke/contract tests
examples/        # quickstart examples
```

The bundled core keeps the public repository clean: instead of publishing many top-level internal packages (`amantia`, `runtime`, `scm_parts`, etc.), they live inside `sfm/`. A small compatibility bootstrap preserves the core's internal imports.

## LangGraph usage

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
    requires_human_review: bool
    sfm_gate_status: str

builder = StateGraph(AgentState)
builder.add_node("sfm_intent", SFMIntentAnalyzerNode())
builder.add_node("sfm_monitor", SFMAgentMonitor())
builder.add_edge(START, "sfm_intent")
builder.add_edge("sfm_intent", "sfm_monitor")
builder.add_edge("sfm_monitor", END)
graph = builder.compile()
```

## Epistemic boundary

This project is a research/observability layer. It does not prove an agent's “true goal”. It reports plausible intent hypotheses, side effects, deception-risk signals and the level at which a claim is authorized or withheld.

Recommended wording:

> Detect plausible agent intentions, side effects, and deception risk with explicit epistemic claim levels.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m sfm_langgraph.cli
python -m build
```

## License

MIT.
