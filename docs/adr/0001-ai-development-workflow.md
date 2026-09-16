# 0001 — Human-gated AI development and worktree environments

Status: accepted for this baseline.

## Decision

Keep environment, testing and cleanup operations behind just. Use one worktree
per independent change, with a shared PostgreSQL server and two owned databases
per checkout. Keep feature intent and acceptance contracts human-approved;
automate subsequent transformations unless a significant decision is unresolved.
Keep existing development and review specializations and selective Gherkin.

## Consequences

The workflow works outside Herdr. Shared PostgreSQL saves resources while
isolating schema/data changes between tasks; it is not a security boundary
between mutually untrusted users. Cleanup needs durable ownership evidence.
Process and test execution need coordination inside each checkout. Prefect
is opt-in and not isolated by this baseline. Herdr automation, workspace
creation and Git cleanup are later orchestration concerns.

Only durable information is merged into main; temporary specification and
planning artifacts are consolidated before the human merge gate.
