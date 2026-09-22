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
- `just architecture-check` (slice A form): `lint-imports`, then `pytest tests/architecture`.
- `just check` gains `architecture-check` before `test-cov`.
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

**ast-grep** (`ast-grep-cli`, dev dependency, pinned in `uv.lock`) for what is
observable as syntactic structure; **runtime introspection** for what needs resolved
types. Rules in `rules/architecture/*.yml`, declared via `sgconfig.yml`.

| AC | Sensor | Rule shape / trap |
| --- | --- | --- |
| B1 | ast-grep | `pattern: self.session.commit($$$)`, anchored to the session attribute (not any `.commit()`), `files:` limited to `domains/**/{repository,service}.py`. `base/factory.py` commits test data legitimately and is out of scope by AC-B1's own wording. |
| B2 | ast-grep | `select($$$)` with `not: inside:` a function that itself `has:` `self._apply_user_scope($$$)` or `self._require_system()`. `inside`/`has` use `stopBy: end` at every level so the check reaches *any* enclosing function, not just the nearest — a `select()` built in a nested helper is still scoped if the outer method scopes it (verified against a nested-helper fixture; an earlier, nearest-ancestor-only version false-positived on it). `base/repository.py`'s two builders (`_build_list_query`, `_build_single_query`) are unscoped by design, exempted per-line with a named `ast-grep-ignore` and a reason — never as a directory-wide `ignores:` block, which is itself an unnamed blanket exemption (found in review; removing it surfaced exactly these two). *Revised 2026-09-21, after review:* the two `users/repository.py` bypasses are no longer suppressed — `get_by_api_key_hash` now calls `self._require_system()` (it is genuinely system-only, its one caller is `app/api/security.py` via `for_system`), and `get_by_user_id` is now scoped normally as free defense in depth (its caller always passes its own id, so the scope is a safe no-op in the one path where it isn't). Zero suppressions ship in application code. |
| B3 | ast-grep | direct `*Service(...)` / `*Repository(...)` construction, scoped to `app/**/*.py` — a repository test legitimately constructs its subject directly to test it in isolation, which is a production-code concern, not a test one. |
| B4 | ast-grep | `kind: keyword_argument` with name `authorization_context` and value `None`. Must be the **kind-based** form: tree-sitter distinguishes `keyword_argument` (call site, rejected) from `default_parameter` (the prescribed `__init__` default, accepted) structurally. Verified on a fixture. Positional `None` (`for_user(session, None)`) is not this rule's concern — `for_user`'s non-optional `authorization_context` parameter makes it a type error, caught by `ty` earlier in `just check`. |
| B5 | runtime | resolve each route's **effective** response type: `route.response_model`, or — when it's `None` (FastAPI's own inference disabled, as `/auth/login` and `/auth/refresh` do) — the endpoint's real return annotation via `typing.get_type_hints`. *Revised 2026-09-21, after review:* the original version only read `response_model`, silently never inspecting those two routes at all; `TokenPair.access_token`/`refresh_token` are real tokens they exist to issue, now visible and explicitly exempted, alongside the fixed `SECRET_FIELD`→`_is_secret_field` vocabulary gap that had made the one shipped `APIKeyGenerated.api_key` exemption inert (the detector never matched `api_key` in the first place). |
| B6 | runtime | each domain exposes a scope strategy and its repository wires one; domain discovery no longer trusts a `*/repository.py` glob alone — it also asserts the discovered set equals every non-`base` domain directory, so an empty or partial result fails instead of silently skipping (found in review: `pytest.mark.parametrize` over an empty list is a skip, not a failure). |

**What ast-grep is not.** It reads syntactic structure. It does not resolve types,
data flow, symbols or the call graph. B2 therefore asserts that the scoping ritual is
*present*, never that authorization is *correct* (AC-B2). No rule, comment or
document may claim otherwise.

**Rule tests (AC-09)** — every rule carries `valid` and `invalid` cases run by
`ast-grep test`. This is the guard against the failure mode that cost us semgrep: a
rule matching nothing looks exactly like a rule with nothing to report.

**Suppressions (AC-05)** — native and verified:
- `ast-grep-ignore: <rule-id>` plus a reason comment; blanket suppressions rejected
  by `--error=no-suppress-all`.
- Stale suppressions rejected by `--error=unused-suppression`. Verified on a fixture:
  the live suppression passes, the stale one fails.

**Recipe (slice B form)**
```
architecture-check:
    uv run --locked ast-grep test
    uv run --locked ast-grep scan --error=unused-suppression --error=no-suppress-all
    uv run --locked lint-imports
    uv run --locked pytest tests/architecture
```

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
- ast-grep reads source, not semantics: an aliased call or an indirect construction
  escapes it. Accepted and stated in AC-B2 — the sensor removes the routine pass,
  the reviewer still reads the diff.
- A rule that matches nothing reads as a clean tree. Mitigated by AC-09 for ast-grep
  and by fixture packages for import-linter; this is the single most likely way for
  this feature to deliver false confidence.

## Open questions

None. D1–D4 in `feature.md` resolve the architectural decisions. The recipe is
named `architecture-check`, matching the existing `type-check` / `format-check`
pattern, per the human's wording when approving the ast-grep design. -> We will use 
`architecture-check`
