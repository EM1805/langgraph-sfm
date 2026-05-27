from amantia.causal_core.final import evaluate_context_conditioning, infer_final_cause


def _context_conditioned_payload():
    records = []
    for idx in range(3):
        records.append(
            {
                "t": idx,
                "context": {"ambiguity": "high"},
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
    for idx in range(3, 6):
        records.append(
            {
                "t": idx,
                "context": {"ambiguity": "low"},
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
        "state": {"ambiguity": "low"},
        "context_key": "ambiguity",
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
        "min_context_records": 3,
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


def test_context_conditioning_detects_context_specific_goals():
    report = evaluate_context_conditioning(_context_conditioned_payload())
    assert report["assessed"] is True
    assert report["context_conditioning_detected"] is True
    assert report["policy_type"] == "context_conditioned_policy"
    assert report["context_key"] == "ambiguity"
    assert report["dominant_goal_by_context"] == {"high": "task_success", "low": "latency"}
    assert report["current_context_value"] == "low"
    assert report["current_context_goal"] == "latency"
    assert "SFM_CONTEXT_CONDITIONED_POLICY_DETECTED" in report["reason_codes"]


def test_context_conditioning_is_integrated_into_final_cause_result():
    result = infer_final_cause(_context_conditioned_payload())
    context = result["context_conditioning_support"]
    assert context["assessed"] is True
    assert context["context_conditioning_detected"] is True
    assert context["current_context_goal"] == "latency"
    assert result["most_likely_goal"] == "latency"
    assert "SFM_CONTEXT_CURRENT_BUCKET_SUPPORTS_CANDIDATE_GOAL" in result["reason_codes"]
    assert "temporal_drift_may_be_context_conditioned_policy" in result["limits"]


def test_context_conditioning_reports_missing_context_key_conservatively():
    payload = _context_conditioned_payload()
    for record in payload["policy_records"]:
        record.pop("context", None)
    report = evaluate_context_conditioning(payload)
    assert report["assessed"] is False
    assert "SFM_CONTEXT_NO_USABLE_CONTEXT_KEY" in report["reason_codes"]
    assert "context_key_with_two_buckets_required" in report["limits"]
