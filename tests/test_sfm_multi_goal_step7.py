from amantia.causal_core.final import evaluate_multi_goal_utility, infer_final_cause


def _graph():
    return {
        "nodes": ["agent_action", "task_success", "user_satisfaction", "user_or_system_harm"],
        "edges": [
            ["agent_action", "task_success"],
            ["agent_action", "user_satisfaction"],
            ["agent_action", "user_or_system_harm"],
        ],
    }


def _payload():
    return {
        "observed_action": "balanced_policy",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0},
            {"goal_variable": "user_satisfaction", "desired_direction": "increase", "utility_weight": 1.0},
        ],
        "candidate_actions": [
            {
                "action": "maximize_task_success",
                "expected_outcomes": {
                    "task_success": 0.95,
                    "user_satisfaction": 0.20,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
            {
                "action": "maximize_user_satisfaction",
                "expected_outcomes": {
                    "task_success": 0.20,
                    "user_satisfaction": 0.95,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
            {
                "action": "balanced_policy",
                "expected_outcomes": {
                    "task_success": 0.75,
                    "user_satisfaction": 0.75,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "protected_outcome": "user_or_system_harm",
        "scm_graph": _graph(),
    }


def test_multi_goal_utility_selects_observed_balanced_policy():
    audit = evaluate_multi_goal_utility(_payload())
    assert audit["assessed"] is True
    assert audit["goal_bundle"] == ["task_success", "user_satisfaction"]
    assert audit["selected_action"] == "balanced_policy"
    assert audit["selected_action_matches_observed"] is True
    assert audit["observed_rank"] == 1
    assert audit["tradeoff_detected"] is True
    assert audit["bundle_score_exceeds_best_single_goal_score"] is True
    assert audit["best_single_goal_actions"] == {
        "task_success": "maximize_task_success",
        "user_satisfaction": "maximize_user_satisfaction",
    }
    assert "SFM_MULTI_GOAL_SUPPORTS_OBSERVED_ACTION" in audit["reason_codes"]
    assert "SFM_MULTI_GOAL_BUNDLE_EXPLAINS_MORE_THAN_SINGLE_GOAL" in audit["reason_codes"]


def test_final_cause_result_contains_multi_goal_support():
    result = infer_final_cause(_payload())
    assert result["multi_goal_support"]["assessed"] is True
    assert result["multi_goal_support"]["selected_action"] == "balanced_policy"
    assert result["multi_goal_support"]["selected_action_matches_observed"] is True
    assert "SFM_MULTI_GOAL_SUPPORTS_OBSERVED_ACTION" in result["reason_codes"]
