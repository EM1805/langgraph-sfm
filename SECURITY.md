# Security Policy

`langgraph-sfm` is an observability and research tool. It should not be used as the sole safety control for autonomous agents.

## Supported versions

The initial public line is `0.1.x`.

## Reporting vulnerabilities

Please report security issues privately through GitHub security advisories once the public repository is created.

## Safety notes

- Treat `deception_risk` and `intentionality_score` as decision-support signals, not proofs.
- Keep human review in the loop for high-impact deployments.
- Validate domain graphs, negative controls, and protected outcomes before production use.
