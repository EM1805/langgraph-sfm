from amantia.causal_core.final import evaluate_hierarchical_goals, infer_final_cause


def _hierarchical_payload():
    return {
        "observed_action": "fast_reply",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "response_speed", "desired_direction": "increase", "utility_weight": 0.8},
            {"goal_variable": "user_satisfaction", "desired_direction": "increase", "utility_weight": 1.0},
        ],
        "candidate_actions": [
            {
                "action": "fast_reply",
                "expected_outcomes": {
                    "response_speed": 0.95,
                    "user_satisfaction": 0.78,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
            {
                "action": "slow_reflective_reply",
                "expected_outcomes": {
                    "response_speed": 0.42,
                    "user_satisfaction": 0.72,
                    "user_or_system_harm": 0.01,
                },
                "risk": "low",
                "harm_probability": 0.01,
            },
        ],
        "goal_hierarchy_edges": [
            {"instrumental_goal": "response_speed", "final_goal": "user_satisfaction"}
        ],
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "response_speed", "user_satisfaction", "user_or_system_harm"],
            "edges": [
                ["agent_action", "response_speed"],
                ["agent_action", "user_satisfaction"],
                ["agent_action", "user_or_system_harm"],
            ],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "response_speed", "user_satisfaction"],
                "edges": [
                    ["agent_action", "response_speed"],
                    ["response_speed", "user_satisfaction"],
                    ["agent_action", "user_satisfaction"],
                ],
            },
            "utility_model": {"response_speed": 0.4, "user_satisfaction": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_hierarchical_sfm_classifies_instrumental_and_final_goals():
    audit = evaluate_hierarchical_goals(_hierarchical_payload())
    assert audit["assessed"] is True
    assert audit["hierarchy_detected"] is True
    assert audit["instrumental_goals"] == ["response_speed"]
    assert audit["terminal_goals"] == ["user_satisfaction"]
    assert audit["selected_ultimate_goal"] == "user_satisfaction"
    assert audit["ultimate_goal_by_instrument"] == {"response_speed": ["user_satisfaction"]}
    profiles = {row["goal_variable"]: row for row in audit["goal_profiles"]}
    assert profiles["response_speed"]["role"] == "instrumental_goal"
    assert profiles["response_speed"]["supports_ultimate_goals"] == ["user_satisfaction"]
    assert profiles["user_satisfaction"]["role"] == "final_goal"
    assert profiles["user_satisfaction"]["supported_by_instruments"] == ["response_speed"]
    assert "SFM_HIERARCHY_INSTRUMENTAL_TO_FINAL_PATH_DETECTED" in audit["reason_codes"]


def test_hierarchical_sfm_is_integrated_into_final_cause_result():
    result = infer_final_cause(_hierarchical_payload())
    hierarchy = result["hierarchical_goal_support"]
    assert hierarchy["assessed"] is True
    assert hierarchy["selected_ultimate_goal"] == "user_satisfaction"
    assert result["most_likely_goal"] == "user_satisfaction"
    assert "SFM_HIERARCHY_SUPPORTS_CANDIDATE_AS_FINAL_GOAL" in result["reason_codes"]
    assert "SFM_HIERARCHY_SELECTED_ULTIMATE_GOAL" in result["reason_codes"]


def test_hierarchical_sfm_reports_missing_edges_conservatively():
    payload = _hierarchical_payload()
    payload.pop("goal_hierarchy_edges")
    payload["scm_graph"]["edges"] = [
        ["agent_action", "response_speed"],
        ["agent_action", "user_satisfaction"],
    ]
    payload["agent"]["belief_graph"]["edges"] = [
        ["agent_action", "response_speed"],
        ["agent_action", "user_satisfaction"],
    ]
    audit = evaluate_hierarchical_goals(payload)
    assert audit["assessed"] is False
    assert "SFM_HIERARCHY_NO_GOAL_EDGES" in audit["reason_codes"]
    assert "goal_hierarchy_edges_required_for_hierarchical_sfm" in audit["limits"]
