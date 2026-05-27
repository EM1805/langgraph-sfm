from pathlib import Path

from amantia.causal_core.final import (
    build_external_sfm_panel_cases,
    run_sfm_external_panel_benchmark,
)


PANEL_PATH = Path(__file__).resolve().parents[1] / "data" / "action_event_panel.csv"


def test_external_panel_cases_are_built_from_longitudinal_panel():
    cases = build_external_sfm_panel_cases(str(PANEL_PATH))
    assert len(cases) == 4
    names = {case.name for case in cases}
    assert "panel_throughput_claim_authorized_with_domain_graph" in names
    assert "panel_missing_graph_withholds_claim_authority" in names
    assert "panel_negative_control_not_promoted_to_final_cause" in names
    assert "panel_protected_harm_not_terminal_goal" in names
    assert cases[0].panel_summary["records"] == 224
    assert cases[0].panel_summary["review_gate_records"] == 112
    assert cases[0].panel_summary["direct_execute_records"] == 112


def test_external_panel_benchmark_passes_graph_ablation_and_negative_controls():
    report = run_sfm_external_panel_benchmark(str(PANEL_PATH))
    assert report["passed"] is True
    assert report["total_cases"] == 4
    assert report["false_positive_claims"] == 0
    assert report["false_negative_claims"] == 0
    assert report["claim_authorization_accuracy"] == 1.0
    assert "SFM_EXTERNAL_PANEL_BENCHMARK_PASSED" in report["reason_codes"]
    assert "SFM_EXTERNAL_PANEL_INCLUDES_GRAPH_ABLATION" in report["reason_codes"]
    assert "SFM_EXTERNAL_PANEL_INCLUDES_NEGATIVE_CONTROL" in report["reason_codes"]
    assert "SFM_EXTERNAL_PANEL_INCLUDES_PROTECTED_OUTCOME_CONTROL" in report["reason_codes"]


def test_external_panel_claim_authority_depends_on_domain_graph():
    report = run_sfm_external_panel_benchmark(str(PANEL_PATH))
    by_name = {case["name"]: case for case in report["case_results"]}
    positive = by_name["panel_throughput_claim_authorized_with_domain_graph"]
    ablated = by_name["panel_missing_graph_withholds_claim_authority"]

    assert positive["observed_claim_authorized"] is True
    assert positive["authority_status"] == "strong_diagnostic_sfm_support"
    assert ablated["observed_hypothesis_supported"] is True
    assert ablated["observed_claim_authorized"] is False
    assert ablated["authority_status"] == "falsifiable_diagnostic_only"


def test_external_panel_protected_and_negative_control_outcomes_do_not_authorize_claims():
    report = run_sfm_external_panel_benchmark(str(PANEL_PATH))
    by_name = {case["name"]: case for case in report["case_results"]}
    negative = by_name["panel_negative_control_not_promoted_to_final_cause"]
    protected = by_name["panel_protected_harm_not_terminal_goal"]

    assert negative["observed_goal"] == "audit_noise"
    assert negative["observed_claim_authorized"] is False
    assert protected["observed_goal"] == "user_or_system_harm"
    assert protected["observed_hypothesis_supported"] is False
    assert protected["observed_claim_authorized"] is False
