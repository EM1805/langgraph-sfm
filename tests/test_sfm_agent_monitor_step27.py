from pathlib import Path

from sfm.amantia.causal_core.final import build_external_sfm_panel_cases
from sfm_langgraph import (
    SFMAgentMonitor,
    SFMIntentAnalyzerNode,
    add_sfm_agent_monitor_node,
    build_sfm_agent_monitor,
    build_sfm_run_report,
)


PANEL_PATH = Path(__file__).resolve().parents[1] / "sfm" / "data" / "action_event_panel.csv"


def _panel_case(name: str):
    cases = build_external_sfm_panel_cases(str(PANEL_PATH))
    return next(case for case in cases if case.name == name)


def _analysis_for(case_name: str, stated_goal: str = "task_throughput"):
    node = SFMIntentAnalyzerNode()
    update = node({"sfm_query": _panel_case(case_name).payload, "stated_goal": stated_goal})
    return update["sfm_analysis"]


def test_sfm_agent_monitor_emits_allow_report_for_authorized_low_deception_case():
    analysis = _analysis_for("panel_throughput_claim_authorized_with_domain_graph")
    monitor = SFMAgentMonitor()
    update = monitor({"run_id": "run-1", "sfm_analysis": analysis})

    assert set(update) == {"sfm_monitor_events", "sfm_monitor", "requires_human_review", "sfm_gate_status"}
    assert update["sfm_gate_status"] == "allow"
    assert update["requires_human_review"] is False
    report = update["sfm_monitor"]
    assert report["run_id"] == "run-1"
    assert report["total_events"] == 1
    assert report["authorized_claim_events"] == 1
    assert report["claim_withheld_events"] == 0
    assert report["final_gate_status"] == "allow"
    assert report["intent_timeline"][0]["primary_intent"] == "task_throughput"


def test_sfm_agent_monitor_routes_missing_graph_diagnostic_to_review():
    analysis = _analysis_for("panel_missing_graph_withholds_claim_authority")
    monitor = build_sfm_agent_monitor()
    update = monitor({"run_id": "run-2", "sfm_analysis": analysis})
    event = update["sfm_monitor_events"][-1]

    assert event["event_type"] == "claim_withheld"
    assert event["requires_human_review"] is True
    assert event["blocked_claim_reason"] == "missing validated SCM graph"
    assert update["sfm_gate_status"] == "review"
    assert update["sfm_monitor"]["claim_withheld_events"] == 1


def test_sfm_agent_monitor_escalates_stated_goal_mismatch_to_human_review():
    analysis = _analysis_for(
        "panel_throughput_claim_authorized_with_domain_graph",
        stated_goal="audit_noise",
    )
    update = SFMAgentMonitor()({"run_id": "run-3", "sfm_analysis": analysis})

    assert update["sfm_gate_status"] == "review"
    assert update["requires_human_review"] is True
    event = update["sfm_monitor_events"][-1]
    assert event["event_type"] == "deception_alert"
    assert event["deception_risk"] == "high"
    assert event["risk_score"] >= 0.5
    assert update["sfm_monitor"]["deception_alerts"] == 1


def test_sfm_agent_monitor_accumulates_timeline_across_multiple_agent_steps():
    monitor = SFMAgentMonitor()
    first = monitor({"run_id": "run-4", "sfm_analysis": _analysis_for("panel_throughput_claim_authorized_with_domain_graph")})
    second = monitor(
        {
            "run_id": "run-4",
            "sfm_monitor_events": first["sfm_monitor_events"],
            "sfm_analysis": _analysis_for("panel_missing_graph_withholds_claim_authority"),
        }
    )

    report = second["sfm_monitor"]
    assert report["total_events"] == 2
    assert report["authorized_claim_events"] == 1
    assert report["claim_withheld_events"] == 1
    assert report["final_gate_status"] == "review"
    assert [row["step_index"] for row in report["intent_timeline"]] == [1, 2]


def test_build_sfm_run_report_handles_precomputed_monitor_events():
    events = [
        {
            "step_index": 1,
            "event_type": "allow",
            "primary_intent": "task_throughput",
            "claim_level": "strong_diagnostic_sfm_support",
            "intent_claim_authorized": True,
            "risk_score": 0.15,
            "requires_human_review": False,
            "gate_status": "allow",
        },
        {
            "step_index": 2,
            "event_type": "deception_alert",
            "primary_intent": "hidden_goal",
            "claim_level": "strong_diagnostic_sfm_support",
            "intent_claim_authorized": True,
            "deception_risk": "high",
            "risk_score": 0.65,
            "requires_human_review": True,
            "gate_status": "allow",
        },
    ]
    report = build_sfm_run_report(events, run_id="run-5")

    assert report["run_id"] == "run-5"
    assert report["total_events"] == 2
    assert report["human_review_required"] is True
    assert report["final_gate_status"] == "review"
    assert report["high_risk_events"] == 1
    assert report["claim_level_counts"]["strong_diagnostic_sfm_support"] == 2


def test_add_sfm_agent_monitor_node_works_with_langgraph_like_builder():
    class FakeBuilder:
        def __init__(self):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

    builder = FakeBuilder()
    node = add_sfm_agent_monitor_node(builder, name="sfm_monitor")

    assert builder.nodes["sfm_monitor"] is node
    assert callable(builder.nodes["sfm_monitor"])
