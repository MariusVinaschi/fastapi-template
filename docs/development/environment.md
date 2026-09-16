# Local environment

Prerequisites: Python 3.13+, uv, just, Git, and PostgreSQL 17 (or Docker for
automatic local PostgreSQL startup). Tooling supports macOS and Linux.

```sh
just setup
just dev
just test
just check
# Once the environment is disposable:
just cleanup
```

`setup` copies missing `.env` and `.env.local` from samples without changing
existing files, syncs locked dependencies, reserves an API port in
18000–18999, creates an application and test database, and migrates only the
application database. The test fixture manages its own tables.

The database endpoint comes from `.env`, `.env.local`, then process variables.
An available configured server is reused. If a local endpoint is unavailable,
the minimal `docker-compose.dev.yml` starts a shared PostgreSQL service with
a persistent volume. Prefect and the full application Compose stack are not
started by setup. Authentication errors are failures, not reasons to replace
an existing server. The database role needs CREATEDB for setup and cleanup.

## Isolation and ownership

Identity includes the checkout's canonical path hash, not just its branch
name. `.worktree/state.json` stores the allocated port, generated local secret,
database names and ownership token with mode 0600; never commit or share it.
Commands apply these generated overrides in the child environment. Direct
`uv run` application commands do not automatically receive worktree overrides;
use `just` or `uv run python -m scripts.workflow run <command> ...`.

Port reservations are serialized under the shared Git common directory;
different worktrees of this repository receive different ports. Other projects
can still occupy a reserved port before dev starts; dev reports that conflict.
Lifecycle operations are serialized per checkout; test commands also serialize
use of its test database. Parallel pytest workers against one database are not
supported. Raw pytest receives the same bootstrap but bypasses the command lock.

`setup` is resumable and preserves existing owned databases. Ownership is
verified using database comments and the local token. An existing unmarked
database is rejected, including after a crash between CREATE and COMMENT;
inspect it manually rather than forcing adoption. Changed DB host/port/user
is rejected until the original endpoint is restored. Moving a checkout also
requires explicit recovery of its old state/resources.

`dev` runs in the foreground with reload and records its process identity.
`cleanup` signals only that matching process group, then drops exactly the
two owned databases. Active external DB connections cause a failure rather
than forced termination. Repeated cleanup is harmless. Missing/corrupt state
never triggers guessed database deletion. Shared servers, volumes, existing
environment files, branches and worktrees are retained. Dropped managed DB
data is not recoverable without a backup.

`just status` prints identity, port and readiness without secrets. If setup
fails during migrations, correct the migration and rerun setup. The port and
databases remain available for diagnosis or explicit cleanup.

## Tests and CI

The root `conftest.py` sets the test database before application imports and
serves both `tests/` and `features/`. `APP_DB_TEST_NAME` can configure legacy
direct runs; managed worktrees always use their generated test database.
Logfire export is disabled in tests.

Tests are classified from their fixture dependencies: `db_session` means
integration, otherwise unit, unless an explicit marker supplies the level.
Tests accessing PostgreSQL directly must declare `pytest.mark.integration`.
BDD scenarios default to integration because step fixtures resolve dynamically;
pure scenarios may explicitly use the unit marker. A unit test requesting
`db_session`, including dynamically from a step, is rejected before DB access. Unit tests make no DB
connections. Use `just test-unit`, `just test-integration`, `just bdd`, or
`just test tests/users/api/test_api_get_me.py -k name`.

BDD runs once as part of the complete suite. No scenarios is allowed; every
scenario must be bound to a collected pytest-bdd test. Full collection checks
bindings before marker filtering; focused file runs deliberately remain focused.

CI installs locked dependencies and invokes the same just recipes against its
provided PostgreSQL service. `CI=true` bypasses local worktree state and Docker
setup. Preserve the existing three CI job names used by branch protection.

Successful local checks record .worktree/check.json with the Git HEAD and
tracked/untracked content represented by a fingerprint. Review may reuse the
exit-code evidence only while scripts.quality.fingerprint still matches.
No review verdict or human approval is inferred from that report.
