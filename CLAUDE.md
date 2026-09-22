# Project instructions

## Essential invariants

- Business logic belongs in app/domains; no FastAPI/Prefect imports there.
  Their structural form is checked by just architecture-check; review still
  evaluates architectural intent, scope, exceptions and semantic correctness.
- API services use for_user; deliberate system operations use for_system.
  Permissions are deny-by-default and repositories scope rows in SQL. Construction
  discipline, commit discipline and scoping presence are decided by
  mechanically by just architecture-check; permission correctness and design
  intent still belong to review.
- Repositories flush, never commit. HTTP requests and Prefect flows own
  transaction boundaries. Workers must not import app/api.
- Preserve existing user changes. Do not create worktrees without explicit
  authorization or edit another worktree. One independent task normally uses
  its own branch and worktree; avoid concurrent implementing writers.
- Keep comments short and explain only non-obvious constraints.
- Use Conventional Commits. Never manually bump project.version.

## Commands

Use just for project operations:
- just setup: locked dependencies, dev PostgreSQL container, isolated DBs,
  migrations, API port.
- just dev: foreground API with reload; just status shows its port.
- just test [pytest arguments]: all tests including configured BDD.
- just test-unit / just test-integration / just bdd: focused suites.
- just check: lint, format check, types, complexipy <=12, architecture, tests
  with coverage.
- just architecture-check: structural invariants alone. No database, no setup.
- just format: explicit formatting; checks do not rewrite code.
- just migrate / just migrate-create "message": worktree database migrations.
- just cleanup: drops this checkout's two databases; retains the shared
  development container and Git worktree. Run only when data is disposable.

## Read on demand

- Current feature: docs/specs/<id>-<slug>/, if present.
- Feature gates, independent review, QA and documentation consolidation:
  [development workflow](docs/development/workflow.md).
- Setup, ownership/recovery, test classification and CI:
  [environment](docs/development/environment.md).
- Domain boundaries, authorization and Unit of Work:
  [architecture](docs/architecture/application.md).
- Rationale for this baseline: [ADR](docs/adr/0001-ai-development-workflow.md).
- Gherkin placement/bindings: [acceptance suite](features/README.md).

Use the existing feature-spec-workflow and tdd-implementation skills when
applicable. Preserve human intent/scope and AC gates. Significant product or
architectural questions require human decisions; routine implementation
choices do not. Review uses the existing review-orchestrator with independent
specialists. QA precedes documentation consolidation and human merge.
