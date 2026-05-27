---
title: langgraph-sfm Agent Intent Monitor
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
---

# langgraph-sfm Agent Intent Monitor

A small Hugging Face Space demo for [`langgraph-sfm`](https://pypi.org/project/langgraph-sfm/).

It lets users enter a declared goal, a proposed agent action, candidate goals, and observed effects, then runs:

```python
from sfm_langgraph import SFMIntentAnalyzerNode, SFMAgentMonitor
```

The output includes:

- primary intent hypothesis
- epistemic claim level
- side-effect risk
- deception-risk signal
- allow / review / block gate
- monitor events and trace

## Deploy on Hugging Face Spaces

Create a new Space with:

- SDK: `Gradio`
- App file: `app.py`
- Python: default

Then copy these files into the Space repository:

```text
app.py
requirements.txt
README.md
```

The Space installs `langgraph-sfm` from PyPI.

## Epistemic boundary

This demo does not prove an agent's true goal. It reports plausible intent hypotheses and governance-facing risk signals with explicit epistemic boundaries.
