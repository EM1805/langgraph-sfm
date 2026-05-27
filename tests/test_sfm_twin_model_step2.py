from amantia.causal_core.final import compare_twin_policies, infer_final_cause


def _graph():
    return {
        "nodes": ["agent_action", "task_success", "user_or_system_harm"],
        "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
    }


def test_twin_policy_detects_goal_dependent_action_switch():
    result = compare_twin_policies(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": [{"goal_variable": "task_success", "desired_direction": "increase"}],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_outcomes": {"task_success": 0.98},
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_outcomes": {"task_success": 0.70},
                    "risk": "none",
                    "harm_probability": 0.0,
                },
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    assert result["compared"] is True
    assert result["selected_with_goal"] == "answer_directly"
    assert result["selected_without_goal"] == "ask_clarification"
    assert result["action_changes_when_goal_removed"] is True
    assert "SFM_TWIN_REMOVING_GOAL_CHANGES_ACTION" in result["reason_codes"]


def test_final_cause_uses_twin_support_in_result():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": [{"goal_variable": "task_success", "desired_direction": "increase"}],
            "candidate_actions": [
                {
                    "action": "answer_directly",
                    "expected_outcomes": {"task_success": 0.98},
                    "expected_success": 0.98,
                    "risk": "low",
                    "harm_probability": 0.01,
                },
                {
                    "action": "ask_clarification",
                    "expected_outcomes": {"task_success": 0.70},
                    "expected_success": 0.70,
                    "risk": "none",
                    "harm_probability": 0.0,
                },
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    # Step 23 separates a plausible diagnostic hypothesis from an authorized
    # SFM claim. Twin evidence alone is strong but not enough for claim authority.
    assert result["intent_hypothesis_supported"] is True
    assert result["intent_claim_authorized"] is False
    assert result["inferred"] is False
    assert result["intent_score"] >= 0.8
    assert result["twin_support"]["selected_with_goal"] == "answer_directly"
    assert "SFM_TWIN_WITH_GOAL_SELECTS_OBSERVED" in result["reason_codes"]


def test_protected_side_effect_is_not_promoted_to_final_cause():
    result = infer_final_cause(
        {
            "observed_action": "risky_action",
            "action_variable": "agent_action",
            "candidate_goals": [
                {
                    "goal_variable": "user_or_system_harm",
                    "desired_direction": "increase",
                    "side_effect_outcomes": ["user_or_system_harm"],
                }
            ],
            "candidate_actions": [
                {"action": "risky_action", "harm_probability": 0.9, "risk": "high"},
                {"action": "safe_action", "harm_probability": 0.01, "risk": "none"},
            ],
            "scm_graph": _graph(),
            "protected_outcome": "user_or_system_harm",
        }
    )
    assert result["side_effects_excluded"] is False
    assert result["inferred"] is False
    assert result["intent_score"] < 0.6
    assert "SFM_GOAL_OVERLAPS_PROTECTED_OR_SIDE_EFFECT" in result["reason_codes"]
