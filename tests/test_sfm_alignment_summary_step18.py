from amantia.causal_core.final import infer_final_cause, infer_final_cause_compact, summarize_sfm_alignment


def _payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0}
        ],
        "candidate_actions": [
            {
                "action": "unsafe_fast_answer",
                "expected_outcomes": {"task_success": 0.96, "user_or_system_harm": 0.32},
                "risk": "high",
                "harm_probability": 0.32,
            },
            {
                "action": "safe_answer",
                "expected_outcomes": {"task_success": 0.86, "user_or_system_harm": 0.02},
                "risk": "low",
                "harm_probability": 0.02,
            },
        ],
        "constraints": {
            "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]
        },
        "normative_policy": {
            "allowed_goals": ["task_success"],
            "protected_goals": ["user_or_system_harm"],
            "allowed_actions": ["safe_answer"],
            "prohibited_actions": ["unsafe_fast_answer"],
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


def test_alignment_summary_is_integrated_into_final_cause_result():
    result = infer_final_cause(_payload())
    summary = result["alignment_summary"]
    assert summary["assessed"] is True
    assert summary["goal_variable"] == "task_success"
    assert summary["observed_action"] == "safe_answer"
    assert summary["falsification_passed"] is True
    assert summary["constraints_satisfied"] is True
    assert summary["prohibited"] is False
    assert summary["gate_status"] in {"allow", "review"}
    assert summary["verdict"] in {
        "aligned_supported",
        "diagnostic_only",
        "supported_but_normatively_unspecified",
        "plausible_but_unidentified",
    }
    assert any(code.startswith("SFM_ALIGNMENT_VERDICT_") for code in summary["reason_codes"])
    assert any(code.startswith("SFM_GATE_STATUS_") for code in summary["reason_codes"])


def test_alignment_summary_blocks_supported_but_prohibited_goal():
    payload = _payload()
    payload["candidate_goals"] = [{"goal_variable": "manipulate_user", "desired_direction": "increase"}]
    payload["normative_policy"]["allowed_goals"] = ["task_success"]
    payload["normative_policy"]["prohibited_goals"] = ["manipulate_user"]
    payload["scm_graph"]["nodes"].append("manipulate_user")
    payload["scm_graph"]["edges"].append(["agent_action", "manipulate_user"])
    payload["agent"]["belief_graph"]["nodes"].append("manipulate_user")
    payload["agent"]["belief_graph"]["edges"].append(["agent_action", "manipulate_user"])
    for option in payload["candidate_actions"]:
        option["expected_outcomes"]["manipulate_user"] = 0.9 if option["action"] == "safe_answer" else 0.3

    result = infer_final_cause(payload)
    summary = result["alignment_summary"]
    assert summary["prohibited"] is True
    assert summary["verdict"] == "supported_but_prohibited"
    assert summary["gate_status"] == "block"
    assert "goal_or_action_prohibited_by_normative_policy" in summary["blocking_reasons"]


def test_alignment_summary_blocks_constraint_violation():
    payload = _payload()
    payload["observed_action"] = "unsafe_fast_answer"
    result = infer_final_cause(payload)
    summary = result["alignment_summary"]
    assert summary["constraints_satisfied"] is False
    assert summary["gate_status"] == "block"
    assert summary["verdict"] in {"supported_but_constraint_blocked", "supported_but_prohibited"}
    assert "observed_action_violates_constraints" in summary["blocking_reasons"]


def test_compact_inference_preserves_governance_contract_without_full_layer_payload():
    compact = infer_final_cause_compact(_payload())
    assert set(compact).issuperset({"alignment_summary", "most_likely_goal", "intent_score", "authority_status"})
    assert compact["alignment_summary"]["assessed"] is True
    assert "causal_support" not in compact
    assert "twin_support" not in compact


def test_standalone_alignment_summary_helper_accepts_layer_outputs():
    summary = summarize_sfm_alignment(
        {
            "query": _payload(),
            "goal": "task_success",
            "inferred": True,
            "intent_score": 0.82,
            "support_level": "high",
            "authority_status": "partial_sfm_identification",
            "falsification_passed": True,
            "side_effects_excluded": True,
            "constraint_support": {"assessed": True, "observed_feasible": True},
            "normative_support": {"assessed": True, "normatively_aligned": True},
            "action_recommendation_support": {
                "assessed": True,
                "recommendation_status": "recommended",
                "recommended_action": "safe_answer",
                "recommendation_matches_observed": True,
            },
        }
    )
    assert summary["verdict"] == "aligned_supported"
    assert summary["gate_status"] == "allow"
    assert summary["allow_execution"] is True
