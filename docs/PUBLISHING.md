# Publishing langgraph-sfm

This checklist prepares a first public release on GitHub and PyPI.

## 1. Pick names

Recommended:

- GitHub repo: `langgraph-sfm`
- PyPI distribution: `langgraph-sfm`
- Python import: `sfm_langgraph`

Before publishing, confirm the PyPI name is still available:

```bash
python -m pip index versions langgraph-sfm
# or open https://pypi.org/project/langgraph-sfm/
```

If the name is taken, use `sfm-langgraph` as the fallback distribution name while keeping the import package as `sfm_langgraph`.

## 2. Local validation

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m pip wheel . -w dist --no-deps
python -m pip install --force-reinstall dist/*.whl
python -m sfm_langgraph.cli
```

## 3. GitHub repository setup

```bash
git init
git add .
git commit -m "Initial langgraph-sfm release"
git branch -M main
git remote add origin git@github.com:emilianomuharremi/langgraph-sfm.git
git push -u origin main
```

Add topics:

- `langgraph`
- `langchain`
- `ai-safety`
- `agent-observability`
- `causal-inference`
- `intent-monitoring`

## 4. PyPI release

Recommended modern route: use PyPI Trusted Publishing from GitHub Actions.

1. Create the project on PyPI after the first upload attempt or pre-register if available.
2. In PyPI, add a trusted publisher for this repo and workflow: `.github/workflows/publish.yml`.
3. Create a GitHub release tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The included `publish.yml` builds the wheel/sdist and publishes on GitHub Releases.

Manual fallback:

```bash
python -m pip install -r requirements-publish.txt
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

## 5. Launch copy

Suggested headline:

> I built `langgraph-sfm`: causal intent monitoring for LangGraph agents.

Suggested short description:

> `langgraph-sfm` adds a LangGraph-compatible SFM node and agent-run monitor that reports plausible intent, side effects, deception risk, and epistemic claim level. It is not a mind reader; it is a conservative observability layer for agent workflows.

## 6. First public demo scenarios

- Deception mismatch: stated goal differs from SFM-supported intent.
- Claim withheld: diagnostic support exists, but SCM graph is missing.
- Human-review routing: run monitor escalates only risky events.
- Side-effect watch: candidate goal overlaps monitored/protected outcome.
