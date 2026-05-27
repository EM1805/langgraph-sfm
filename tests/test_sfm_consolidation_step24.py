from amantia.causal_core.final import (
    SFMExecutionPlan,
    SFMExecutionRunner,
    infer_final_cause,
    normalize_protection_policy,
    run_sfm_validation_benchmark,
)


def _payload():
    return {
        "observed_action": "safe_answer",
        "action_variable": "agent_action",
        "candidate_goals": [
            {
                "goal_variable": "task_success",
                "protected_outcomes": ["user_or_system_harm"],
                "side_effect_outcomes": ["latency_spike"],
            }
        ],
        "candidate_actions": [
            {
                "action": "safe_answer",
                "expected_outcomes": {
                    "task_success": 0.82,
                    "user_or_system_harm": 0.02,
                    "latency_spike": 0.10,
                },
                "risk": "low",
                "harm_probability": 0.02,
            },
            {
                "action": "unsafe_fast_answer",
                "expected_outcomes": {
                    "task_success": 0.92,
                    "user_or_system_harm": 0.45,
                    "latency_spike": 0.02,
                },
                "risk": "high",
                "harm_probability": 0.45,
            },
        ],
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "user_or_system_harm"],
            "edges": [["agent_action", "task_success"], ["agent_action", "user_or_system_harm"]],
        },
        "agent": {
            "belief_graph": {
                "nodes": ["agent_action", "task_success"],
                "edges": [["agent_action", "task_success"]],
            },
            "utility_model": {"task_success": 1.0},
        },
        "constraint_model": {
            "hard_constraints": {"user_or_system_harm": {"threshold": 0.10}},
            "side_effects": ["latency_spike"],
        },
        "normative_policy": {
            "rules": [
                {
                    "target": "unsafe_fast_answer",
                    "target_type": "action",
                    "status": "prohibited",
                    "severity": 0.9,
                    "source": "test_policy",
                }
            ],
            "protected_outcomes": ["user_or_system_harm"],
        },
    }


def test_execution_runner_centralizes_disabled_layer_reports():
    plan = SFMExecutionPlan.resolve(enabled_layers=["identification"])
    runner = SFMExecutionRunner(plan)
    assert runner.run("identification", lambda: {"assessed": True}) == {"assessed": True}
    disabled = runner.run("normative", lambda: {"assessed": True})
    assert disabled["disabled"] is True
    assert disabled["layer"] == "normative"
    assert "SFM_LAYER_DISABLED_NORMATIVE" in disabled["reason_codes"]
    assert "identification" in runner.to_dict()["executed_layers"]
    assert "normative" in runner.to_dict()["disabled_layers"]


def test_protection_policy_unifies_query_constraints_and_normative_rules():
    policy = normalize_protection_policy(_payload()).to_dict()
    assert policy["assessed"] is True
    assert "user_or_system_harm" in policy["protected_outcomes"]
    assert "user_or_system_harm" in policy["hard_constraints"]
    assert "latency_spike" in policy["side_effect_outcomes"]
    assert "unsafe_fast_answer" in policy["prohibited_actions"]
    assert "SFM_PROTECTION_POLICY_NORMALIZED" in policy["reason_codes"]


def test_inference_exposes_normalized_protection_policy_in_constraint_support():
    result = infer_final_cause(_payload())
    protection = result["constraint_support"]["normalized_protection_policy"]
    assert protection["assessed"] is True
    assert "user_or_system_harm" in protection["protected_outcomes"]
    assert "latency_spike" in protection["side_effect_outcomes"]
    assert "unsafe_fast_answer" in protection["prohibited_actions"]
    assert result["most_likely_goal"] == "task_success"


def test_step24_validation_matrix_expands_negative_cases():
    report = run_sfm_validation_benchmark()
    assert report["passed"] is True
    assert report["total_cases"] >= 9
    assert report["false_positive_claims"] == 0
    names = {case["name"] for case in report["case_results"]}
    assert "belief_graph_supports_goal_but_real_graph_zero_effect_with_controls" in names
    assert "utility_high_without_scm_claim_withheld" in names
    assert "protected_outcome_candidate_not_terminal_goal" in names
    assert "goal_discovery_avoids_protected_outcome" in names
