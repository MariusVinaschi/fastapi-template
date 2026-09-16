# 0001 — Human-gated AI development and worktree environments

Status: accepted for this baseline. Revised: the development server is now a
container this project owns rather than any reachable PostgreSQL.

## Decision

Keep environment, testing and cleanup operations behind just. Use one worktree
per independent change. Development PostgreSQL is a single container defined by
`docker-compose.dev.yml`, shared by every worktree, published on port 5433; each
checkout owns two databases inside it, named from the hash of its canonical path
and marked with an ownership token. Generated values live in `.env.worktree`,
which just, Docker Compose and pytest all read natively, so only provisioning
and teardown need code. Keep feature intent and acceptance contracts
human-approved; automate subsequent transformations unless a significant
decision is unresolved. Keep existing development and review specializations
and selective Gherkin.

## Consequences

The workflow works outside Herdr. A shared container saves resources while
isolating schema and data between tasks; it is not a security boundary between
mutually untrusted users. Cleanup needs durable ownership evidence, because all
checkouts share one server. Docker becomes a hard requirement for local
development — an earlier revision reused any server already listening on the
configured endpoint, which silently ran tests against PostgreSQL 15 while CI
used 17. Pinning the image removes that class of drift. Port 5433 avoids the
default port, commonly held by another project's container. Prefect is opt-in
and not isolated by this baseline. Herdr automation, workspace creation and Git
cleanup are later orchestration concerns.

Only durable information is merged into main; temporary specification and
planning artifacts are consolidated before the human merge gate.
