from amantia.causal_core.final import evaluate_constraint_aware_sfm, infer_final_cause


def _constraint_payload():
    return {
        "observed_action": "ask_clarification",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0}
        ],
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_outcomes": {
                    "task_success": 0.95,
                    "user_or_system_harm": 0.30,
                    "latency": 0.10,
                },
                "risk": "high",
                "harm_probability": 0.30,
            },
            {
                "action": "ask_clarification",
                "expected_outcomes": {
                    "task_success": 0.82,
                    "user_or_system_harm": 0.02,
                    "latency": 0.35,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "constraints": {
            "hard": [
                {"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}
            ],
            "soft": [
                {"outcome": "latency", "direction": "decrease", "threshold": 0.40, "weight": 0.2}
            ],
            "side_effects": ["latency"],
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm", "latency"],
            "edges": [
                ["agent_action", "task_success"],
                ["agent_action", "user_or_system_harm"],
                ["agent_action", "latency"],
            ],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_or_system_harm", "latency"],
                "edges": [
                    ["agent_action", "task_success"],
                    ["agent_action", "user_or_system_harm"],
                    ["agent_action", "latency"],
                ],
            },
            "utility_model": {"task_success": 1.0, "user_or_system_harm": -2.0, "latency": -0.2},
        },
    }


def test_constraint_aware_sfm_selects_action_under_hard_constraints():
    audit = evaluate_constraint_aware_sfm(_constraint_payload())
    assert audit["assessed"] is True
    assert audit["selected_action"] == "ask_clarification"
    assert audit["selected_action_matches_observed"] is True
    assert audit["observed_feasible"] is True
    assert audit["feasible_actions"] == ["ask_clarification"]
    assert audit["infeasible_actions"] == ["answer_directly"]
    assert audit["tradeoff_under_constraints"] is True
    assert "SFM_CONSTRAINTS_CHANGE_UNCONSTRAINED_ACTION_CHOICE" in audit["reason_codes"]
    assert "SFM_PROTECTED_OUTCOMES_TREATED_AS_CONSTRAINTS" in audit["reason_codes"]


def test_constraint_aware_sfm_is_integrated_into_final_cause_result():
    result = infer_final_cause(_constraint_payload())
    constraint = result["constraint_support"]
    assert constraint["assessed"] is True
    assert constraint["selected_action"] == "ask_clarification"
    assert constraint["selected_action_matches_observed"] is True
    assert result["most_likely_goal"] == "task_success"
    assert "SFM_CONSTRAINT_AWARE_SUPPORTS_OBSERVED_ACTION" in result["reason_codes"]
    assert "SFM_CONSTRAINT_AWARE_POLICY_SUPPORTS_OBSERVED_ACTION" in result["reason_codes"]


def test_constraint_aware_sfm_does_not_promote_protected_outcome_to_final_goal():
    payload = _constraint_payload()
    payload["candidate_goals"] = [
        {"goal_variable": "user_or_system_harm", "desired_direction": "decrease", "utility_weight": 1.0}
    ]
    result = infer_final_cause(payload)
    constraint = result["constraint_support"]
    assert constraint["constraint_like_candidate_goals"] == ["user_or_system_harm"]
    assert constraint["final_goals"] == []
    assert result["side_effects_excluded"] is False
    assert result["inferred"] is False
    assert result["intent_score"] <= 0.49
    assert "SFM_CANDIDATE_GOAL_CLASSIFIED_AS_CONSTRAINT_NOT_FINAL_GOAL" in result["reason_codes"]
    assert "candidate_goal_classified_as_constraint_or_side_effect_not_final_goal" in result["limits"]
