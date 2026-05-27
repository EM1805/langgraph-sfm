from amantia.causal_core.final import evaluate_empirical_utility, infer_final_cause


def _graph():
    return {
        "nodes": ["agent_action", "task_success", "user_or_system_harm"],
        "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
    }


def _payload():
    return {
        "observed_action": "ask_clarification",
        "action_variable": "agent_action",
        "candidate_goals": [{"goal_variable": "task_success", "desired_direction": "increase"}],
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_outcomes": {"task_success": 0.72, "user_or_system_harm": 0.10},
                "expected_success": 0.72,
                "risk": "medium",
                "harm_probability": 0.10,
            },
            {
                "action": "ask_clarification",
                "expected_outcomes": {"task_success": 0.78, "user_or_system_harm": 0.01},
                "expected_success": 0.78,
                "risk": "low",
                "harm_probability": 0.01,
            },
        ],
        "outcome_records": [
            {"selected_action": "ask_clarification", "success": True, "harm": False, "user_satisfaction": 4.5},
            {"selected_action": "ask_clarification", "success": True, "harm": False, "user_satisfaction": 5.0},
            {"selected_action": "ask_clarification", "success": True, "harm": False, "user_satisfaction": 4.0},
            {"selected_action": "answer_directly", "success": True, "harm": True, "user_satisfaction": 2.0},
            {"selected_action": "answer_directly", "success": False, "harm": False, "user_satisfaction": 2.5},
            {"selected_action": "answer_directly", "success": False, "harm": False, "user_satisfaction": 3.0},
        ],
        "min_empirical_records_per_action": 2,
        "scm_graph": _graph(),
        "protected_outcome": "user_or_system_harm",
    }


def test_empirical_utility_learns_implicit_preference_from_outcomes():
    audit = evaluate_empirical_utility(_payload())
    assert audit["assessed"] is True
    assert audit["selected_action"] == "ask_clarification"
    assert audit["selected_action_matches_observed"] is True
    assert audit["observed_rank"] == 1
    assert audit["support_strength"] > 0.55
    assert "SFM_EMPIRICAL_UTILITY_SUPPORTS_OBSERVED_ACTION" in audit["reason_codes"]


def test_empirical_utility_reports_insufficient_evidence_without_records():
    payload = dict(_payload())
    payload.pop("outcome_records")
    audit = evaluate_empirical_utility(payload)
    assert audit["assessed"] is False
    assert "SFM_EMPIRICAL_UTILITY_NO_OUTCOME_RECORDS" in audit["reason_codes"]
    assert "outcome_records_or_outcome_log_path_required" in audit["limits"]


def test_final_cause_result_contains_empirical_utility_support():
    result = infer_final_cause(_payload())
    assert result["empirical_utility_support"]["assessed"] is True
    assert result["empirical_utility_support"]["selected_action"] == "ask_clarification"
    assert "SFM_EMPIRICAL_UTILITY_SUPPORTS_OBSERVED_ACTION" in result["reason_codes"]
    assert result["intent_score"] >= 0.7
