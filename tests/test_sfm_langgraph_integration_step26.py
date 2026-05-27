from pathlib import Path

from amantia.causal_core.final import build_external_sfm_panel_cases
from sfm_langgraph import (
    SFMIntentAnalyzerConfig,
    SFMIntentAnalyzerNode,
    add_sfm_intent_analyzer_node,
    build_sfm_intent_analyzer_node,
)


PANEL_PATH = Path(__file__).resolve().parents[1] / "data" / "action_event_panel.csv"


def _panel_case(name: str):
    cases = build_external_sfm_panel_cases(str(PANEL_PATH))
    return next(case for case in cases if case.name == name)


def test_sfm_langgraph_node_returns_partial_state_update_for_authorized_panel_case():
    case = _panel_case("panel_throughput_claim_authorized_with_domain_graph")
    node = SFMIntentAnalyzerNode(SFMIntentAnalyzerConfig(include_raw_result=True))
    update = node({"sfm_query": case.payload, "stated_goal": "task_throughput"})

    assert set(update) == {"sfm_analysis", "sfm_trace_events"}
    analysis = update["sfm_analysis"]
    assert analysis["primary_intent"] == "task_throughput"
    assert analysis["intentionality_score"] == 1.0
    assert analysis["intent_claim_authorized"] is True
    assert analysis["final_cause_claim_level"] == "strong_diagnostic_sfm_support"
    assert analysis["gate_status"] == "allow"
    assert analysis["deception_risk"] == "low"
    assert analysis["raw_result"]["most_likely_goal"] == "task_throughput"
    assert update["sfm_trace_events"][-1]["claim_level"] == "strong_diagnostic_sfm_support"


def test_sfm_langgraph_node_withholds_claim_when_domain_graph_is_missing():
    case = _panel_case("panel_missing_graph_withholds_claim_authority")
    node = build_sfm_intent_analyzer_node()
    update = node({"sfm_query": case.payload})
    analysis = update["sfm_analysis"]

    assert analysis["primary_intent"] == "task_throughput"
    assert analysis["intent_hypothesis_supported"] is True
    assert analysis["intent_claim_authorized"] is False
    assert analysis["final_cause_claim_level"] == "falsifiable_diagnostic"
    assert analysis["blocked_claim_reason"] == "missing validated SCM graph"
    assert analysis["raw_result"] == {}


def test_sfm_langgraph_node_flags_stated_goal_mismatch_as_deception_risk():
    case = _panel_case("panel_throughput_claim_authorized_with_domain_graph")
    node = SFMIntentAnalyzerNode()
    update = node({"sfm_query": case.payload, "declared_goal": "audit_noise"})
    analysis = update["sfm_analysis"]

    assert analysis["primary_intent"] == "task_throughput"
    assert analysis["deception_risk"] == "high"
    assert "audit_noise" in analysis["deception_rationale"]


def test_sfm_langgraph_node_can_build_query_from_common_state_keys_with_injected_analyzer():
    captured = {}

    def fake_analyzer(query):
        captured.update(query)
        return {
            "intent_hypothesis_supported": True,
            "intent_claim_authorized": False,
            "most_likely_goal": "task_success",
            "observed_action": query["observed_action"],
            "intent_score": 0.74,
            "authority_status": "falsifiable_diagnostic_only",
            "alignment_summary": {"gate_status": "review"},
            "reason_codes": ["SFM_TEST_REASON"],
            "limits": [],
        }

    node = SFMIntentAnalyzerNode(analyzer=fake_analyzer)
    update = node(
        {
            "last_action": "ask_clarification",
            "candidate_actions": ["answer_directly", "ask_clarification"],
            "goals": [{"goal_variable": "task_success"}],
            "graph": {"nodes": ["agent_action", "task_success"], "edges": [["agent_action", "task_success"]]},
            "user_goal": "task_success",
        }
    )

    assert captured["observed_action"] == "ask_clarification"
    assert captured["candidate_goals"] == [{"goal_variable": "task_success"}]
    assert captured["scm_graph"]["edges"] == [["agent_action", "task_success"]]
    assert update["sfm_analysis"]["primary_intent"] == "task_success"
    assert update["sfm_analysis"]["final_cause_claim_level"] == "falsifiable_diagnostic"


def test_add_sfm_intent_analyzer_node_works_with_langgraph_like_builder():
    class FakeBuilder:
        def __init__(self):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

    builder = FakeBuilder()
    node = add_sfm_intent_analyzer_node(builder, name="sfm")

    assert builder.nodes["sfm"] is node
    assert callable(builder.nodes["sfm"])
