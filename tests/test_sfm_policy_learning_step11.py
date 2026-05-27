from amantia.causal_core.final import evaluate_policy_learning, infer_final_cause


def _policy_learning_payload():
    policy_records = []
    # Across repeated decisions, ask_clarification is the option that maximizes
    # task_success while answer_directly usually maximizes latency.  This should
    # make task_success the inverse-goal winner.
    for idx, ambiguity in enumerate(["high", "high", "medium", "high"]):
        policy_records.append(
            {
                "t": idx,
                "state": {"ambiguity": ambiguity},
                "selected_action": "ask_clarification",
                "candidate_actions": [
                    {
                        "action": "answer_directly",
                        "expected_outcomes": {
                            "task_success": 0.48 + idx * 0.02,
                            "user_satisfaction": 0.40,
                            "latency": 0.90,
                            "user_or_system_harm": 0.07,
                        },
                    },
                    {
                        "action": "ask_clarification",
                        "expected_outcomes": {
                            "task_success": 0.86,
                            "user_satisfaction": 0.72,
                            "latency": 0.42,
                            "user_or_system_harm": 0.01,
                        },
                    },
                ],
            }
        )
    return {
        "observed_action": "ask_clarification",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0},
            {"goal_variable": "latency", "desired_direction": "increase", "utility_weight": 1.0},
        ],
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_outcomes": {"task_success": 0.50, "latency": 0.90, "user_or_system_harm": 0.07},
            },
            {
                "action": "ask_clarification",
                "expected_outcomes": {"task_success": 0.86, "latency": 0.42, "user_or_system_harm": 0.01},
            },
        ],
        "policy_records": policy_records,
        "min_policy_records": 3,
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "latency", "user_or_system_harm"],
            "edges": [["agent_action", "task_success"], ["agent_action", "latency"], ["agent_action", "user_or_system_harm"]],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "latency"],
                "edges": [["agent_action", "task_success"], ["agent_action", "latency"]],
            },
            "utility_model": {"task_success": 1.0, "latency": 0.1, "user_or_system_harm": -2.0},
        },
    }


def test_policy_learning_ranks_goal_that_explains_repeated_selected_actions():
    report = evaluate_policy_learning(_policy_learning_payload())
    assert report["assessed"] is True
    assert report["most_likely_goal"] == "task_success"
    assert report["usable_records"] == 4
    top = report["goal_evidence"][0]
    assert top["goal_variable"] == "task_success"
    assert top["selected_optimal_rate"] == 1.0
    assert "SFM_POLICY_LEARNING_FOUND_PLAUSIBLE_GOAL" in report["reason_codes"]


def test_policy_learning_is_integrated_into_final_cause_result():
    result = infer_final_cause(_policy_learning_payload())
    assert result["policy_learning_support"]["assessed"] is True
    assert result["policy_learning_support"]["most_likely_goal"] == "task_success"
    assert "SFM_POLICY_LEARNING_SUPPORTS_CANDIDATE_GOAL" in result["reason_codes"]
    assert result["policy_learning_support"]["current_action_seen_in_sequence"] is True


def test_policy_learning_reports_missing_sequence_records_conservatively():
    payload = _policy_learning_payload()
    payload.pop("policy_records")
    report = evaluate_policy_learning(payload)
    assert report["assessed"] is False
    assert "SFM_POLICY_LEARNING_NO_SEQUENCE_RECORDS" in report["reason_codes"]
    assert "sequence_records_required" in report["limits"]
