from amantia.causal_core.final import (
    evaluate_normative_sfm,
    infer_final_cause,
    normalize_normative_policy,
    recommend_sfm_action,
)


def _base_payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0}
        ],
        "candidate_actions": [
            {
                "action": "unsafe_fast_answer",
                "expected_outcomes": {"task_success": 0.94, "user_or_system_harm": 0.30},
                "risk": "high",
                "harm_probability": 0.30,
            },
            {
                "action": "safe_answer",
                "expected_outcomes": {"task_success": 0.82, "user_or_system_harm": 0.02},
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "constraints": {
            "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm"],
            "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_or_system_harm"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
            },
            "utility_model": {"task_success": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_normalize_normative_policy_merges_inline_lists_and_rich_rules():
    policy = {
        "allowed_goals": [{"target": "task_success", "severity": 0.7, "reason": "primary allowed goal"}],
        "rules": [
            {
                "target": "manipulate_user",
                "target_type": "goal",
                "status": "prohibited",
                "severity": 0.95,
                "source": "safety_policy",
            }
        ],
        "action_rules": [
            {"target": "unsafe_fast_answer", "status": "prohibited", "severity": 0.9},
        ],
    }

    normalized = normalize_normative_policy(policy).to_dict()
    assert normalized["assessed"] is True
    assert normalized["allowed_goals"] == ["task_success"]
    assert normalized["prohibited_goals"] == ["manipulate_user"]
    assert normalized["prohibited_actions"] == ["unsafe_fast_answer"]
    assert any(rule["severity"] == 0.7 for rule in normalized["rules"] if rule["target"] == "task_success")
    assert any(rule["source"] == "safety_policy" for rule in normalized["rules"] if rule["target"] == "manipulate_user")


def test_normative_audit_uses_normalized_rule_severity_for_inline_policy_dicts():
    payload = _base_payload()
    payload["normative_policy"] = {
        "allowed_goals": [
            {"target": "task_success", "severity": 0.6, "reason": "allowed but lower confidence"}
        ],
        "allowed_actions": ["safe_answer"],
    }

    audit = evaluate_normative_sfm(payload)
    assert audit["goal_status"] == "allowed"
    assert audit["action_status"] == "allowed"
    assert audit["goal_rule_severity"] == 0.6
    assert audit["normalized_policy"]["allowed_goals"] == ["task_success"]
    assert "SFM_NORMATIVE_POLICY_NORMALIZED" in audit["reason_codes"]


def test_rich_normative_rules_feed_final_cause_alignment_summary():
    payload = _base_payload()
    payload["normative_policy"] = {
        "rules": [
            {"target": "task_success", "target_type": "goal", "status": "allowed", "severity": 0.8},
            {"target": "safe_answer", "target_type": "action", "status": "allowed", "severity": 0.8},
        ]
    }

    result = infer_final_cause(payload)
    assert result["normative_support"]["goal_status"] == "allowed"
    assert result["alignment_summary"]["normatively_aligned"] is True
    assert result["alignment_summary"]["prohibited"] is False


def test_recommender_uses_same_normalized_rules_as_normative_audit():
    payload = _base_payload()
    payload["normative_policy"] = {
        "rules": [
            {"target": "task_success", "target_type": "goal", "status": "allowed"},
            {"target": "unsafe_fast_answer", "target_type": "action", "status": "prohibited", "severity": 0.9},
            {"target": "safe_answer", "target_type": "action", "status": "allowed", "severity": 0.8},
        ]
    }

    recommendation = recommend_sfm_action(payload)
    assert recommendation["recommended_action"] == "safe_answer"
    assert "unsafe_fast_answer" in recommendation["blocked_actions"]
    unsafe = next(row for row in recommendation["rankings"] if row["action"] == "unsafe_fast_answer")
    assert unsafe["normative_status"] == "prohibited"
    assert unsafe["hard_blocked"] is True
