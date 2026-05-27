from amantia.causal_core.final import build_intentional_intervention, infer_final_cause


def test_do_star_expression_surface():
    intervention = build_intentional_intervention(
        action_variable="agent_action",
        selected_action="ask_clarification",
        goal="task_success",
        agent={"agent_id": "assistant_agent"},
    )
    assert intervention.expression == "do*(agent_action=ask_clarification | agent=assistant_agent, goal=task_success)"


def test_final_cause_diagnostic_surface():
    result = infer_final_cause({
        "observed_action": "ask_clarification",
        "action_variable": "agent_action",
        "candidate_goals": ["task_success"],
        "candidate_actions": [
            {"action": "answer_directly", "expected_success": 0.52, "risk": "medium", "harm_probability": 0.08},
            {"action": "ask_clarification", "expected_success": 0.78, "risk": "low", "harm_probability": 0.01},
        ],
        "scm_graph": {
            "nodes": ["agent_action", "task_success", "ambiguity"],
            "edges": [["ambiguity", "agent_action"], ["agent_action", "task_success"]],
        },
    })
    assert result["most_likely_goal"] == "task_success"
    assert result["intentional_intervention"]["expression"].startswith("do*(agent_action=ask_clarification")
    assert "SFM_ACTION_PREFERS_GOAL" in result["reason_codes"]
