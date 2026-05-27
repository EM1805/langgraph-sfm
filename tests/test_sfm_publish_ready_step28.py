from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import sfm_langgraph
from sfm_langgraph.cli import run_demo


ROOT = Path(__file__).resolve().parents[1]


def test_public_api_exports_publish_ready_nodes():
    assert hasattr(sfm_langgraph, "SFMIntentAnalyzerNode")
    assert hasattr(sfm_langgraph, "SFMAgentMonitor")
    assert hasattr(sfm_langgraph, "build_sfm_run_report")


def test_cli_demo_returns_conservative_claim_withheld_report():
    output = run_demo()
    analysis = output["sfm_analysis"]
    monitor = output["sfm_monitor"]
    assert analysis["primary_intent"] == "answer_user_question"
    assert analysis["intent_hypothesis_supported"] is True
    assert analysis["intent_claim_authorized"] is False
    assert analysis["final_cause_claim_level"] == "falsifiable_diagnostic"
    assert output["sfm_gate_status"] == "review"
    assert monitor["claim_withheld_events"] == 1


def test_cli_module_executes_as_script():
    result = subprocess.run(
        [sys.executable, "-m", "sfm_langgraph.cli", "--indent", "0"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert '"sfm_analysis"' in result.stdout
    assert '"sfm_monitor"' in result.stdout


def test_publish_files_present_and_readme_has_positioning():
    assert (ROOT / "LICENSE").exists()
    assert (ROOT / "MANIFEST.in").exists()
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Causal intent monitoring for LangGraph agents" in readme
    assert "not as a final detector of hidden intentions" in readme
    assert "pip install langgraph-sfm" in readme
