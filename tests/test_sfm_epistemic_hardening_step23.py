from amantia.causal_core.final import infer_final_cause, run_sfm_validation_benchmark


def _high_score_payload_without_graph():
    return {
        "observed_action": "answer_directly",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
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
        "negative_control_goals": ["unrelated_metric"],
        # The defect: this diagnostic evidence is strong, but no real SCM graph
        # is supplied.  Step 23 must preserve the hypothesis but withhold claim authority.
        "scm_graph": {},
    }


def test_missing_real_graph_supports_hypothesis_but_blocks_claim_authority():
    result = infer_final_cause(_high_score_payload_without_graph())
    assert result["intent_score"] >= 0.6
    assert result["intent_hypothesis_supported"] is True
    assert result["intent_claim_authorized"] is False
    assert result["inferred"] is False
    assert result["sfm_identifiability_support"]["can_claim_intent"] is False
    assert "SFM_IDENT_MISSING_REAL_GRAPH_BLOCKS_CLAIM_AUTHORITY" in result["reason_codes"]
    assert "real_scm_graph_not_supplied_claim_authority_withheld" in result["limits"]
    assert result["alignment_summary"]["verdict"] == "plausible_but_unidentified"
    assert result["alignment_summary"]["gate_status"] == "review"


def test_result_exposes_three_epistemic_execution_flags_on_authorized_case():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "negative_control_goals": ["unrelated_metric"],
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
            "agent": {
                "belief_graph": {
                    "nodes": ["agent_action", "task_success", "unrelated_metric"],
                    "edges": [["agent_action", "task_success"]],
                }
            },
        }
    )
    assert result["intent_hypothesis_supported"] is True
    assert result["intent_claim_authorized"] is True
    assert result["inferred"] is True
    assert result["governance_execution_allowed"] in {True, False}
    assert "SFM_INTENT_CLAIM_AUTHORIZED" in result["reason_codes"]


def test_synthetic_validation_benchmark_passes_core_epistemic_cases():
    report = run_sfm_validation_benchmark()
    assert report["passed"] is True
    assert report["total_cases"] >= 5
    assert report["false_positive_claims"] == 0
    assert report["claim_authorization_accuracy"] == 1.0
    assert "SFM_VALIDATION_BENCHMARK_PASSED" in report["reason_codes"]
