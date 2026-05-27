from amantia.causal_core.final import infer_final_cause, recommend_sfm_action


def _payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "goal_bundle": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0},
            {"goal_variable": "user_satisfaction", "desired_direction": "increase", "utility_weight": 0.7},
        ],
        "candidate_actions": [
            {
                "action": "unsafe_fast_answer",
                "expected_outcomes": {
                    "task_success": 0.95,
                    "user_satisfaction": 0.60,
                    "user_or_system_harm": 0.32,
                },
                "risk": "high",
                "harm_probability": 0.32,
                "uncertainty": 0.08,
                "evidence_quality": "high",
            },
            {
                "action": "safe_answer",
                "expected_outcomes": {
                    "task_success": 0.82,
                    "user_satisfaction": 0.82,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
                "uncertainty": 0.04,
                "evidence_quality": "high",
            },
            {
                "action": "uncertain_answer",
                "expected_outcomes": {
                    "task_success": 0.87,
                    "user_satisfaction": 0.75,
                    "user_or_system_harm": 0.03,
                },
                "risk": "low",
                "harm_probability": 0.03,
                "uncertainty": 0.30,
                "evidence_quality": "low",
            },
        ],
        "constraints": {
            "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]
        },
        "normative_policy": {
            "allowed_goals": ["task_success", "user_satisfaction"],
            "protected_goals": ["user_or_system_harm"],
            "allowed_actions": ["safe_answer", "uncertain_answer"],
            "prohibited_actions": ["unsafe_fast_answer"],
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_satisfaction", "user_or_system_harm"],
            "edges": [
                ["agent_action", "task_success"],
                ["agent_action", "user_satisfaction"],
                ["agent_action", "user_or_system_harm"],
            ],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_satisfaction", "user_or_system_harm"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_satisfaction"]],
            },
            "utility_model": {"task_success": 1.0, "user_satisfaction": 0.7, "user_or_system_harm": -2.0},
        },
    }


def test_sfm_action_recommendation_selects_safe_feasible_action():
    audit = recommend_sfm_action(_payload())
    assert audit["assessed"] is True
    assert audit["recommendation_status"] == "recommended"
    assert audit["recommended_action"] == "safe_answer"
    assert audit["recommendation_matches_observed"] is True
    assert "safe_answer" in audit["feasible_actions"]
    assert "unsafe_fast_answer" in audit["blocked_actions"]
    assert audit["rankings"][0]["action"] == "safe_answer"
    assert audit["rankings"][0]["recommendable"] is True
    assert any(row["action"] == "uncertain_answer" and row["uncertainty_penalty"] >= 0.20 for row in audit["rankings"])
    assert "SFM_ACTION_RECOMMENDATION_SELECTED_ACTION" in audit["reason_codes"]
    assert audit["recommended_intervention"]["expression"].startswith("do*(agent_action=pi_sfm_recommendation_policy")


def test_sfm_action_recommendation_surfaces_escalation_action():
    payload = _payload()
    payload["observed_action"] = "expert_review"
    payload["candidate_actions"] = [
        {
            "action": "safe_answer",
            "expected_outcomes": {"task_success": 0.70, "user_satisfaction": 0.65, "user_or_system_harm": 0.01},
            "risk": "low",
            "uncertainty": 0.04,
        },
        {
            "action": "expert_review",
            "expected_outcomes": {"task_success": 0.92, "user_satisfaction": 0.90, "user_or_system_harm": 0.01},
            "risk": "low",
            "uncertainty": 0.03,
        },
    ]
    payload["normative_policy"]["allowed_actions"] = ["safe_answer", "expert_review"]
    payload["normative_policy"]["escalation_actions"] = ["expert_review"]

    audit = recommend_sfm_action(payload)
    assert audit["assessed"] is True
    assert audit["recommendation_status"] == "requires_escalation"
    assert audit["recommended_action"] == "expert_review"
    assert "expert_review" in audit["escalation_actions"]
    assert "SFM_ACTION_RECOMMENDATION_SELECTED_ESCALATION_ACTION" in audit["reason_codes"]
    assert "recommended_action_requires_escalation_before_execution" in audit["limits"]


def test_sfm_action_recommendation_is_integrated_into_final_cause_result():
    payload = _payload()
    payload["candidate_goals"] = payload["goal_bundle"]
    result = infer_final_cause(payload)
    recommendation = result["action_recommendation_support"]
    assert recommendation["assessed"] is True
    assert recommendation["recommended_action"] == "safe_answer"
    assert recommendation["recommendation_matches_observed"] is True
    assert "SFM_ACTION_RECOMMENDATION_SUPPORTS_OBSERVED_ACTION_FOR_CANDIDATE_GOAL" in result["reason_codes"]
    assert "SFM intervention recommendation under goals/constraints/norms/uncertainty" in result["reason"]
