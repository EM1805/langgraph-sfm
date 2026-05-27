from __future__ import annotations

"""Public quickstart for langgraph-sfm.

This example is intentionally runnable without LangGraph installed.  The same
callables can be passed to a LangGraph StateGraph via builder.add_node(...).
"""

from typing import Any, Dict

from sfm_langgraph import SFMAgentMonitor, SFMIntentAnalyzerConfig, SFMIntentAnalyzerNode


def demo_analyzer(query: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "observed_action": query.get("observed_action", "call_search_tool"),
        "most_likely_goal": "answer_user_question",
        "intent_score": 0.82,
        "intent_hypothesis_supported": True,
        "intent_claim_authorized": False,
        "authority_status": "falsifiable_diagnostic_only",
        "governance_execution_allowed": False,
        "alignment_summary": {"gate_status": "review"},
        "reason_codes": ["SFM_EXAMPLE_MISSING_VALIDATED_SCM_GRAPH"],
        "limits": ["Example analyzer only. Plug in real SFM payloads for production."],
    }


state = {
    "run_id": "quickstart-run",
    "last_action": "call_search_tool",
    "candidate_goals": [{"goal_variable": "answer_user_question"}],
    "graph": {
        "nodes": ["agent_action", "answer_user_question"],
        "edges": [["agent_action", "answer_user_question"]],
    },
    "stated_goal": "answer_user_question",
}

analyzer = SFMIntentAnalyzerNode(SFMIntentAnalyzerConfig(include_raw_result=False), analyzer=demo_analyzer)
monitor = SFMAgentMonitor()

state.update(analyzer(state))
state.update(monitor(state))

print(state["sfm_analysis"])
print(state["sfm_monitor"])
