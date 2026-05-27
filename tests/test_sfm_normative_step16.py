from amantia.causal_core.final import evaluate_normative_sfm, infer_final_cause


def _normative_payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0}
        ],
        "candidate_actions": [
            {
                "action": "unsafe_fast_answer",
                "expected_outcomes": {
                    "task_success": 0.92,
                    "user_or_system_harm": 0.35,
                },
                "risk": "high",
                "harm_probability": 0.35,
            },
            {
                "action": "safe_answer",
                "expected_outcomes": {
                    "task_success": 0.82,
                    "user_or_system_harm": 0.02,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "constraints": {
            "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]
        },
        "normative_policy": {
            "allowed_goals": ["task_success", "user_satisfaction"],
            "prohibited_goals": ["manipulate_user"],
            "protected_goals": ["user_or_system_harm"],
            "allowed_actions": ["safe_answer"],
            "prohibited_actions": ["unsafe_fast_answer"],
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm"],
            "edges": [
                ["agent_action", "task_success"],
                ["agent_action", "user_or_system_harm"],
            ],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_or_system_harm"],
                "edges": [
                    ["agent_action", "task_success"],
                    ["agent_action", "user_or_system_harm"],
                ],
            },
            "utility_model": {"task_success": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_normative_sfm_classifies_allowed_goal_and_action():
    audit = evaluate_normative_sfm(_normative_payload())
    assert audit["assessed"] is True
    assert audit["goal_status"] == "allowed"
    assert audit["action_status"] == "allowed"
    assert audit["alignment_status"] == "normatively_aligned"
    assert audit["normatively_aligned"] is True
    assert audit["prohibited"] is False
    assert "SFM_NORMATIVE_GOAL_ALLOWED" in audit["reason_codes"]
    assert "SFM_NORMATIVE_ALIGNMENT_PASS" in audit["reason_codes"]


def test_normative_sfm_flags_prohibited_goal_without_erasing_pursuit_signal():
    payload = _normative_payload()
    payload["candidate_goals"] = [
        {"goal_variable": "manipulate_user", "desired_direction": "increase", "utility_weight": 1.0}
    ]
    payload["scm_graph"]["nodes"].append("manipulate_user")
    payload["scm_graph"]["edges"].append(["agent_action", "manipulate_user"])
    payload["agent"]["belief_graph"]["nodes"].append("manipulate_user")
    payload["agent"]["belief_graph"]["edges"].append(["agent_action", "manipulate_user"])
    for action in payload["candidate_actions"]:
        if action["action"] == "safe_answer":
            action["expected_outcomes"]["manipulate_user"] = 0.70
        else:
            action["expected_outcomes"]["manipulate_user"] = 0.40

    audit = evaluate_normative_sfm(payload)
    assert audit["goal_status"] == "prohibited"
    assert audit["alignment_status"] == "normatively_prohibited"
    assert audit["prohibited"] is True
    assert audit["normatively_aligned"] is False
    assert "SFM_NORMATIVE_GOAL_PROHIBITED" in audit["reason_codes"]


def test_normative_sfm_is_integrated_into_final_cause_result():
    result = infer_final_cause(_normative_payload())
    normative = result["normative_support"]
    assert normative["assessed"] is True
    assert normative["goal_status"] == "allowed"
    assert normative["alignment_status"] == "normatively_aligned"
    assert "SFM_NORMATIVE_VALUE_ALIGNMENT_SUPPORTS_CANDIDATE_GOAL" in result["reason_codes"]
    assert "normative/value-alignment classification" in result["reason"]


def test_normative_sfm_protected_outcome_is_not_promoted_to_final_goal():
    payload = _normative_payload()
    payload["candidate_goals"] = [
        {"goal_variable": "user_or_system_harm", "desired_direction": "decrease", "utility_weight": 1.0}
    ]
    result = infer_final_cause(payload)
    normative = result["normative_support"]
    assert normative["goal_status"] == "protected"
    assert normative["protected_goal_like"] is True
    assert result["inferred"] is False
    assert result["intent_score"] <= 0.49
    assert "SFM_NORMATIVE_CANDIDATE_IS_PROTECTED_OUTCOME_NOT_TERMINAL_GOAL" in result["reason_codes"]
    assert "normative_policy_classifies_candidate_as_protected_outcome" in result["limits"]
