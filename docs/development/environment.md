# Local environment

Prerequisites: Python 3.13+, uv, just, Git and Docker.

```sh
just setup
just dev
just test
just check
# Once the environment is disposable:
just cleanup
```

`setup` copies missing `.env` and `.env.local` from samples without changing
existing files, syncs locked dependencies, starts the development PostgreSQL
container, picks an API port in 18000–18999, creates an application and test
database, and migrates only the application database. The test fixture manages
its own tables.

## The development server

`docker-compose.dev.yml` defines one PostgreSQL 17 container, Compose project
`fastapi-template-dev`, published on `127.0.0.1:5433`. Every worktree of this
repository shares it and owns two databases inside it. Port 5433 is deliberate:
5432 is commonly held by another project's container, and an earlier revision
that reused whatever was listening there silently ran tests on PostgreSQL 15.
The image pins the version, so local and CI agree. Prefect and the full
application Compose stack are not started by setup. The volume persists across
`cleanup`; removing it is a manual `docker compose -f docker-compose.dev.yml
down -v`.

## Isolation and ownership

Identity includes the checkout's canonical path hash, not just its branch name.
`setup` writes `.env.worktree` with mode 0600: worktree id and root, ownership
token, API port, database names and a generated `SECRET_KEY`. Never commit or
share it. `just` loads it through `set dotenv-filename`, Docker Compose reads
`.env`, and `conftest.py` merges `.env`, `.env.local` and `.env.worktree` before
any application import — so no command needs a wrapper to receive the generated
values. A direct `uv run` outside `just` does not get them; use `just`.

The API port is derived from the checkout path and then stored in
`.env.worktree`, so each worktree keeps a stable port and different worktrees
start from different ones. Nothing arbitrates between them: if two checkouts do
land on the same port, or another project takes it first, `just dev` reports the
conflict — edit `APP_PORT` in that checkout's `.env.worktree` to move it.
Commands are not serialized either. Do not run `setup` and `cleanup` at once in
one checkout, and do not run two suites concurrently: they share that checkout's
single test database, and parallel pytest workers against one database are not
supported.

`setup` is resumable and preserves existing owned databases: it clears
`WORKTREE_READY` first, so an interrupted run never looks complete, and rerunning
reuses the same identity, port and token. Ownership is verified from the database
comment and the local token. An existing database with no token, or another
checkout's token, is rejected rather than adopted — inspect it manually. An
`.env.worktree` whose `WORKTREE_ROOT` does not match the current path is refused,
so a moved or copied checkout cannot claim another's resources.

`cleanup` drops exactly the two owned databases and removes `.env.worktree`. Active connections cause a failure rather than forced
termination. Repeated cleanup is harmless. A missing or foreign environment file
never triggers guessed deletion. The shared container, its volume, existing
environment files, branches and worktrees are retained. Dropped data is not
recoverable without a backup.

`just dev` runs in the foreground on the checkout's port and refuses to start
before setup. Stop it with Ctrl-C. `just status` prints identity, port and
readiness without secrets. If setup fails during migrations, correct the
migration and rerun setup; the port and databases remain available for
diagnosis or explicit cleanup.

## Tests and CI

The root `conftest.py` sets the test database before application imports and
serves both `tests/` and `features/`. In a provisioned checkout, `APP_DB_HOST`,
`APP_DB_PORT`, `APP_DB_NAME` and `APP_DB_TEST_NAME` come from `.env.worktree`
and no ambient variable can move them: a differing one is refused rather than
applied, because the fixture creates and drops tables in whichever database it
is given. Every other variable still accepts an override. Where nothing was
provisioned — CI, or a server you manage yourself — set
`WORKFLOW_ALLOW_UNPROVISIONED_DB=1`, exactly `1`, and supply all four
explicitly.

In both modes `APP_DB_TEST_NAME` must differ from `APP_DB_NAME`, and there
is no option to allow otherwise: the fixture drops every table in the test
database, so a database the tests touch is entirely disposable by
definition. Consent to an unprovisioned server is never consent to destroy
its application data. CI therefore declares two distinct names even though
only the test database is created. Logfire export is disabled in tests.

Tests are classified from their fixture dependencies: `db_session` means
integration, otherwise unit, unless an explicit marker supplies the level. Tests
accessing PostgreSQL directly must declare `pytest.mark.integration`. BDD
scenarios default to integration because step fixtures resolve dynamically; pure
scenarios may explicitly use the unit marker. A unit test requesting
`db_session`, including dynamically from a step, is rejected before database
access. Unit tests make no database connections. Tests that drive the
development container skip themselves when it is not running. Use
`just test-unit`, `just test-integration`, `just bdd`, or
`just test tests/users/api/test_api_get_me.py -k name`.

BDD runs once as part of the complete suite. No scenarios is allowed; every
scenario must be bound to a collected pytest-bdd test. Full collection checks
bindings before marker filtering; focused file runs deliberately remain focused.

CI installs locked dependencies and invokes the same just recipes against its
own PostgreSQL 17 service. Preserve the existing three CI job names used by
branch protection. `just check` runs the gates in order and stops at the first
failure — it is a plain just dependency chain, not a script. Its result
describes the code as it stood when it ran, so review runs it rather than
trusting a recorded result.
