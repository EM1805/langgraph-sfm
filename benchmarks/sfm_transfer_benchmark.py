"""Controlled synthetic cross-agent transfer experiment (research only).

Source, calibration, and test seeds are distinct. Test labels never select
policy tiers; guarded mode consumes labels only *after* forecasting each event.
Simulation is authored; transfer quality is not a real-world causal finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from sfm_langgraph.transfer import (
    SFMExperience, SFMTransferQuery, SFMTransferAdvisor, SFMOnlineTransferGuard,
)

SOURCE_SEED = 1999
CALIBRATION_SEEDS = (2101, 2103, 2107)
TEST_SEEDS = (6101, 6107, 6113, 6121)
GROUPS = (
    "shared_new_context", "conditional_context",
    "private_negative_transfer", "drift_unannounced", "drift_declared",
)
POLICIES = ("none", "global", "exact", "mechanism", "selected")


def source_records():
    rng = random.Random(SOURCE_SEED)
    records = []
    step = 1
    for mechanism in ("shared", "conditional", "private", "unstable"):
        for agent in ("donor-a", "donor-b", "donor-c"):
            for ctx in ("C0", "C1"):
                p = {
                    "shared": .72,
                    "conditional": .88 if ctx == "C0" else .12,
                    "private": .86,
                    "unstable": .86,
                }[mechanism]
                for n in range(18):
                    records.append(SFMExperience(
                        agent_id=agent, run_id=f"{agent}-{mechanism}-{ctx}",
                        context=ctx, mechanism=mechanism, action="execute",
                        outcome=int(rng.random() < p), observed_step=step,
                        evidence_id=f"{mechanism}-{agent}-{ctx}-{n}",
                        verified=True,
                    ))
                    step += 1
    return records


def target_examples(seeds, *, phase):
    if phase not in ("calibration", "test"):
        raise ValueError(phase)
    cases = []
    for group in GROUPS:
        for seed in seeds:
            rng = random.Random(seed * 1447 + GROUPS.index(group) * 17011)
            if group == "shared_new_context":
                mechanism, context, p = "shared", "C2", .72
            elif group == "conditional_context":
                mechanism, context, p = "conditional", "C0", .88
            elif group == "private_negative_transfer":
                mechanism, context, p = "private", "C0", .10
            elif group == "drift_unannounced":
                mechanism, context, p = (
                    "unstable", "C0", .86 if phase == "calibration" else .11
                )
            else:
                mechanism, context, p = "unstable_v2", "C0", .11
            for index in range(25):
                # Unlike the superseded exploratory pilot, both contexts are
                # represented within each calibration/test seed.
                if group == "conditional_context":
                    context = "C0" if (seed + index) % 2 else "C1"
                    p = .88 if context == "C0" else .12
                query = SFMTransferQuery(
                    target_agent=f"target-{phase}",
                    run_id=f"{phase}-{group}-{seed}",
                    mechanism=mechanism, context=context, action="execute",
                    as_of_step=10_000 + index,
                )
                cases.append((group, seed, query, int(rng.random() < p)))
    return cases


def evaluate(advisor, cases):
    losses = {p: defaultdict(list) for p in POLICIES}
    covered = {p: defaultdict(int) for p in POLICIES}
    checks = {p: 0 for p in POLICIES}
    for group, _seed, query, label in cases:
        for policy in POLICIES:
            pred = advisor.predict(query, policy)
            estimate = pred.probability if pred.probability is not None else .5
            losses[policy][group].append((estimate - label) ** 2)
            covered[policy][group] += pred.probability is not None
            checks[policy] += pred.checked_records
    summary = {}
    for policy in POLICIES:
        per_group = {
            group: {
                "brier": round(mean(losses[policy][group]), 6),
                "n": len(losses[policy][group]),
                "coverage": round(
                    covered[policy][group] / len(losses[policy][group]), 6
                ),
            }
            for group in GROUPS
        }
        all_losses = [
            err for group in GROUPS for err in losses[policy][group]
        ]
        summary[policy] = {
            "mean_brier": round(mean(all_losses), 6),
            "coverage": round(sum(covered[policy].values()) / len(all_losses), 6),
            "record_checks_proxy": checks[policy],
            "by_group": per_group,
        }
    return summary


def evaluate_guarded(advisor, cases):
    guard = SFMOnlineTransferGuard(
        advisor, window=12, min_feedback=6, excess_loss=.10
    )
    losses = defaultdict(list)
    covered = defaultdict(int)
    revoked = defaultdict(int)
    for group, seed, query, label in cases:
        pred = guard.forecast(query)
        p = pred.probability if pred.probability is not None else .5
        losses[group].append((p - label) ** 2)
        covered[group] += pred.probability is not None
        revoked[group] += guard.observe(
            query, label, f"feedback-{group}-{seed}-{query.as_of_step}"
        )
    n = sum(len(v) for v in losses.values())
    return {
        "mean_brier": round(sum(sum(x) for x in losses.values()) / n, 6),
        "coverage": round(sum(covered.values()) / n, 6),
        "by_group": {
            g: {
                "brier": round(mean(losses[g]), 6),
                "coverage": round(covered[g] / len(losses[g]), 6),
                "revoked_observations": revoked[g],
                "n": len(losses[g]),
            }
            for g in GROUPS
        },
    }


def run():
    donors = source_records()
    advisor = SFMTransferAdvisor(donors, min_support=4, min_agents=2)
    calibration = target_examples(CALIBRATION_SEEDS, phase="calibration")
    frozen, receipts = advisor.calibrate(
        [(q, y) for _group, _seed, q, y in calibration],
        min_cases=12, min_improvement=.002,
    )
    test = target_examples(TEST_SEEDS, phase="test")
    scores = evaluate(frozen, test)
    scores["selected_guarded"] = evaluate_guarded(frozen, test)
    return {
        "status": "RESEARCH_ONLY_NOT_PROMOTED",
        "domain": "authored Bernoulli synthetic worlds; not live agent transfer",
        "source_seed": SOURCE_SEED,
        "calibration_seeds": list(CALIBRATION_SEEDS),
        "test_seeds": list(TEST_SEEDS),
        "exploratory_pilot": "3109-3137 and 5102-5119 results exposed, not sealed here",
        "donor_count": len(donors),
        "calibration_n": len(calibration),
        "test_n": len(test),
        "calibration_results": receipts,
        "selected_tiers": frozen.calibrated,
        "test_scores": scores,
        "definition": "Brier score lower is better; 0.5 forecast used on ABSTAIN",
        "blocked_claims": [
            "No empirical causal identification or general agent improvement.",
            "Mechanism and regime labels are supplied by the caller.",
            "Unannounced drift may be harmful before feedback revocation.",
            "Guarded test uses after-the-fact online feedback, not a zero-shot test.",
            "Verified provenance flags are trusted, not cryptographically proven.",
            "Record checks are not CPU/energy-comparable costs.",
            "No authorization or safety gate is changed by the advisor.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    payload = run()
    raw = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(raw, encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "test_n": payload["test_n"],
        "selected": payload["selected_tiers"],
        "scores": {
            key: {"mean_brier": val["mean_brier"], "coverage": val["coverage"]}
            for key, val in payload["test_scores"].items()
        },
        "sha256": hashlib.sha256(raw.encode()).hexdigest(),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
