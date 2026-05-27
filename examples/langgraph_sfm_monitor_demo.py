from __future__ import annotations

"""Minimal SFM + LangGraph monitor demo.

Run without LangGraph installed:
    python examples/langgraph_sfm_monitor_demo.py

Run with LangGraph installed to see the same node inside StateGraph:
    pip install langgraph
    python examples/langgraph_sfm_monitor_demo.py --langgraph
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sfm_langgraph import SFMIntentAnalyzerConfig, SFMIntentAnalyzerNode
from amantia.causal_core.final import build_external_sfm_panel_cases

PANEL = ROOT / "data" / "action_event_panel.csv"


class AgentState(TypedDict, total=False):
    sfm_query: Dict[str, Any]
    stated_goal: str
    sfm_analysis: Dict[str, Any]
    sfm_trace_events: list[Dict[str, Any]]


def build_demo_state() -> AgentState:
    case = next(
        item
        for item in build_external_sfm_panel_cases(str(PANEL))
        if item.name == "panel_throughput_claim_authorized_with_domain_graph"
    )
    return {
        "sfm_query": case.payload,
        "stated_goal": "task_throughput",
    }


def run_plain_callable() -> Dict[str, Any]:
    node = SFMIntentAnalyzerNode(SFMIntentAnalyzerConfig(include_raw_result=False))
    return node(build_demo_state())


def run_langgraph() -> Dict[str, Any]:
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # pragma: no cover - optional dependency example
        raise RuntimeError("Install langgraph to run this branch: pip install langgraph") from exc

    builder = StateGraph(AgentState)
    builder.add_node("sfm_intent_analyzer", SFMIntentAnalyzerNode())
    builder.add_edge(START, "sfm_intent_analyzer")
    builder.add_edge("sfm_intent_analyzer", END)
    graph = builder.compile()
    return graph.invoke(build_demo_state())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--langgraph", action="store_true", help="execute inside LangGraph StateGraph")
    args = parser.parse_args()
    output = run_langgraph() if args.langgraph else run_plain_callable()
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
