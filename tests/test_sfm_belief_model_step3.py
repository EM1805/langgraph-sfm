from amantia.causal_core.final import assess_agent_beliefs, infer_final_cause


def test_belief_graph_aligned_with_real_graph_is_reported():
    payload = {
        "observed_action": "answer_directly",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
        "candidate_actions": [
            {"action": "answer_directly", "expected_success": 0.9, "risk": "low", "harm_probability": 0.01},
            {"action": "ask_clarification", "expected_success": 0.6, "risk": "none", "harm_probability": 0.0},
        ],
        "scm_graph": {
            "nodes": ["agent_action", "task_success"],
            "edges": [["agent_action", "task_success"]],
        },
        "agent": {
            "agent_id": "assistant_agent",
            "belief_graph": {
                "nodes": ["agent_action", "task_success"],
                "edges": [["agent_action", "task_success"]],
            },
        },
    }
    assessment = assess_agent_beliefs(payload)
    assert assessment["assessed"] is True
    assert assessment["real_has_path"] is True
    assert assessment["belief_has_path"] is True
    assert assessment["belief_agrees_with_real"] is True
    assert assessment["belief_error_type"] == "none"
    assert "SFM_AGENT_BELIEF_ALIGNED_WITH_REAL_PATH" in assessment["reason_codes"]


def test_false_positive_agent_belief_can_support_intent_but_flags_real_zero_effect():
    result = infer_final_cause(
        {
            "observed_action": "take_shortcut",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "candidate_actions": [
                {"action": "take_shortcut", "expected_success": 0.95, "risk": "low", "harm_probability": 0.01},
                {"action": "standard_route", "expected_success": 0.55, "risk": "none", "harm_probability": 0.0},
            ],
            "scm_graph": {
                "nodes": ["agent_action", "task_success", "weather"],
                "edges": [["weather", "task_success"]],
            },
            "agent": {
                "agent_id": "mistaken_agent",
                "belief_graph": {
                    "nodes": ["agent_action", "task_success"],
                    "edges": [["agent_action", "task_success"]],
                },
            },
        }
    )
    assert result["belief_support"]["belief_error_type"] == "false_positive_belief"
    assert result["belief_support"]["intent_under_agent_beliefs"] is True
    assert result["belief_support"]["real_world_goal_path_supported"] is False
    assert "SFM_REAL_GRAPH_SUGGESTS_ZERO_GOAL_EFFECT" in result["reason_codes"]
    assert "SFM_AGENT_BELIEF_FALSE_POSITIVE_VS_REAL_GRAPH" in result["reason_codes"]
    assert "agent_belief_graph_diverges_from_real_graph" in result["limits"]
    # Step 23 preserves the belief-based hypothesis but withholds claim authority:
    # the agent may have acted for the goal under its beliefs, but the real graph
    # says the action does not actually affect that goal.
    assert result["intent_hypothesis_supported"] is True
    assert result["intent_claim_authorized"] is False
    assert result["inferred"] is False
    assert result["intent_score"] >= 0.8


def test_missing_belief_graph_is_explicit_limit_not_implicit_agent_knowledge():
    result = infer_final_cause(
        {
            "observed_action": "answer_directly",
            "action_variable": "agent_action",
            "candidate_goals": ["task_success"],
            "candidate_actions": [
                {"action": "answer_directly", "expected_success": 0.95, "risk": "low", "harm_probability": 0.01},
                {"action": "ask_clarification", "expected_success": 0.60, "risk": "none", "harm_probability": 0.0},
            ],
            "scm_graph": {
                "nodes": ["agent_action", "task_success"],
                "edges": [["agent_action", "task_success"]],
            },
        }
    )
    assert result["belief_support"]["belief_model_supplied"] is False
    assert result["belief_support"]["belief_error_type"] == "missing_belief_graph"
    assert "agent_belief_graph_not_supplied" in result["limits"]
    assert "SFM_AGENT_BELIEF_GRAPH_MISSING" in result["reason_codes"]
