# Contributing

Thanks for helping improve `langgraph-sfm`.

## Development setup

```bash
python -m pip install -e ".[test]"
python -m pytest
```

## Contribution guidelines

- Keep SFM claim levels explicit.
- Do not turn diagnostic support into authorized causal/final-cause claims without the relevant gates.
- Add tests for negative cases, claim-withheld cases, and side-effect/protected-outcome cases.
- Keep LangGraph optional. The core nodes should remain plain callables.

## Pull request checklist

- Tests pass.
- New behavior has a negative/adversarial test when applicable.
- README/docs do not overclaim intent detection.
- Public APIs remain importable from `sfm_langgraph`.
