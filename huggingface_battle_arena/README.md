---
title: LangGraph SFM Battle Arena
emoji: ⚔️
colorFrom: red
colorTo: blue
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# LangGraph-SFM Battle Arena

A multi-round red-team / blue-team demo for [`langgraph-sfm`](https://pypi.org/project/langgraph-sfm/).

This Space shows the interaction between:

- **LangGraph**: orchestrates a looping agent workflow with conditional routing.
- **Red team**: adapts attacks across rounds.
- **SFM blue team**: monitors plausible intent, side effects, deception risk, and gates tool execution.

It compares two runs:

```text
Without SFM → permissive baseline
With SFM    → SFM intent analyzer + monitor + gate
```

The demo includes:

- multi-round battle mode
- adaptive red-team attempts
- SFM ON/OFF comparison
- scoreboard
- LangGraph node timeline
- advanced SFM JSON details hidden in accordions

## Epistemic boundary

This demo does not prove an agent's true goal. It reports plausible intent hypotheses and governance-facing risk signals with explicit epistemic boundaries.
