# Python CI/CD Pipeline Demo

A small Flask API used to demonstrate a complete, production-style CI/CD
pipeline: lint → test → Docker build validation → image publish → (optional)
AWS deployment via OIDC.

## The App

A minimal Flask API with two endpoints:
- `GET /health` — health check, used by container/orchestrator probes
- `POST /add` — adds two numbers, with input validation (used to demonstrate
  meaningful unit tests, not just a trivial "hello world")

## Pipeline Architecture

```
Push/PR ──▶ CI workflow (ci.yml)
             ├─ lint (flake8)
             ├─ test (pytest)
             └─ docker build check (no push)

Push to main ──▶ CD workflow (cd.yml)
                   ├─ build-and-push  → always runs, publishes to GHCR
                   └─ deploy-to-aws   → manual only (workflow_dispatch),
                                        OIDC auth, ECR push, ECS deploy
```

### Why CI and CD are separate workflows
`ci.yml` runs on every push and pull request — fast feedback, no side
effects outside the CI runner itself (nothing is published or deployed).
`cd.yml` only runs on `main`, and splits further: publishing the image to
GHCR happens automatically, but the **AWS deployment step requires a manual
trigger** (`workflow_dispatch`). This is a deliberate gate — publishing an
image is low-risk and reversible; deploying to real infrastructure is not,
so it shouldn't happen silently on every merge.

### Why OIDC instead of AWS access keys
The AWS deploy job never stores `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`
as secrets. Instead, it uses OpenID Connect: GitHub issues a short-lived,
cryptographically signed token for the job run, which AWS exchanges for
temporary credentials via a pre-configured IAM role trust relationship.
Those credentials expire when the job ends. This removes an entire class of
risk — there's no long-lived credential that could leak from a log, a
misconfigured secret, or a compromised workflow file.

To actually use the AWS job, you'd need to:
1. Create an IAM OIDC identity provider for `token.actions.githubusercontent.com`
   (one-time setup per AWS account).
2. Create an IAM role trusting that provider, scoped to this repo (`repo:your-org/your-repo:ref:refs/heads/main`).
3. Set `AWS_ROLE_ARN` as a repository variable.

This repo intentionally leaves that role unconfigured — the job is here to
show the *pattern*, not to deploy anywhere by default.

### Why lint has two passes
The first `flake8` run only checks for real errors (syntax errors,
undefined names — codes `E9`, `F63`, `F7`, `F82`) and **fails the build** if
found. The second run checks style/complexity but uses `--exit-zero`, so
style issues are visible in the log without blocking the pipeline. This
keeps the gate meaningful (real bugs block merges) without being overly
strict about style on every PR.

### Why there's a Docker build-check job in CI (separate from CD)
`ci.yml` builds the image but never pushes it. This catches a broken
Dockerfile (missing file, bad syntax, failed dependency install) on every
pull request, before it ever reaches `main` — rather than finding out only
when `cd.yml` tries to publish.

## Running Locally

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
flake8 app tests

python -m app.main   # runs on http://localhost:8080
```

## Running with Docker

```bash
docker build -t pipeline-demo-app .
docker run -p 8080:8080 pipeline-demo-app
curl http://localhost:8080/health
curl -X POST http://localhost:8080/add -H "Content-Type: application/json" -d '{"a": 2, "b": 3}'
```

## Tech Stack

Python · Flask · Pytest · Flake8 · Docker · GitHub Actions · AWS (ECR, ECS,
IAM OIDC)
