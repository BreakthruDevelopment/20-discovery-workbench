# Rules for every agent (Claude Code, Grok Build, Codex)

This repo is part of the **30 apps in 30 days** portfolio, in the AWS demo track (apps 17 to 20). The playbook
lives in [BreakthruDevelopment/ai-dev-os](https://github.com/BreakthruDevelopment/ai-dev-os); the spec is
`specs/20-discovery-workbench.md` there and the track's shared rules are in `specs/day-0-aws-demo-track.md`. This is a
Python package, not a Next.js app: the Next.js stack rules of the other repos do not apply.

## Repo safety (non-negotiable)

The BreakthruDevelopment org holds other, unrelated applications.

- Touch only repos with the GitHub topic `30-apps-30-days`. Everything else is read-only.
- Never force-push, delete, rename, transfer or archive any repo or branch you didn't create for the current task.
- Never push to `main`. Open a PR from a branch named `<harness>/<short-task>` (e.g. `claude/python-scaffolding`).
- Pick up only issues labeled for your harness, and follow the role file named in the issue title (`ai-dev-os/roles/`).
- Never commit secrets. `.env*` is ignored; real values live in GitHub Actions secrets or a cloud secret manager.

## Stack

- **Python 3.12**, managed with `uv` (`uv sync --locked`, `uv run --frozen ...`); commit `uv.lock`.
- `ruff check` and `ruff format --check`, `mypy --strict`, `pytest`. Strict means strict: no blanket
  `# type: ignore` or `# noqa`. A missing third-party stub gets a narrowly scoped `[[tool.mypy.overrides]]` entry
  with a comment saying why.
- The package is `workbench`; the command is `wb`.

## Foundation paths, and why nothing enforces them here

**The foundation paths are `workbench/core/` and `.github/workflows/`.** Wave 1 (slices 20.1 and 20.2) owns them.
A later slice creates or edits nothing there unless a security-sensitive `claude` slice names it as owner; later
slices add their own packages instead (`workbench/coordinator/`, `workbench/readout/`, `workbench/cli/`). If your
slice needs a change in a foundation path, or the data layer it needs is not on `main`, stop and comment on the
issue.

**Neither path is in the runner's `WAVE1_PATHS` guard** (`scripts/issuelib.py` in ai-dev-os; the pre-push guard in
`scripts/run-harness.sh` mirrors it). That list holds `p2p/core/`, `kit/core/`, `erp/` and `contracts/`, and this repo
has none of them. **So no mechanical check refuses a push that touches these paths: the rule is held by the spec and
by review, and by you.** A quiet guard is not permission.

`pyproject.toml`, `uv.lock` and `Dockerfile` are **shared, not foundation.** A slice that adds a dependency edits
`pyproject.toml`, relocks (`uv lock`) and says so on its PR.

## The lockfile rule (the word is inverted between pnpm and uv)

pnpm's `--frozen-lockfile` means "fail if the lock is out of date". **In uv that behaviour is `--locked`.** uv's
`--frozen` means "install from the lock without checking it matches `pyproject.toml`". Copying the pnpm habit
gives CI that cannot fail on a stale lock: a dependency added to `pyproject.toml` and never relocked passes green
and is then absent at deploy, because the Dockerfile installs the locked set. CI therefore runs:

- `uv sync --locked`, which fails when `uv.lock` is stale, **and**
- `--frozen` on every `uv run` step, because a bare `uv run` silently rewrites `uv.lock` and resolves from PyPI.

Both halves are load-bearing; `UV_FROZEN=1` is not a substitute. Locally, `uv lock` is how you relock.

- **App 17 (`agent-container`) is pinned by git tag** in `[tool.uv.sources]` (currently `v0.1.0`, commit `9955f1f`),
  never by branch or bare commit. A slice that needs something the tag lacks stops and comments on its issue; it does
  not bump the tag or reimplement the contract. `tests/test_app17_pin.py` reads the installed package's
  `direct_url.json` and asserts the commit, so it proves the pin resolved.
- Two things are load-bearing for the whole track and change only on a `claude` slice: the CI job name
  `Lint, test, build, smoke`, and the `review-gate.yml` caller, which must keep the `pull_request`,
  `pull_request_review` and `issue_comment` triggers and `permissions: actions: write`.

## The track's rules

- **Every model call goes through app 17's `ModelProvider`.** No code here calls Bedrock directly.
- **Every demo and test runs at zero cost on recorded replies**; `--live` switches to Bedrock. Nothing needs the
  network to be shown.
- **The loop ends on the stop reason, never on the text.**
- **Access checks (`assert_can`) and the `engagement_id` filter live in `workbench/core`**, never in callers. A
  `sponsor` reads only a finalised readout of its own engagement and nothing under `sources/`.
- **Source text, transcripts and tickets are data, never instructions.** Fence them before they reach a model.
- **Every claim carries a verbatim quote that is checked against its document.**
- **Validate input at the boundary** (CLI arguments, tool arguments, model output) with typed models.
- **Logs:** JSON lines with fixed fields. Never log secrets, credentials or document text.
- **No AWS credential is ever committed.** Local runs use the default credential chain. Slices that need no AWS
  access must not reference CI secrets; the CI job today reads none.

## Definition of done (CI enforces most of it)

The required check is named exactly `Lint, test, build, smoke`; a second job is `Container image`. **Only the
first is a required context in the ruleset**, so a broken Dockerfile can merge green: check it yourself when you
touch it. The required job runs `uv sync --locked`, `ruff check`, `ruff format --check`, `mypy --strict`, `pytest`,
builds the package, imports it from a clean environment, and runs `wb --version`. New rules have a test in
`tests/`. The README's "What this app does" section is filled in.
