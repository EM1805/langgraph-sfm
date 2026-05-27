from amantia.causal_core.final import (
    EXECUTION_PROFILES,
    infer_final_cause,
    infer_final_cause_compact,
    resolve_sfm_execution_plan,
)


def _payload(**overrides):
    payload = {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
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
    payload.update(overrides)
    return payload


def test_execution_profiles_are_public_and_resolvable():
    assert set(EXECUTION_PROFILES).issuperset({"full", "fast", "minimal", "governance"})
    plan = resolve_sfm_execution_plan({"execution_profile": "fast"})
    assert plan["profile"] == "fast"
    assert "twin_model" in plan["enabled_layers"]
    assert "normative" in plan["disabled_layers"]
    assert "SFM_EXECUTION_PROFILE_FAST" in plan["reason_codes"]


def test_fast_profile_disables_heavy_governance_layers_but_keeps_summary():
    result = infer_final_cause(_payload(execution_profile="fast"))
    plan = result["execution_profile_support"]
    assert plan["profile"] == "fast"
    assert result["normative_support"]["disabled"] is True
    assert result["action_recommendation_support"]["disabled"] is True
    assert result["alignment_summary"]["assessed"] is True
    assert "SFM_LAYER_DISABLED_NORMATIVE" in result["normative_support"]["reason_codes"]


def test_enabled_layers_override_narrows_execution_without_breaking_core_result():
    result = infer_final_cause(
        _payload(
            enabled_layers=["identification", "counterfactual", "twin", "identifiability"],
        )
    )
    plan = result["execution_profile_support"]
    assert set(plan["enabled_layers"]).issuperset({"identification", "counterfactual", "twin_model", "alignment_summary"})
    assert result["falsification_support"]["disabled"] is True
    assert result["utility_support"]["disabled"] is True
    assert result["alignment_summary"]["assessed"] is True


def test_disabled_layers_override_can_remove_alignment_summary_explicitly():
    result = infer_final_cause(_payload(disabled_layers=["alignment_summary", "norms"]))
    plan = result["execution_profile_support"]
    assert "alignment_summary" in plan["disabled_layers"]
    assert result["alignment_summary"]["disabled"] is True
    assert result["normative_support"]["disabled"] is True


def test_compact_result_exposes_execution_profile_contract():
    compact = infer_final_cause_compact(_payload(execution_profile="governance"))
    assert compact["execution_profile_support"]["profile"] == "governance"
    assert "alignment_summary" in compact
    assert "causal_support" not in compact
