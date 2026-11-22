# 20 — Discovery workbench

Part of the AWS demo track (apps 17 to 20): the **discover** stage. A coordinator plans scoped questions over a
discovery pack, delegates them to parallel subagents on the agent container (app 17), and produces a readout in
which every claim carries a verbatim, checked quote and every failed subagent is a named coverage gap.

## What this app does

The package is `workbench` and the command is `wb`. App 17 is pinned at tag `v0.1.0`. The synthetic discovery
pack at `sources/acme-p2p/` is committed evidence for a fictional procure-to-pay engagement: four interview
transcripts, a system inventory, a 12-row ticket extract and two memos, written by the pack's generator from
`manifest.json`. The engagement store, access rules, source library, coordinator and readout arrive in later
slices. See `AGENTS.md` for the rules.

## Develop

```bash
uv sync --locked
uv run --frozen ruff check . && uv run --frozen ruff format --check .
uv run --frozen mypy --strict
uv run --frozen pytest
```
