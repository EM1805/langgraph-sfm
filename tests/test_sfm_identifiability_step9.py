from amantia.causal_core.final import assess_sfm_identifiability, infer_final_cause


def _strong_payload():
    return {
        "observed_action": "answer_directly",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
        "negative_control_goals": ["unrelated_metric"],
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success", "unrelated_metric"],
                "edges": [["agent_action", "task_success"]],
            },
        },
        "candidate_actions": [
            {
                "action": "answer_directly",
                "expected_success": 0.95,
                "expected_outcomes": {"task_success": 0.95, "unrelated_metric": 0.10},
                "risk": "low",
                "harm_probability": 0.01,
            },
            {
                "action": "ask_clarification",
                "expected_success": 0.60,
                "expected_outcomes": {"task_success": 0.60, "unrelated_metric": 0.90},
                "risk": "none",
                "harm_probability": 0.0,
            },
        ],
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "unrelated_metric"],
            "edges": [["agent_action", "task_success"]],
        },
    }


def test_standalone_identifiability_reports_surface_diagnostic_without_engine_evidence():
    audit = assess_sfm_identifiability(_strong_payload())
    assert audit["assessed"] is True
    assert audit["tier"] in {"diagnostic_only", "falsifiable_diagnostic"}
    assert audit["evidence_matrix"]["candidate_action_alternatives_supplied"] is True
    assert audit["evidence_matrix"]["falsification_controls_supplied"] is True
    assert "candidate_actions_represent_relevant_agent_options" in audit["required_assumptions"]


def test_final_cause_result_contains_sfm_identifiability_support():
    result = infer_final_cause(_strong_payload())
    ident = result["sfm_identifiability_support"]
    assert ident["assessed"] is True
    assert ident["tier"] in {"partially_identifiable", "strongly_supported"}
    assert ident["can_claim_intent"] is True
    assert ident["evidence_matrix"]["causal_action_goal_effect_identified"] is True
    assert ident["evidence_matrix"]["twin_policy_changes_when_goal_removed"] is True
    assert result["authority_status"] in {"partial_sfm_identification", "strong_diagnostic_sfm_support"}
    assert "SFM_IDENT_CAN_REPORT_INTENT_DIAGNOSTICALLY" in result["reason_codes"]


def test_zero_effect_blocks_partial_identification():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "candidate_actions": [
                {"action": "answer_directly", "expected_success": 0.95, "expected_outcomes": {"task_success": 0.95}},
                {"action": "ask_clarification", "expected_success": 0.60, "expected_outcomes": {"task_success": 0.60}},
            ],
            "scm_graph": {
                "nodes": ["agent_action", "task_success", "context"],
                "edges": [["context", "agent_action"]],
            },
        }
    )
    ident = result["sfm_identifiability_support"]
    assert ident["evidence_matrix"]["zero_effect_identification"] is True
    assert ident["partially_identifiable"] is False
    assert result["inferred"] is False
    assert "SFM_IDENT_ZERO_EFFECT_BLOCKS_PARTIAL_IDENTIFICATION" in result["reason_codes"]
