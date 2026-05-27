from amantia.causal_core.final import evaluate_utility_function, infer_final_cause


def _graph():
    return {
        "nodes": ["agent_action", "task_success", "user_or_system_harm", "engagement_spike"],
        "edges": [
            ["agent_action", "task_success"],
            ["agent_action", "user_or_system_harm"],
            ["agent_action", "engagement_spike"],
        ],
    }


def test_explicit_utility_selects_observed_action_via_safety_tradeoff():
    audit = evaluate_utility_function(
        {
            "observed_action": "ask_clarification",
            "action_variable": "agent_action",
            "candidate_goals": [{"goal_variable": "task_success", "desired_direction": "increase"}],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_outcomes": {"task_success": 0.96, "user_or_system_harm": 0.80},
                    "risk": "high",
                    "harm_probability": 0.80,
                },
                {
                    "action": "ask_clarification",
                    "expected_outcomes": {"task_success": 0.78, "user_or_system_harm": 0.02},
                    "risk": "low",
                    "harm_probability": 0.02,
                },
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    assert audit["assessed"] is True
    assert audit["selected_action"] == "ask_clarification"
    assert audit["selected_action_matches_observed"] is True
    assert audit["tradeoff_detected"] is True
    assert audit["rankings"][0]["protected_penalty"] < audit["rankings"][1]["protected_penalty"]
    assert "SFM_UTILITY_TRADEOFF_DETECTED" in audit["reason_codes"]
    assert "SFM_UTILITY_PROTECTED_CONSTRAINTS_INCLUDED" in audit["reason_codes"]


def test_final_cause_result_contains_utility_support():
    result = infer_final_cause(
        {
            "observed_action": "ask_clarification",
            "action_variable": "agent_action",
            "candidate_goals": [{"goal_variable": "task_success", "desired_direction": "increase"}],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_outcomes": {"task_success": 0.96, "user_or_system_harm": 0.80},
                    "expected_success": 0.96,
                    "risk": "high",
                    "harm_probability": 0.80,
                },
                {
                    "action": "ask_clarification",
                    "expected_outcomes": {"task_success": 0.78, "user_or_system_harm": 0.02},
                    "expected_success": 0.78,
                    "risk": "low",
                    "harm_probability": 0.02,
                },
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    assert result["utility_support"]["assessed"] is True
    assert result["utility_support"]["selected_action"] == "ask_clarification"
    assert "SFM_UTILITY_SUPPORTS_OBSERVED_ACTION" in result["reason_codes"]
    assert result["intent_score"] >= 0.6


def test_side_effect_is_monitored_but_not_automatically_optimized_as_goal():
    audit = evaluate_utility_function(
        {
            "observed_action": "ask_clarification",
            "action_variable": "agent_action",
            "candidate_goals": [
                {
                    "goal_variable": "task_success",
                    "desired_direction": "increase",
                    "side_effect_outcomes": ["engagement_spike"],
                }
            ],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_outcomes": {
                        "task_success": 0.70,
                        "user_or_system_harm": 0.01,
                        "engagement_spike": 0.99,
                    },
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_outcomes": {
                        "task_success": 0.82,
                        "user_or_system_harm": 0.01,
                        "engagement_spike": 0.10,
                    },
                    "risk": "low",
                    "harm_probability": 0.01,
                },
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    side_components = [c for c in audit["utility_components"] if c["role"] == "side_effect"]
    assert side_components
    assert side_components[0]["outcome"] == "engagement_spike"
    assert side_components[0]["active"] is False
    assert audit["side_effect_weight"] == 0.0
    assert audit["selected_action"] == "ask_clarification"
    assert "SFM_UTILITY_SIDE_EFFECTS_MONITORED_NOT_AUTOMATIC_GOALS" in audit["reason_codes"]
