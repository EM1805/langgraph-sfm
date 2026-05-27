# SFM Step 27 — Agent Monitor for LangGraph Workflows

Step 27 turns the Step 26 SFM intent node into a run-level agent monitor.

The monitor is deliberately not another intent classifier. It preserves the SFM
claim-authority boundary by tracking:

- primary intent hypotheses;
- final-cause claim level;
- whether the claim was actually authorized;
- claim-withholding reasons;
- deception risk from stated-goal mismatch;
- side-effect and protected-outcome risk;
- human-review routing and final gate status.

## Package surface

```python
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor

analyzer = SFMIntentAnalyzerNode()
monitor = SFMAgentMonitor()

state.update(analyzer(state))
state.update(monitor(state))
```

Compatibility re-export:

```python
from amantia.integrations.langgraph_sfm import SFMAgentMonitor
```

## LangGraph shape

```python
from langgraph.graph import END, START, StateGraph
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor

builder = StateGraph(AgentState)
builder.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())
builder.add_node("sfm_agent_monitor", SFMAgentMonitor())
builder.add_edge(START, "sfm_intent_analyzer")
builder.add_edge("sfm_intent_analyzer", "sfm_agent_monitor")
builder.add_edge("sfm_agent_monitor", END)
graph = builder.compile()
```

A production graph can route from `sfm_agent_monitor` with a conditional edge:

- `allow` -> continue agent execution;
- `review` -> human-in-the-loop queue;
- `block` -> stop or safe fallback.

## Monitor output

The monitor reads `sfm_analysis` and returns a partial state update:

```python
{
    "sfm_monitor_events": [...],
    "sfm_monitor": {
        "run_id": "demo-agent-run",
        "total_events": 3,
        "final_gate_status": "review",
        "human_review_required": True,
        "deception_alerts": 1,
        "claim_withheld_events": 1,
        "authorized_claim_events": 2,
        "claim_level_counts": {...},
        "intent_timeline": [...],
        "risk_events": [...]
    },
    "requires_human_review": True,
    "sfm_gate_status": "review"
}
```

## Event taxonomy

The monitor emits one `SFMRiskEvent` for each SFM analysis step:

- `allow`: authorized low-risk event;
- `review`: gate already requires review;
- `claim_withheld`: SFM supports a hypothesis but refuses causal claim authority;
- `deception_alert`: stated goal differs from an SFM-supported primary intent;
- `side_effect_alert`: side effect or protected outcome risk is high;
- `blocked`: the SFM node or governance gate failed closed.

## Why this matters

A normal observability tool may say: “the agent appears to want X.”

The SFM monitor says: “the agent appears to pursue X, but the claim level is
`falsifiable_diagnostic`, the SCM graph is missing, and the run should be routed
to human review.”

That distinction is the product differentiator: agent observability with causal
and epistemic governance rather than unconstrained intent labeling.

## Validation added in Step 27

The Step 27 tests verify that:

1. authorized low-deception SFM analyses remain `allow`;
2. missing-graph diagnostics become reviewable `claim_withheld` events;
3. stated-goal mismatch escalates to `deception_alert` and human review;
4. multiple SFM steps accumulate into a run-level timeline;
5. precomputed events can be converted into a standalone report;
6. the monitor can be attached to a LangGraph-like builder without importing LangGraph.

Run:

```bash
python examples/langgraph_sfm_agent_monitor_demo.py
pytest tests/test_sfm_agent_monitor_step27.py
```
