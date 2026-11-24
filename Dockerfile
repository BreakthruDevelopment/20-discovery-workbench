# Minimal image: the locked runtime dependencies and the package, nothing else. No credentials are baked in.
# App 17 is a git dependency (pinned by tag in pyproject.toml), so the build stage needs git.
FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY workbench ./workbench
# `--locked`, not `--frozen`: `--frozen` installs from the lock without checking it still
# matches pyproject.toml, so a dependency added and never relocked builds an image that is
# simply missing it. ci.yml makes the same distinction for the same reason.
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
COPY --from=build /opt/venv /opt/venv
RUN useradd --system --uid 10001 app
USER app
# The deployed surface is `wb serve` (GET /healthz, GET /), so the image serves with no
# arguments. `--version` stays reachable by overriding the command -- which is what ci.yml's
# `Container image` job does -- but it must not be the default: a container that prints one
# line and exits is health-checked and restarted forever.
# `wb serve` binds every interface and reads PORT, so no flags are needed here.
EXPOSE 8080
ENTRYPOINT ["wb"]
CMD ["serve"]
