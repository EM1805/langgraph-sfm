from amantia.causal_core.final import (
    evaluate_sfm_robustness,
    infer_final_cause,
    infer_final_cause_compact,
    resolve_sfm_execution_plan,
)


def _payload(low_uncertainty=True):
    first_uncertainty = 0.02 if low_uncertainty else 0.35
    first_quality = "high" if low_uncertainty else "low"
    second_uncertainty = 0.03 if low_uncertainty else 0.30
    second_quality = "high" if low_uncertainty else "low"
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "min_intent_score": 0.6,
        "candidate_goals": [
            {"goal_variable": "task_success", "desired_direction": "increase", "utility_weight": 1.0}
        ],
        "candidate_actions": [
            {
                "action": "safe_answer",
                "expected_outcomes": {"task_success": 0.90, "user_or_system_harm": 0.02},
                "risk": "low",
                "harm_probability": 0.02,
                "uncertainty": first_uncertainty,
                "evidence_quality": first_quality,
            },
            {
                "action": "careful_answer",
                "expected_outcomes": {"task_success": 0.78, "user_or_system_harm": 0.01},
                "risk": "low",
                "harm_probability": 0.01,
                "uncertainty": second_uncertainty,
                "evidence_quality": second_quality,
            },
        ],
        "constraints": {
            "hard": [{"outcome": "user_or_system_harm", "direction": "decrease", "threshold": 0.05}]
        },
        "normative_policy": {
            "allowed_goals": ["task_success"],
            "allowed_actions": ["safe_answer", "careful_answer"],
        },
        "protected_outcome": "user_or_system_harm",
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm"],
            "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
        },
        "agent": {
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "user_or_system_harm"],
                "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
            },
            "utility_model": {"task_success": 1.0, "user_or_system_harm": -2.0},
        },
    }


def test_robustness_layer_is_integrated_into_final_cause_result():
    result = infer_final_cause(_payload(low_uncertainty=True))
    robustness = result["robustness_support"]
    assert robustness["assessed"] is True
    assert robustness["robustness_status"] == "robust_supported"
    assert robustness["robust_to_uncertainty"] is True
    assert robustness["pessimistic_intent_score"] >= result["raw"]["min_intent_score"]
    assert "SFM_ROBUSTNESS_ASSESSED" in robustness["reason_codes"]
    assert result["alignment_summary"]["robust_to_uncertainty"] is True


def test_high_uncertainty_turns_alignment_summary_into_review_not_allow():
    result = infer_final_cause(_payload(low_uncertainty=False))
    robustness = result["robustness_support"]
    summary = result["alignment_summary"]
    assert robustness["assessed"] is True
    assert robustness["robustness_status"] in {"fragile_support", "supported_but_uncertain"}
    assert robustness["uncertainty_review_required"] is True
    assert summary["verdict"] in {"supported_but_uncertain", "plausible_but_unidentified"}
    assert summary["gate_status"] == "review"
    assert summary["uncertainty_review_required"] is True


def test_standalone_robustness_helper_accepts_precomputed_layer_outputs():
    audit = evaluate_sfm_robustness(
        {
            "query": _payload(low_uncertainty=True),
            "goal": "task_success",
            "intent_score": 0.82,
            "intent_supported": True,
            "falsification_passed": True,
            "sfm_identifiability_support": {"authority_status": "partial_sfm_identification"},
            "action_recommendation_support": {"assessed": True, "top_margin": 0.12},
            "constraint_support": {"assessed": True, "observed_feasible": True},
            "normative_support": {"assessed": True, "normatively_aligned": True},
        }
    )
    assert audit["assessed"] is True
    assert audit["pessimistic_intent_score"] <= audit["baseline_intent_score"]
    assert audit["robustness_status"] in {"robust_supported", "supported_but_uncertain"}


def test_robustness_layer_can_be_selected_by_alias():
    plan = resolve_sfm_execution_plan({"enabled_layers": ["id", "cf", "robust", "summary"]})
    assert "robustness" in plan["enabled_layers"]
    assert "alignment_summary" in plan["enabled_layers"]


def test_compact_result_exposes_robustness_contract():
    compact = infer_final_cause_compact(_payload(low_uncertainty=True))
    assert compact["robustness_status"] == "robust_supported"
    assert compact["robust_to_uncertainty"] is True
