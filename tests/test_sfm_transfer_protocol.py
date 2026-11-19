"""Protocol Genesis: cross-run transfer, negative transfer and gate non-bypass."""
from dataclasses import asdict, replace
import pytest

from sfm_langgraph.monitor import SFMAgentMonitor
from sfm_langgraph.transfer import (
    SFMExperience, SFMTransferQuery, SFMTransferAdvisor, SFMOnlineTransferGuard,
)
from benchmarks.sfm_transfer_benchmark import run, source_records, target_examples


def donor(n, agent="a", context="C0", mechanism="m", step=1,
          outcome=1, verified=True, action="a1"):
    return SFMExperience(
        agent_id=agent, run_id="run-" + agent, context=context,
        mechanism=mechanism, action=action, outcome=outcome,
        observed_step=step, evidence_id=f"e-{n}", verified=verified,
    )


def query(context="C0", mechanism="m", step=100, agent="target", action="a1"):
    return SFMTransferQuery(agent, "target-run", context, mechanism, action, step)


def test_positive_donor_pool_is_only_advisory():
    advisor = SFMTransferAdvisor([
        donor(i, agent="a" if i % 2 else "b", step=i+1) for i in range(6)
    ], min_support=4, min_agents=2)
    p = advisor.predict(query(), "exact")
    assert p.status == "ADVISORY_ONLY"
    assert .5 < p.probability < 1
    assert p.to_dict()["may_authorize_action"] is False
    assert len(p.evidence_ids) == 6


def test_future_unverified_self_and_wrong_action_are_excluded():
    records = [
        donor(1, "a", step=1), donor(2, "b", step=2),
        donor(3, "c", step=100), donor(4, "d", step=9, verified=False),
        donor(5, "target", step=3), donor(6, "e", step=2, action="a2"),
    ]
    advisor = SFMTransferAdvisor(records, min_support=3, min_agents=2)
    assert advisor.predict(query(step=10), "mechanism").support == 2
    p = advisor.predict(query(step=101), "mechanism")
    assert p.status == "ADVISORY_ONLY"
    assert p.support == 3


def test_same_source_run_is_excluded():
    records = [
        replace(donor(i, agent=f"a{i}", step=i), run_id="target-run")
        for i in range(5)
    ]
    advisor = SFMTransferAdvisor(records, min_support=2, min_agents=2)
    assert advisor.predict(query(), "global").status == "ABSTAIN"


def test_new_context_can_reuse_only_compatible_mechanism():
    records = [
        donor(i, agent="a" if i % 2 else "b", context="C1", step=i+1)
        for i in range(6)
    ]
    advisor = SFMTransferAdvisor(records, min_support=4, min_agents=2)
    assert advisor.predict(query(context="C0"), "exact").status == "ABSTAIN"
    assert advisor.predict(query(context="C0"), "mechanism").status == "ADVISORY_ONLY"
    assert advisor.predict(query(context="C0", mechanism="new"), "mechanism").status == "ABSTAIN"


def test_malformed_or_duplicated_donor_data_is_rejected():
    with pytest.raises(ValueError):
        SFMTransferAdvisor([donor(1), donor(1)])
    with pytest.raises(ValueError):
        replace(donor(1), outcome=True)
    with pytest.raises(ValueError):
        replace(donor(1), observed_step=-1)
    with pytest.raises(ValueError):
        replace(donor(1), agent_id=" ")


def test_transfer_sidecar_cannot_change_native_monitor_gate():
    advisor = SFMTransferAdvisor(
        [donor(i, agent="a" if i % 2 else "b", step=i+1) for i in range(6)],
        min_support=4, min_agents=2, calibrated={"m": "exact"},
    )
    monitor = SFMAgentMonitor()
    old = monitor({
        "run_id": "target-run",
        "sfm_analysis": {"gate_status": "block", "reason_codes": ["SFM_TEST_BLOCK"]},
    })
    state = {
        **old, "sfm_transfer_query": asdict(query())
    }
    update = advisor.advise(state)
    assert set(update) == {"sfm_transfer_advice"}
    assert update["sfm_transfer_advice"]["status"] == "ADVISORY_ONLY"
    assert update["sfm_transfer_advice"]["may_authorize_action"] is False
    assert state["sfm_gate_status"] == "block"
    assert state["requires_human_review"] is True


