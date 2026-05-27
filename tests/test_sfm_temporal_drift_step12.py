from amantia.causal_core.final import evaluate_temporal_goal_drift, infer_final_cause


def _temporal_drift_payload():
    records = []
    # Early period: ask_clarification is repeatedly optimal for task_success.
    for idx in range(3):
        records.append(
            {
                "t": idx,
                "selected_action": "ask_clarification",
                "candidate_actions": [
                    {
                        "action": "answer_directly",
                        "expected_outcomes": {
                            "task_success": 0.45,
                            "latency": 0.92,
                            "user_or_system_harm": 0.07,
                        },
                    },
                    {
                        "action": "ask_clarification",
                        "expected_outcomes": {
                            "task_success": 0.88,
                            "latency": 0.40,
                            "user_or_system_harm": 0.01,
                        },
                    },
                ],
            }
        )
    # Later period: answer_directly is repeatedly optimal for latency/speed.
    for idx in range(3, 6):
        records.append(
            {
                "t": idx,
                "selected_action": "answer_directly",
                "candidate_actions": [
                    {
                        "action": "answer_directly",
                        "expected_outcomes": {
                            "task_success": 0.55,
                            "latency": 0.94,
                            "user_or_system_harm": 0.06,
                        },
                    },
                    {
                        "action": "ask_clarification",
                        "expected_outcomes": {
                            "task_success": 0.86,
                            "latency": 0.38,
                            "user_or_system_harm": 0.01,
                        },
                    },
                ],
            }
        )
    return {
        "observed_action": "answer_directly",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase"},
            {"goal_variable": "latency", "desired_direction": "increase"},
        ],
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_outcomes": {"task_success": 0.55, "latency": 0.94, "user_or_system_harm": 0.06},
            },
            {
                "action": "ask_clarification",
                "expected_outcomes": {"task_success": 0.86, "latency": 0.38, "user_or_system_harm": 0.01},
            },
        ],
        "policy_records": records,
        "temporal_window_size": 3,
        "min_temporal_window_records": 3,
        "min_temporal_goal_support": 0.5,
        "min_policy_records": 3,
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "latency", "user_or_system_harm"],
            "edges": [
                ["agent_action", "task_success"],
                ["agent_action", "latency"],
                ["agent_action", "user_or_system_harm"],
            ],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "latency"],
                "edges": [["agent_action", "task_success"], ["agent_action", "latency"]],
            },
            "utility_model": {"task_success": 0.7, "latency": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_temporal_goal_drift_detects_change_between_windows():
    report = evaluate_temporal_goal_drift(_temporal_drift_payload())
    assert report["assessed"] is True
    assert report["drift_detected"] is True
    assert report["window_count"] == 2
    assert report["initial_goal"] == "task_success"
    assert report["final_goal"] == "latency"
    assert report["drift_events"][0]["event_type"] == "goal_change"
    assert "SFM_TEMPORAL_GOAL_DRIFT_DETECTED" in report["reason_codes"]


def test_temporal_goal_drift_is_integrated_into_final_cause_result():
    result = infer_final_cause(_temporal_drift_payload())
    temporal = result["temporal_goal_drift_support"]
    assert temporal["assessed"] is True
    assert temporal["drift_detected"] is True
    assert temporal["final_goal"] == "latency"
    assert "SFM_TEMPORAL_FINAL_WINDOW_SUPPORTS_CANDIDATE_GOAL" in result["reason_codes"]
    assert "temporal_goal_drift_detected" in result["limits"]


def test_temporal_goal_drift_reports_insufficient_records_conservatively():
    payload = _temporal_drift_payload()
    payload["policy_records"] = payload["policy_records"][:3]
    report = evaluate_temporal_goal_drift(payload)
    assert report["assessed"] is False
    assert "SFM_TEMPORAL_INSUFFICIENT_RECORDS" in report["reason_codes"]
    assert "at_least_two_temporal_windows_required" in report["limits"]
