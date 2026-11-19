"""Protocol Genesis: falsification and non-regression for bounded SFM monitor history.

Cases distinguish an actual cross-run memory leak from intended within-run
carry-over of a block/review decision. No external LLM or network needed.
"""
import pytest
from sfm_langgraph.monitor import (
    SFMAgentMonitor, SFMAgentMonitorConfig, build_sfm_run_report,
)


def analysis(gate="allow"):
    return {
        "gate_status": gate,
        "deception_risk": "low",
        "side_effect_risk": "low",
        "intent_hypothesis_supported": True,
        "intent_claim_authorized": True,
        "primary_intent": "complete_task",
        "observed_action": "noop",
    }


def advance(monitor, prior, run_id, gate="allow"):
    state = {
        "run_id": run_id,
        "sfm_analysis": analysis(gate),
    }
    if prior is not None:
        state.update(prior)
    return monitor(state)


def test_normal_compatible_timeline_and_allow_baseline():
    monitor = SFMAgentMonitor(SFMAgentMonitorConfig(max_events=3))
    first = advance(monitor, None, "alpha")
    second = advance(monitor, first, "alpha")
    assert first["sfm_gate_status"] == second["sfm_gate_status"] == "allow"
    assert [e["step_index"] for e in second["sfm_monitor_events"]] == [1, 2]
    assert second["sfm_monitor"]["total_events"] == 2


def test_context_switch_discards_foreign_history_and_gate():
    monitor = SFMAgentMonitor(SFMAgentMonitorConfig(max_events=2))
    previous = advance(monitor, None, "old", "block")
    assert previous["sfm_gate_status"] == "block"
    new = advance(monitor, previous, "new", "allow")
    assert new["sfm_gate_status"] == "allow"
    assert new["requires_human_review"] is False
    assert len(new["sfm_monitor_events"]) == 1
    assert new["sfm_monitor_events"][0]["event_id"] == "new:1"
    assert new["sfm_monitor"]["run_id"] == "new"
    assert new["sfm_monitor"]["blocked_events"] == 0


def test_bounded_history_does_not_repeat_event_ids():
    monitor = SFMAgentMonitor(SFMAgentMonitorConfig(max_events=2))
    state = None
    indices = []
    for _ in range(5):
        state = advance(monitor, state, "session:with:colon")
        indices.append(state["sfm_monitor_events"][-1]["step_index"])
    assert indices == [1, 2, 3, 4, 5]
    assert [e["event_id"] for e in state["sfm_monitor_events"]] == [
        "session:with:colon:4", "session:with:colon:5"
    ]
    assert state["sfm_monitor"]["total_events"] == 2


def test_evicted_block_is_not_forgotten_inside_same_run():
    monitor = SFMAgentMonitor(SFMAgentMonitorConfig(max_events=2))
    first = advance(monitor, None, "persistent", "block")
    second = advance(monitor, first, "persistent", "allow")
    third = advance(monitor, second, "persistent", "allow")
    assert [e["gate_status"] for e in third["sfm_monitor_events"]] == ["allow", "allow"]
    assert third["sfm_monitor"]["blocked_events"] == 0  # retained window only
    assert third["sfm_gate_status"] == "block"  # cumulative gate not downgraded
    assert third["requires_human_review"] is True
    assert "SFM_HISTORY_GATE_RETAINED" in third["sfm_monitor"]["reason_codes"]


def test_review_is_retained_until_new_run():
    monitor = SFMAgentMonitor(SFMAgentMonitorConfig(max_events=1))
    one = advance(monitor, None, "review-run", "review")
    two = advance(monitor, one, "review-run", "allow")
    assert two["sfm_gate_status"] == "review"
    assert two["requires_human_review"]
    three = advance(monitor, two, "fresh", "allow")
    assert three["sfm_gate_status"] == "allow"


def test_unscoped_injected_prior_event_is_not_imported():
    monitor = SFMAgentMonitor()
    result = monitor({
        "run_id": "isolated",
        "sfm_analysis": analysis("allow"),
        "sfm_monitor_events": [
            {"step_index": 99, "gate_status": "block", "reason_codes": []}
        ],
    })
    assert result["sfm_gate_status"] == "allow"
    assert [e["step_index"] for e in result["sfm_monitor_events"]] == [1]


def test_standalone_precomputed_report_keeps_original_semantics():
    report = build_sfm_run_report([{
        "step_index": 1, "gate_status": "block",
        "risk_score": 0.9, "requires_human_review": True
    }], run_id="explicit")
    assert report["final_gate_status"] == "block"
    assert report["total_events"] == 1


def test_invalid_zero_window_rejected():
    with pytest.raises(ValueError, match="max_events"):
        SFMAgentMonitor(SFMAgentMonitorConfig(max_events=0))
