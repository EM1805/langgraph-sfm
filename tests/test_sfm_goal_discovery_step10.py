from amantia.causal_core.final import discover_candidate_goals, infer_final_cause


def _payload_without_explicit_goals():
    return {
        "observed_action": "ask_clarification",
        "action_variable": "agent_action",
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_outcomes": {
                    "task_success": 0.55,
                    "user_satisfaction": 0.30,
                    "user_or_system_harm": 0.06,
                },
                "risk": "medium",
                "harm_probability": 0.06,
            },
            {
                "action": "ask_clarification",
                "expected_outcomes": {
                    "task_success": 0.86,
                    "user_satisfaction": 0.74,
                    "user_or_system_harm": 0.01,
                },
                "risk": "low",
                "harm_probability": 0.01,
            },
        ],
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
                "nodes": ["agent_action", "task_success", "user_satisfaction"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_satisfaction"]],
            },
            "utility_model": {"task_success": 1.2, "user_satisfaction": 0.7, "user_or_system_harm": -2.0},
        },
    }


def test_goal_discovery_ranks_plausible_positive_goals_over_protected_outcomes():
    report = discover_candidate_goals(_payload_without_explicit_goals())
    assert report["assessed"] is True
    assert report["discovered"] is True
    selected = [goal["goal_variable"] for goal in report["selected_goals"]]
    assert "task_success" in selected
    assert "user_or_system_harm" not in selected
    top_candidate = report["candidates"][0]
    assert top_candidate["selected_goal_matches_observed"] is True
    assert "SFM_GOAL_DISCOVERY_FOUND_CANDIDATES" in report["reason_codes"]


def test_infer_final_cause_bootstraps_missing_candidate_goals_from_discovery():
    result = infer_final_cause(_payload_without_explicit_goals())
    assert result["goal_discovery_support"]["used_for_inference"] is True
    assert result["most_likely_goal"] in {"task_success", "user_satisfaction"}
    assert result["intentional_intervention"]["goal"]["goal_variable"] == result["most_likely_goal"]
    assert "SFM_GOAL_DISCOVERY_BOOTSTRAPPED_CANDIDATE_GOALS" in result["reason_codes"]
    assert "candidate_goals_were_discovered_not_user_supplied" in result["limits"]


def test_explicit_candidate_goals_are_preserved_and_discovery_is_diagnostic_only():
    payload = _payload_without_explicit_goals()
    payload["candidate_goals"] = ["user_satisfaction"]
    result = infer_final_cause(payload)
    assert result["most_likely_goal"] == "user_satisfaction"
    assert result["goal_discovery_support"]["explicit_goals_supplied"] is True
    assert result["goal_discovery_support"]["used_for_inference"] is False
    assert "SFM_GOAL_DISCOVERY_EXPLICIT_GOALS_PRESERVED" in result["reason_codes"]
