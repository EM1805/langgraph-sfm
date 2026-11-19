"""Research-only cross-agent experience transfer advisor for SFM.

Donor outcome observations can be proposed as diagnostic forecasts, never as
causal proof or permission to execute actions. All policy choices are
calibration-only. No original monitor/gate code is changed. Donor verification
flags and mechanism labels are trusted inputs, not cryptographic attestations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value.strip()


@dataclass(frozen=True)
class SFMExperience:
    agent_id: str
    run_id: str
    context: str
    mechanism: str
    action: str
    outcome: int
    observed_step: int
    evidence_id: str
    verified: bool = False

    def __post_init__(self) -> None:
        for key in ("agent_id", "run_id", "context", "mechanism", "action", "evidence_id"):
            object.__setattr__(self, key, _text(getattr(self, key), key))
        if type(self.outcome) is not int or self.outcome not in (0, 1):
            raise ValueError("outcome must be observed binary 0/1")
        if type(self.observed_step) is not int or self.observed_step < 0:
            raise ValueError("observed_step must be nonnegative integer")
        if type(self.verified) is not bool:
            raise ValueError("verified must be bool")


@dataclass(frozen=True)
class SFMTransferQuery:
    target_agent: str
    run_id: str
    context: str
    mechanism: str
    action: str
    as_of_step: int

    def __post_init__(self) -> None:
        for key in ("target_agent", "run_id", "context", "mechanism", "action"):
            object.__setattr__(self, key, _text(getattr(self, key), key))
        if type(self.as_of_step) is not int or self.as_of_step <= 0:
            raise ValueError("as_of_step must be a positive integer")


@dataclass(frozen=True)
class SFMPrediction:
    status: str
    policy: str
    probability: float | None = None
    support: int = 0
    donor_agents: int = 0
    evidence_ids: tuple[str, ...] = ()
    reason: str = ""
    checked_records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "policy": self.policy,
            "probability": self.probability,
            "support": self.support,
            "donor_agents": self.donor_agents,
            "evidence_ids": list(self.evidence_ids),
            "reason": self.reason,
            "checked_records": self.checked_records,
            "may_authorize_action": False,
        }


class SFMTransferAdvisor:
    """Optional diagnostic forecasts using verified, prior cross-agent records.

    Policies: none/global/exact/mechanism/selected. The global policy is a
    baseline only: calibration cannot select it for operational advice.
    Selected is a frozen map from mechanism to exact, mechanism, or none.
    """

    POLICIES = ("none", "global", "exact", "mechanism", "selected")
    TIERS = ("none", "global", "exact", "mechanism")

    def __init__(
        self, experiences: Iterable[SFMExperience], *,
        min_support: int = 4, min_agents: int = 2, max_donors: int = 160,
        calibrated: Mapping[str, str] | None = None,
    ) -> None:
        self._records = tuple(experiences)
        if any(not isinstance(r, SFMExperience) for r in self._records):
            raise TypeError("all donor records must be SFMExperience")
        if not (min_support >= 1 and min_agents >= 1 and max_donors >= min_support):
            raise ValueError("invalid donor limits")
        self.min_support = min_support
        self.min_agents = min_agents
        self.max_donors = max_donors
        self.calibrated = dict(calibrated or {})
        if any(t not in self.TIERS for t in self.calibrated.values()):
            raise ValueError("unknown calibrated policy")
        evidence_ids = [r.evidence_id for r in self._records]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("repeated evidence_id")

    @property
    def stored_records(self) -> int:
        return len(self._records)

    def with_calibration(self, mapping: Mapping[str, str]) -> "SFMTransferAdvisor":
        return SFMTransferAdvisor(
            self._records, min_support=self.min_support, min_agents=self.min_agents,
            max_donors=self.max_donors, calibrated=mapping,
        )

    def predict(self, q: SFMTransferQuery, policy: str = "selected") -> SFMPrediction:
        if not isinstance(q, SFMTransferQuery):
            raise TypeError("query must be SFMTransferQuery")
        if policy not in self.POLICIES:
            raise ValueError("unknown policy")
        if policy == "selected":
            policy = self.calibrated.get(q.mechanism, "none")
        if policy == "none":
            return SFMPrediction(
                status="ABSTAIN", policy=policy,
                reason="no safe transfer policy selected",
            )
        eligible = []
        examined = 0
        for record in self._records:
            examined += 1
            if (
                not record.verified or record.observed_step >= q.as_of_step
                or record.agent_id == q.target_agent or record.run_id == q.run_id
                or record.action != q.action
            ):
                continue
            if policy in ("exact", "mechanism") and record.mechanism != q.mechanism:
                continue
            if policy == "exact" and record.context != q.context:
                continue
            eligible.append(record)
        chosen = sorted(
            eligible, key=lambda r: (-r.observed_step, r.evidence_id),
        )[:self.max_donors]
        agents = len({r.agent_id for r in chosen})
        if len(chosen) < self.min_support or agents < self.min_agents:
            return SFMPrediction(
                status="ABSTAIN", policy=policy, support=len(chosen),
                donor_agents=agents, reason="insufficient independent donor evidence",
                checked_records=examined,
            )
        estimate = (1.0 + sum(r.outcome for r in chosen)) / (len(chosen) + 2.0)
        return SFMPrediction(
            status="ADVISORY_ONLY", policy=policy, probability=estimate,
            support=len(chosen), donor_agents=agents,
            evidence_ids=tuple(r.evidence_id for r in chosen),
            reason="observational donor estimate; independent gate unchanged",
            checked_records=examined,
        )

    def calibrate(
        self, calibration: Sequence[tuple[SFMTransferQuery, int]], *,
        min_cases: int = 8, min_improvement: float = 0.002,
    ) -> tuple["SFMTransferAdvisor", dict[str, Any]]:
        """Select mechanism-compatible tiers using calibration outcomes only.

        A fallback forecast of 0.5 gives Brier score 0.25 for binary outcomes.
        Scoring the global donor pool is for a negative control: it cannot be
        chosen for selected transfer, even if validation happens to favor it.
        """
        if not calibration:
            raise ValueError("calibration cannot be empty")
        grouped: dict[str, list[tuple[SFMTransferQuery, int]]] = {}
        for query, label in calibration:
            if (not isinstance(query, SFMTransferQuery)
                    or type(label) is not int or label not in (0, 1)):
                raise ValueError("invalid calibration example")
            grouped.setdefault(query.mechanism, []).append((query, label))
        selections = {}
        receipts = {}
        for mechanism, pairs in sorted(grouped.items()):
            losses = {}
            coverage = {}
            for tier in self.TIERS:
                errors = []
                supported = 0
                for query, observed in pairs:
                    predicted = self.predict(query, policy=tier)
                    probability = predicted.probability if predicted.probability is not None else .5
                    errors.append((probability - observed) ** 2)
                    supported += predicted.probability is not None
                losses[tier] = sum(errors) / len(errors)
                coverage[tier] = supported / len(pairs)
            loss, tier = min((losses[t], t) for t in ("exact", "mechanism"))
            if len(pairs) < min_cases or loss > losses["none"] - min_improvement:
                tier = "none"
            selections[mechanism] = tier
            receipts[mechanism] = {
                "cases": len(pairs), "losses": losses, "coverage": coverage,
                "selected": tier, "status": "FROZEN_CALIBRATION_ONLY",
            }
        return self.with_calibration(selections), receipts

    def advise(
        self, state: Mapping[str, Any], *,
        query_key: str = "sfm_transfer_query",
        output_key: str = "sfm_transfer_advice",
    ) -> dict[str, Any]:
        """LangGraph sidecar. Never writes sfm_gate_status or review flags."""
        raw = state.get(query_key)
        if not isinstance(raw, Mapping):
            return {output_key: SFMPrediction(
                status="ABSTAIN", policy="none",
                reason="missing explicit transfer contract",
            ).to_dict()}
        try:
            query = SFMTransferQuery(**dict(raw))
            prediction = self.predict(query).to_dict()
        except (TypeError, ValueError) as exc:
            prediction = SFMPrediction(
                status="ABSTAIN", policy="none",
                reason=f"invalid transfer contract: {type(exc).__name__}",
            ).to_dict()
        return {output_key: prediction}


class SFMOnlineTransferGuard:
    """Revoke frozen transfer after *later* independently observed feedback.

    This opt-in monitor is local to one target agent/run/context/mechanism/action.
    It abstains for the remainder of a run after sufficiently poor outcomes.
    It cannot authorize any action or change the separate SFM governance gate.
    """

    def __init__(
        self, advisor: SFMTransferAdvisor, *, window: int = 12,
        min_feedback: int = 6, excess_loss: float = 0.10,
    ) -> None:
        if not (1 <= min_feedback <= window) or excess_loss < 0:
            raise ValueError("invalid sequential feedback settings")
        self.advisor = advisor
        self.window = window
        self.min_feedback = min_feedback
        self.excess_loss = excess_loss
        self._pending: dict[SFMTransferQuery, SFMPrediction] = {}
        self._seen_evidence: set[str] = set()
        self._feedback: dict[tuple[str, ...], list[tuple[float, int]]] = {}
        self._revoked: set[tuple[str, ...]] = set()

    @staticmethod
    def _key(q: SFMTransferQuery) -> tuple[str, ...]:
        return (q.target_agent, q.run_id, q.context, q.mechanism, q.action)

    def forecast(self, q: SFMTransferQuery) -> SFMPrediction:
        if q in self._pending:
            raise ValueError("repeated pending prediction")
        key = self._key(q)
        if key in self._revoked:
            prediction = SFMPrediction(
                status="ABSTAIN", policy="none",
                reason="negative transfer observed on prior, independently verified outcomes",
            )
        else:
            prediction = self.advisor.predict(q, "selected")
        self._pending[q] = prediction
        return prediction

    def observe(self, q: SFMTransferQuery, outcome: int, evidence_id: str) -> bool:
        """Feedback cannot affect its own forecast: forecast must exist first."""
        if q not in self._pending:
            raise ValueError("observation without a prior forecast")
        if type(outcome) is not int or outcome not in (0, 1):
            raise ValueError("outcome must be observed binary 0/1")
        evidence_id = _text(evidence_id, "evidence_id")
        if evidence_id in self._seen_evidence:
            raise ValueError("feedback evidence duplicated")
        self._seen_evidence.add(evidence_id)
        prior = self._pending.pop(q)
        key = self._key(q)
        if prior.probability is not None:
            history = self._feedback.setdefault(key, [])
            history.append((prior.probability, outcome))
            if len(history) > self.window:
                history.pop(0)
            if len(history) >= self.min_feedback:
                donor_loss = sum((p - y) ** 2 for p, y in history) / len(history)
                abstain_loss = sum((.5 - y) ** 2 for _, y in history) / len(history)
                if donor_loss > abstain_loss + self.excess_loss:
                    self._revoked.add(key)
        return key in self._revoked

    def revoked(self, q: SFMTransferQuery) -> bool:
        return self._key(q) in self._revoked
