# Protocol Genesis × SFM — selective experience transfer, v0.1

**State: RESEARCH_ONLY_NOT_PROMOTED.** This experiment extends the already
verified monitor-run isolation from PR #1. It **does not modify** the SFM
monitor, structural-final-models evaluator, authority proof, or action gate.
The new module is **not exported as a default public API** and must be
explicitly imported as sfm_langgraph.transfer.

## Falsifiable hypothesis

Does donor experience from other agents help forecast a binary outcome on a
new agent/context **without hiding negative transfer**, when the independently
validated regime/mechanism signature matches? Can subsequent feedback revoke a
harmful transfer before it persists indefinitely?

## Experimental contract

- Donor records: immutable objects, explicit source agent/run, context,
  mechanism, action, binary outcome, evidence ID, time index, and a caller-
  supplied verified flag. The flag is **not cryptographic verification**.
- Source records are usable only when observed before the query, verified,
  from a different agent and run, and for the same action.
- Exact transfer requires both context and mechanism to match.
  Mechanism transfer allows a new context but requires the mechanism to match.
- Global transfer disregards mechanism and exists **only as a negative control**.
- Calibration chooses among exact/mechanism/abstain by Brier score measured on
  independent calibration cases, never on the designated test.
- Minimum support: 4 records from at least 2 donor agents; at most 160
  accepted records per forecast.
- An optional sequential feedback guard compares the rolling donor Brier loss
  with an abstaining 0.5 forecast: window=12, min=6 observed outcomes,
  margin=0.10. It **only revokes** a transfer for the current target run.
- Every forecast is created **before** its outcome is observed. There is no
  test-label exposure in the current forecast, only prequential feedback.
- The adapter returns sfm_transfer_advice only. It never sets
  sfm_gate_status, requires_human_review, or any authorization field.

## Benchmark and reported results

A deliberately authored Bernoulli **synthetic** simulation with 432 donor
records, 375 independent calibration observations and **500** evaluation
observations (5 families × 4 test seeds × 25 events):

| Policy | Mean Brier (lower better) | Coverage |
|---|---:|---:|
| No transfer / abstain | 0.250000 | 0% |
| Global unrestricted | 0.553679 | 100% |
| Fixed exact | 0.395770 | 60% |
| Fixed mechanism | 0.420916 | 80% |
| Selected, frozen | 0.313029 | 60% |
| Selected + feedback revocation | **0.242427** | 44.8% |

The guarded policy is slightly below the 0.25 abstention baseline **in this
constructed dataset**, but **not proven better in general**. In the
unannounced-drift group specifically it still has Brier 0.381327, worse
than abstention at 0.25, although it improves on frozen selection at 0.734337.
The guard only abstains after at least six bad outcomes. Thus the central
negative-transfer failure is not solved.

A *declared* regime change yields a different mechanism signature and
abstention. But detecting the change is an **external prerequisite**, not
a capability demonstrated by the module. New-context transfer is simulated
for one shareable mechanism, not tested on actual user/agent observations.

### Explicitly exposed preliminary results

Earlier exploratory seeds 3109/3119/3121/3137 accidentally covered only one
conditional context; results from that version are invalid for broad claims.
A corrected exploratory 5102/5107/5113/5119 set was inspected while adding
the feedback veto, so it is **exposed development evidence**, not a new blind
test. The posted 6101/6107/6113/6121 evaluation uses the frozen policy/guard
settings described above. Do not reuse it for hyperparameter tuning and then
claim a new sealed experiment.

## Reproduce

From repo root with dev/test dependencies installed:

    python -m pytest -q tests/test_sfm_transfer_protocol.py
    python -m benchmarks.sfm_transfer_benchmark --output transfer-evidence/result.json

GitHub Actions runs this command and saves the JSON evidence as a downloadable
workflow artifact. No repository original is modified in-place, and the PR is
stacked on the *draft* monitor-run-isolation PR.

## Scope and blockers

The scheme infers observational predictive utility, **not causal effects**.
Mechanism names, verified flags, and outcome labels are supplied externally.
Synthetic data do not demonstrate capacity to learn those quantities from
real agents. A strong static baseline and external/domain-independent cases
remain mandatory before any promotion. CPU/RAM and index overhead are not
measured; full-record scans are a known scaling limitation.

A future study should compare a fixed guard at equal observation/compute
budget, adversarial and unannounced drift, donor tampering, externally labeled
outcomes and independent agent families. Until then, keep transfer disabled
by default and the main SFM gate authoritative.
