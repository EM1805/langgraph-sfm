from __future__ import annotations

"""SFM Agent Monitor demo for LangGraph-style workflows.

Run without LangGraph installed:
    python examples/langgraph_sfm_agent_monitor_demo.py

Run with LangGraph installed:
    pip install langgraph
    python examples/langgraph_sfm_agent_monitor_demo.py --langgraph
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from amantia.causal_core.final import build_external_sfm_panel_cases
from sfm_langgraph import SFMAgentMonitor, SFMIntentAnalyzerNode

PANEL = ROOT / "data" / "action_event_panel.csv"


class AgentState(TypedDict, total=False):
    run_id: str
    sfm_query: Dict[str, Any]
    stated_goal: str
    sfm_analysis: Dict[str, Any]
    sfm_trace_events: list[Dict[str, Any]]
    sfm_monitor_events: list[Dict[str, Any]]
    sfm_monitor: Dict[str, Any]
    requires_human_review: bool
    sfm_gate_status: str


def _case(name: str):
    return next(item for item in build_external_sfm_panel_cases(str(PANEL)) if item.name == name)


def build_demo_states() -> list[AgentState]:
    positive = _case("panel_throughput_claim_authorized_with_domain_graph")
    missing_graph = _case("panel_missing_graph_withholds_claim_authority")
    return [
        {"run_id": "demo-agent-run", "sfm_query": positive.payload, "stated_goal": "task_throughput"},
        {"run_id": "demo-agent-run", "sfm_query": missing_graph.payload, "stated_goal": "task_throughput"},
        {"run_id": "demo-agent-run", "sfm_query": positive.payload, "stated_goal": "audit_noise"},
    ]


def run_plain_callable() -> Dict[str, Any]:
    analyzer = SFMIntentAnalyzerNode()
    monitor = SFMAgentMonitor()
    state: Dict[str, Any] = {}
    for step in build_demo_states():
        state.update(step)
        state.update(analyzer(state))
        state.update(monitor(state))
    return {
        "sfm_gate_status": state["sfm_gate_status"],
        "requires_human_review": state["requires_human_review"],
        "sfm_monitor": state["sfm_monitor"],
    }


def run_langgraph() -> Dict[str, Any]:
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # pragma: no cover - optional dependency example
        raise RuntimeError("Install langgraph to run this branch: pip install langgraph") from exc

    builder = StateGraph(AgentState)
    builder.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())
    builder.add_node("sfm_agent_monitor", SFMAgentMonitor())
    builder.add_edge(START, "sfm_intent_analyzer")
    builder.add_edge("sfm_intent_analyzer", "sfm_agent_monitor")
    builder.add_edge("sfm_agent_monitor", END)
    graph = builder.compile()

    state: AgentState = {}
    for step in build_demo_states():
        state.update(step)
        state = graph.invoke(state)
    return {
        "sfm_gate_status": state["sfm_gate_status"],
        "requires_human_review": state["requires_human_review"],
        "sfm_monitor": state["sfm_monitor"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--langgraph", action="store_true", help="execute analyzer + monitor inside LangGraph StateGraph")
    args = parser.parse_args()
    output = run_langgraph() if args.langgraph else run_plain_callable()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
