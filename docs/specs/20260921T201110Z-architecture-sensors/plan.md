# Plan — Executable architecture sensors

Contract: `acs.md` (gate 2 approved 2026-09-21). Two slices, A then B.

## Slice A — import graph

**Move (D1, AC-A6/A7)**
- `app/infrastructure/security.py` → `app/api/security.py`.
- Update `app/api/dependencies.py:15` and ~14 test imports under `tests/`.
- Pure relocation: no edit to the module's body beyond its own imports.

**Contracts** — `[tool.importlinter]` in `pyproject.toml`, `root_package = "app"`,
`include_external_packages = true`, `exclude_type_checking_imports = true` (D2).

| AC | Contract |
| --- | --- |
| A1 | `forbidden`: `app.domains` → `fastapi`, `starlette`, `prefect` |
| A2 | `forbidden`: `app.workers` → `app.api` |
| A3 | `layers`: `app.api \| app.workers` / `app.domains.sessions` / `app.domains.users` / `app.domains.base` / `app.infrastructure` |
| A4 | `protected` **one per domain**: `app.domains.<x>.repository`, allowed importer `app.domains.<x>` |

A4 must not use wildcards. Measured: `protected_modules = app.domains.*.repository`
with `allowed_importers = app.domains.*` reports KEPT on a real cross-domain import,
because every domain matches the allow-list. Per-domain contracts catch it.

**Command & wiring (AC-08, AC-03)**
- `just check-architecture` → `lint-imports` + `pytest -m architecture`.
- `just check` gains it before `test-cov`.
- `prek.toml`: local hook, `pass_filenames = false`.
- `.github/workflows/ci.yml`: step in the existing `lint` job (no DB service there).

**Tests**
- `tests/architecture/` marked `architecture`; register the marker in `pyproject.toml`.
- A4/A5 exhaustiveness: every `app/domains/<x>/repository.py` has a matching contract.
- Per-contract proof: run `lint-imports` against fixture packages under
  `tests/architecture/fixtures/`, each carrying one violation. Feasible and fast —
  measured at 89 files / 224 dependencies in about a second on the real tree.
- Stale-exemption check (AC-05) over `ignore_imports`, via
  `unmatched_ignore_imports_alerting = "error"`.

## Slice B — non-import invariants

Stdlib `ast` for source-level checks; in-process introspection where real types are
needed. Sensors in `tests/architecture/`, same marker, same command.

| AC | Sensor | Scope / trap |
| --- | --- | --- |
| B1 | `ast` | only `domains/**/{repository,service}.py`; `base/factory.py:30` commits test data legitimately |
| B2 | `ast` | `select()` in a domain repository without `_apply_user_scope`; 2 real hits to declare: `users/repository.py:63,69` |
| B3 | `ast` | direct `*Service(...)` / `*Repository(...)` outside its own module |
| B4 | `ast` | **call-site keyword only**, never the `__init__` default; a naive match gives 4 false positives |
| B5 | runtime | walk `APIRoute.response_model`, recurse nested + generics; exempt `APIKeyGenerated.api_key` |
| B6 | runtime | each domain exposes a scope strategy and its repository wires one |

B5 needs settings but no connection: verified against an unreachable DB host —
9 routes resolved, including `PaginatedSchema[UserRead]`.

**Exemptions (AC-05)** — one declaration site, each entry `target + reason`. A test
fails when an entry matches no current violation.

## Documentation (AC-07)

Mark each automated invariant as machine-checked and name its check, in
`docs/architecture/application.md`, `.agents/skills/domain-*/SKILL.md` and the
`.claude/rules/domains/` copies. **Edit `.agents/` — a test keeps the copies
identical.** Add to `docs/development/workflow.md` that reviewers do not re-verify
machine-checked invariants. Leave judgment rules unmarked.

## Risks

- Contracts that look right and enforce nothing (see A4). Every contract is proven
  against a fixture that must fail it.
- Over-broad sensors get disabled rather than fixed. B1/B2/B4 are scoped narrowly
  and start from the real code, which is already clean under them.
- The move touches many test imports; mechanical, and AC-A7 keeps it honest.
- Slice B's AST sensors read source, not semantics: an aliased call escapes them.
  Accepted — a reviewer still reads the diff; the sensor removes the routine pass.

## Open questions

None. D1–D4 in `feature.md` resolve the architectural decisions; naming the recipe
`check-architecture` rather than `architecture-check` (which would match the
existing `type-check` / `format-check` pattern) is the human's stated choice. -> We will use 
`architecture-check`