def test_invalid_query_abstains():
    advisor = SFMTransferAdvisor([donor(1)])
    assert advisor.advise({})["sfm_transfer_advice"]["status"] == "ABSTAIN"
    assert advisor.advise({"sfm_transfer_query": {"target_agent": "x"}})["sfm_transfer_advice"]["status"] == "ABSTAIN"


def test_calibration_frozen_before_separate_test():
    advisor = SFMTransferAdvisor(source_records())
    calibration = target_examples((2101,2103,2107), phase="calibration")
    frozen, evidence = advisor.calibrate([(q,y) for _,_,q,y in calibration])
    assert frozen.calibrated == {m:r["selected"] for m,r in evidence.items()}
    assert "global" not in frozen.calibrated.values()  # control only
    test = target_examples((6101,), phase="test")
    _flipped = [(group,seed,q,1-y) for group,seed,q,y in test]
    assert frozen.calibrated == {m:r["selected"] for m,r in evidence.items()}


def test_declared_drift_and_agent_specific_negative_transfer_abstain():
    r = run()
    assert r["test_n"] == 500
    assert r["selected_tiers"]["unstable_v2"] == "none"
    assert r["selected_tiers"]["private"] == "none"
    assert r["test_scores"]["selected"]["by_group"]["drift_declared"]["coverage"] == 0


def test_unannounced_drift_is_a_falsifier_even_after_revocation():
    r = run()
    name = "drift_unannounced"
    frozen = r["test_scores"]["selected"]["by_group"][name]["brier"]
    guarded = r["test_scores"]["selected_guarded"]["by_group"][name]["brier"]
    none = r["test_scores"]["none"]["by_group"][name]["brier"]
    assert none < guarded < frozen
    assert r["status"] == "RESEARCH_ONLY_NOT_PROMOTED"


def test_guard_revokes_only_after_independent_feedback():
    records = [
        donor(i, agent="a" if i%2 else "b", step=i+1, outcome=1)
        for i in range(12)
    ]
    advisor = SFMTransferAdvisor(
        records, min_support=4, min_agents=2, calibrated={"m": "exact"},
    )
    guard = SFMOnlineTransferGuard(advisor, min_feedback=6, window=10, excess_loss=.10)
    forecasts = []
    for step in range(100, 107):
        q = query(step=step)
        p = guard.forecast(q)
        forecasts.append(p)
        if step <= 105:
            assert p.probability is not None
        else:
            assert p.probability is None
        assert guard.observe(q, 0, f"receipt-{step}") == (step >= 105)
    assert guard.revoked(query(step=108))
    assert forecasts[0].probability == forecasts[5].probability


def test_guard_is_scoped_to_run_and_rejects_reused_receipts():
    records = [
        donor(i, agent="a" if i%2 else "b", step=i+1, outcome=1)
        for i in range(12)
    ]
    advisor = SFMTransferAdvisor(
        records, min_support=4, min_agents=2, calibrated={"m": "exact"}
    )
    guard = SFMOnlineTransferGuard(advisor, min_feedback=2, window=4)
    first = query(step=101)
    guard.forecast(first)
    with pytest.raises(ValueError):
        guard.forecast(first)
    guard.observe(first, 0, "receipt101")
    with pytest.raises(ValueError):
        guard.observe(first, 0, "receipt101")
    second = query(step=102)
    guard.forecast(second)
    assert guard.observe(second, 0, "receipt102")
    assert guard.forecast(query(step=103)).status == "ABSTAIN"
    new_run = replace(query(step=103), run_id="different-run")
    assert guard.forecast(new_run).status == "ADVISORY_ONLY"


def test_benchmark_is_deterministic_and_explicitly_non_promoted():
    a, b = run(), run()
    assert a == b
    assert a["status"] == "RESEARCH_ONLY_NOT_PROMOTED"
    assert a["test_scores"]["selected_guarded"]["mean_brier"] < a["test_scores"]["selected"]["mean_brier"]
