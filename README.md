# 20 — Discovery workbench

Part of the AWS demo track (apps 17 to 20): the **discover** stage. A coordinator plans scoped questions over a
discovery pack, delegates them to parallel subagents on the agent container (app 17), and produces a readout in
which every claim carries a verbatim, checked quote and every failed subagent is a named coverage gap.

## What this app does

Slice 20.1 is scaffolding only: the Python package (`workbench`, command `wb`), CI, the Dockerfile and the pin to
app 17 at tag `v0.1.0`. The engagement store, access rules, source library, discovery pack, coordinator and readout
arrive in later slices; this section is completed when they land. See `AGENTS.md` for the rules.

## Develop

```bash
uv sync --locked
uv run --frozen ruff check . && uv run --frozen ruff format --check .
uv run --frozen mypy --strict
uv run --frozen pytest
```
