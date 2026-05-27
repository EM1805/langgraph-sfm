from amantia.causal_core.final import evaluate_do_star_intervention, infer_final_cause


def _payload():
    return {
        "observed_action": "balanced_policy",
        "action_variable": "agent_action",
        "policy_name": "safety_weighted_goal_policy",
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_satisfaction", "user_or_system_harm"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_satisfaction"]],
            },
            "utility_model": {"latency": 0.1},
        },
        "state": {"ambiguity": "high"},
        "goal_bundle": [
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
                    "latency": 0.30,
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
                    "latency": 0.20,
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
                    "latency": 0.20,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_satisfaction", "user_or_system_harm"],
            "edges": [
                ["agent_action", "task_success"],
                ["agent_action", "user_satisfaction"],
                ["agent_action", "user_or_system_harm"],
            ],
        },
    }


def test_do_star_operator_serializes_policy_signature_and_selects_observed_action():
    audit = evaluate_do_star_intervention(_payload())
    assert audit["evaluated"] is True
    assert audit["operator"] == "do_star"
    assert audit["policy_signature"] == "policy(S, B, G_bundle, U)"
    assert audit["policy_name"] == "safety_weighted_goal_policy"
    assert audit["selected_action"] == "balanced_policy"
    assert audit["selected_action_matches_observed"] is True
    assert audit["goal_bundle"] == ["task_success", "user_satisfaction"]
    assert audit["policy_inputs"]["belief_graph_supplied"] is True
    assert audit["policy_inputs"]["utility_model_supplied"] is True
    assert audit["expression"].startswith("do*(agent_action=pi_safety_weighted_goal_policy")
    assert "SFM_DO_STAR_OPERATOR_EVALUATED" in audit["reason_codes"]
    assert "SFM_DO_STAR_SELECTS_OBSERVED_ACTION" in audit["reason_codes"]


def test_final_cause_result_contains_formal_do_star_support():
    result = infer_final_cause(_payload())
    assert result["do_star_support"]["evaluated"] is True
    assert result["do_star_support"]["selected_action"] == "balanced_policy"
    assert result["do_star_support"]["selected_action_matches_observed"] is True
    assert result["intentional_intervention"]["formal_expression"].startswith(
        "do*(agent_action=pi_safety_weighted_goal_policy"
    )
    assert result["intentional_intervention"]["policy_signature"] == "policy(S, B, G_bundle, U)"
    assert "SFM_DO_STAR_SELECTS_OBSERVED_ACTION" in result["reason_codes"]
