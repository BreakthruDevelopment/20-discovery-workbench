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
# PORT=3000 because that is what the Lambda Web Adapter forwards to: stacks/aws/main.tf sets
# AWS_LWA_PORT=3000 for every app and sets no PORT, so the port has to come from the image.
# `wb serve` reads PORT, so this is all it takes; its own default stays 8080 for a local run.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH PORT=3000
COPY --from=build /opt/venv /opt/venv
RUN useradd --system --uid 10001 app
# AWS Lambda Web Adapter: lets this same image run as a package_type="Image" Lambda, which is
# how stacks/aws/main.tf deploys every app. It is a Lambda extension -- it implements the Lambda
# Runtime API and proxies to the HTTP server on AWS_LWA_PORT -- and is inert on every other
# platform, so a plain `docker run` is unaffected. Copied before USER so it keeps its exec bit,
# and from the same pinned version 30-apps-template uses.
# Without this the function fails init on every invoke: see issue #29.
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
# Prove the adapter is built for the platform this image is: `COPY --from` an external image is
# the one step in this build that could hand us a binary of the wrong architecture, and the only
# symptom would be a Lambda that fails init in production. ci.yml's `test -x` check cannot see
# this -- it runs on amd64, while the image that actually deploys is arm64 -- and an exec-format
# error is not something a mode bit reveals. Reading ELF e_machine (offset 18, 2 bytes LE:
# 62 = x86-64, 183 = AArch64) runs inside BOTH platform builds, which is the point.
ARG TARGETARCH
RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) want=62 ;; \
      arm64) want=183 ;; \
      *) echo "adapter check: unsupported TARGETARCH" >&2; exit 1 ;; \
    esac; \
    got=$(od -An -tu2 -j18 -N2 /opt/extensions/lambda-adapter | tr -d ' \n'); \
    if [ "$got" != "$want" ]; then \
      echo "adapter check: ELF e_machine $got, expected $want" >&2; exit 1; \
    fi
USER app
# The deployed surface is `wb serve` (GET /healthz, GET /), so the image serves with no
# arguments. `--version` stays reachable by overriding the command -- which is what ci.yml's
# `Container image` job does -- but it must not be the default: a container that prints one
# line and exits is health-checked and restarted forever.
# `wb serve` binds every interface and reads PORT, so no flags are needed here.
#
# ENTRYPOINT is the ABSOLUTE path, not the bare name `wb`. AWS requires an absolute path for a
# container image's entry point, and `wb` lives at /opt/venv/bin/wb, which is reachable only
# through the PATH this image sets in its own ENV -- not through Lambda's documented default
# PATH (/usr/local/bin:/usr/bin/:/bin:/opt/bin). 30-apps-template gets away with a bare `node`
# only because /usr/local/bin/node is already on that default path, so the live AWS apps are no
# evidence for an entry point outside it. This is the first image on this stack with one.
EXPOSE 3000
ENTRYPOINT ["/opt/venv/bin/wb"]
CMD ["serve"]
