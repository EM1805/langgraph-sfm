from amantia.causal_core.final import (
    infer_final_cause,
    infer_final_cause_compact,
    render_sfm_audit_report,
    resolve_sfm_execution_plan,
)


def _payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
        "candidate_actions": [
            {
                "action": "safe_answer",
                "expected_outcomes": {"task_success": 0.9, "user_or_system_harm": 0.02},
                "risk": "low",
                "harm_probability": 0.02,
                "uncertainty": 0.02,
                "evidence_quality": "high",
            },
            {
                "action": "careful_answer",
                "expected_outcomes": {"task_success": 0.78, "user_or_system_harm": 0.01},
                "risk": "low",
                "harm_probability": 0.01,
                "uncertainty": 0.03,
                "evidence_quality": "high",
            },
        ],
        "constraints": {"hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]},
        "normative_policy": {
            "allowed_goals": ["task_success"],
            "allowed_actions": ["safe_answer", "careful_answer"],
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm"],
            "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_or_system_harm"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
            },
            "utility_model": {"task_success": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_report_layer_is_integrated_into_final_cause_result():
    result = infer_final_cause(_payload())
    report = result["audit_report"]
    assert report["generated"] is True
    assert report["format"] == "markdown"
    assert report["goal_variable"] == "task_success"
    assert "SFM Audit Report" in report["markdown"]
    assert "Executive summary" in report["markdown"]
    assert report["machine_summary"]["gate_status"] == result["alignment_summary"]["gate_status"]


def test_standalone_report_helper_accepts_sfm_result_dict():
    result = infer_final_cause(_payload())
    report = render_sfm_audit_report(result)
    assert report["generated"] is True
    assert report["verdict"] == result["alignment_summary"]["verdict"]
    assert report["sections"]
    assert report["raw"] == {}


def test_report_layer_can_be_selected_by_alias():
    plan = resolve_sfm_execution_plan({"enabled_layers": ["id", "cf", "summary", "report"]})
    assert "audit_report" in plan["enabled_layers"]
    assert "alignment_summary" in plan["enabled_layers"]


def test_compact_result_exposes_report_summary_and_markdown():
    compact = infer_final_cause_compact(_payload())
    assert "Observed action" in compact["audit_report_summary"]
    assert "# SFM Audit Report" in compact["audit_report_markdown"]
