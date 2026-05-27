# Step 28 — Publish-ready GitHub + PyPI package

Step 28 turns the Step 27 LangGraph/SFM monitor into a first public-release package.

## Added

- Public package metadata for the `langgraph-sfm` PyPI distribution.
- Public-facing README optimized for developer adoption.
- CLI smoke demo: `python -m sfm_langgraph.cli` and `langgraph-sfm-demo`.
- `MANIFEST.in`, `LICENSE`, `.gitignore`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `ROADMAP.md`, `CITATION.cff`.
- GitHub Actions templates for CI and PyPI Trusted Publishing.
- Public quickstart example that runs without LangGraph or external model calls.
- Packaging smoke tests.

## Design choice

The distribution name is `langgraph-sfm`, while the import package remains `sfm_langgraph`.
This follows Python packaging conventions where distribution names may use hyphens and import packages use underscores.

## Safety posture

Public copy avoids claims such as “proves the true goal of an agent.” The recommended positioning is:

> Detect plausible agent intentions, side effects, and deception risk with explicit epistemic claim levels.

## Local release checks

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m pip wheel . -w dist --no-deps
python -m sfm_langgraph.cli
```
