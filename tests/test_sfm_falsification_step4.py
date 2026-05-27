from amantia.causal_core.final import audit_sfm_falsification, infer_final_cause


def _graph():
    return {
        "nodes": ["agent_action", "task_success", "unrelated_metric", "engagement_spike"],
        "edges": [["agent_action", "task_success"], ["agent_action", "engagement_spike"]],
    }


def test_negative_control_goal_failure_penalizes_intent_inference():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "negative_control_goals": ["unrelated_metric"],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_success": 0.95,
                    "expected_outcomes": {"task_success": 0.95, "unrelated_metric": 0.97},
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_success": 0.60,
                    "expected_outcomes": {"task_success": 0.60, "unrelated_metric": 0.55},
                    "risk": "none",
                    "harm_probability": 0.0,
                },
            ],
            "scm_graph": _graph(),
        }
    )
    assert result["falsification_passed"] is False
    assert result["falsification_support"]["falsified"] is True
    assert result["inferred"] is False
    assert result["intent_score"] < 0.6
    assert "SFM_FALSIFICATION_FAILED" in result["reason_codes"]
    assert "sfm_falsification_failed" in result["limits"]


def test_negative_control_goal_can_pass_when_it_does_not_explain_observed_action():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "negative_control_goals": ["unrelated_metric"],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_success": 0.95,
                    "expected_outcomes": {"task_success": 0.95, "unrelated_metric": 0.20},
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_success": 0.60,
                    "expected_outcomes": {"task_success": 0.60, "unrelated_metric": 0.90},
                    "risk": "none",
                    "harm_probability": 0.0,
                },
            ],
            "scm_graph": _graph(),
        }
    )
    assert result["falsification_passed"] is True
    assert result["falsification_support"]["passed"] is True
    assert result["inferred"] is True
    assert "SFM_FALSIFICATION_PASSED" in result["reason_codes"]


def test_placebo_goal_audit_reports_unassessable_when_measurement_is_missing():
    report = audit_sfm_falsification(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "placebo_goals": ["fake_placebo_goal"],
            "candidate_actions": [
                {"action": "answer_directly", "expected_success": 0.95, "risk": "low", "harm_probability": 0.01},
                {"action": "ask_clarification", "expected_success": 0.60, "risk": "none", "harm_probability": 0.0},
            ],
            "scm_graph": _graph(),
        }
    )
    assert report["passed"] is True
    assert report["unassessable_checks"]
    assert "SFM_FALSIFICATION_HAS_UNASSESSABLE_CONTROLS" in report["reason_codes"]


def test_side_effect_goal_ambiguity_blocks_final_cause_claim():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "side_effect_goals": ["engagement_spike"],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_success": 0.95,
                    "expected_outcomes": {"task_success": 0.95, "engagement_spike": 0.99},
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_success": 0.60,
                    "expected_outcomes": {"task_success": 0.60, "engagement_spike": 0.50},
                    "risk": "none",
                    "harm_probability": 0.0,
                },
            ],
            "scm_graph": _graph(),
        }
    )
    assert result["falsification_passed"] is False
    assert result["inferred"] is False
    assert "SFM_SIDE_EFFECT_GOAL_AMBIGUITY" in str(result["falsification_support"])
