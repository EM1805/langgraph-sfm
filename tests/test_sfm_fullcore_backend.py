from __future__ import annotations

from sfm import infer_final_cause_compact
from sfm_langgraph import SFMIntentAnalyzerNode


def _state():
    return {
        "run_id": "full-core-smoke",
        "last_action": "call_search_tool",
        "candidate_goals": [{"goal_variable": "answer_user_question"}],
        "graph": {
            "nodes": ["agent_action", "answer_user_question"],
            "edges": [["agent_action", "answer_user_question"]],
        },
        "stated_goal": "answer_user_question",
    }


def test_full_core_compact_inference_is_packaged():
    result = infer_final_cause_compact({
        "observed_action": "call_search_tool",
        "candidate_goals": [{"goal_variable": "answer_user_question"}],
        "scm_graph": {
            "nodes": ["agent_action", "answer_user_question"],
            "edges": [["agent_action", "answer_user_question"]],
        },
        "protected_outcome": "user_or_system_harm",
    })
    assert isinstance(result, dict)
    assert result["most_likely_goal"] == "answer_user_question"
    assert "reason_codes" in result


def test_langgraph_node_uses_bundled_full_core_by_default():
    update = SFMIntentAnalyzerNode()(_state())
    analysis = update["sfm_analysis"]
    assert analysis["primary_intent"] == "answer_user_question"
    assert analysis["observed_action"] == "call_search_tool"
    assert "SFM_EXECUTION_PROFILE_FULL" in analysis["reason_codes"]
