# Executable architecture sensors

- ID: 20260921T201110Z-architecture-sensors
- Branch / worktree: `feat/verify-architecture`
- Status: gate 1 approved (2026-09-21), scope amended by D1 and D2 below

## Intention

Make this repository's architectural invariants **verifiable by a machine** rather
than re-validated by a human or an agent on every change.

## Problem

The invariants are real and precise, but they exist only as prose, spread across
`CLAUDE.md`, `AGENTS.md`, `docs/architecture/application.md`, `.claude/rules/domains/*.md`
and `.agents/skills/domain-*/SKILL.md`. Nothing executes them.

Consequences observed today:

- Every review spends attention re-checking rules that never change. An agent
  reviewer asked to confirm "domains import no FastAPI" is doing a job a linter
  does in under a second, and unlike the linter it can be wrong or be talked out
  of its answer.
- `just check` (lint, format, types, complexity, tests) has **no gate at all** on
  layering, domain boundaries or authorization rituals. A violating change is
  green.
- The prose and the code have already drifted without anyone noticing. The
  documented layering says `app/infrastructure/` sits below `app/domains/`, but
  `app/infrastructure/security.py` imports domain models, services and exceptions.
  Nothing reported this, because nothing was watching.
- Each rule file has to restate the rule for the reader *and* be trusted as the
  enforcement mechanism. It cannot be both.

## Objective

An architectural violation fails a deterministic check, locally and in CI, with a
message naming the offending import or construct — so that prose documents explain
*why* a rule exists and point at the check that enforces it, instead of being the
enforcement.

## In scope

- A deterministic gate over the **import graph**: layering between `app/api`,
  `app/workers`, `app/domains`, `app/infrastructure`; domains free of web and
  orchestration frameworks; workers free of `app/api`; a domain's repository
  private to its own domain.
- A deterministic gate over the **non-import invariants** that the import graph
  cannot see: no `commit()` in repositories and domain services, no direct
  service construction bypassing `for_user` / `for_system`, no
  `authorization_context=None` passed directly, custom repository reads scoped,
  response schemas free of secret fields.
- Wiring both gates into `just check`, the git hooks and CI, so the local and
  remote verdicts are identical.
- An escape hatch: a violation can be deliberately accepted, but only in a
  reviewable, named, justified way — never by silently disabling the gate.
- Rewriting the affected rule and architecture documents so each invariant names
  the check that enforces it, and reviewers are told not to re-verify it by hand.
- Recording the layering the checks will assert as an explicit, approved decision,
  including whatever today's drift turns out to mean.

## Out of scope

- Changing application behaviour. No route, schema, model, status code or
  database schema changes. The one module move in D1 is a relocation, not a
  behaviour change.
- Any refactor beyond D1. Other violations are declared truthfully in the
  contract rather than fixed here.
- Runtime or performance enforcement, dependency/CVE scanning, coverage
  thresholds, or any rule about test structure.
- Rules that are genuinely a matter of judgment (naming quality, when an
  abstraction is warranted, comment usefulness). These stay prose and stay human.
- Replacing the existing review agents. The sensors remove mechanical checks from
  their workload; they do not remove the review.

## Decisions taken (2026-09-21)

**D1 — `app/infrastructure/security.py` moves to `app/api/`.** Evidence: it imports
`fastapi` (`Depends`, `HTTPException`, `Security`, `APIKeyHeader`), raises
`HTTPException`, and its only production importer is `app/api/dependencies.py`.
Every other module under `app/infrastructure/` depends on `app/infrastructure/config`
and nothing else. It is an HTTP delivery adapter filed in the wrong package. Moving
it makes the documented three-layer model true, so the contract carries no permanent
exception. This brings the move into scope.

**D2 — `app/domains/sessions` may depend on `app/domains/users`.** A refresh session
belongs to a user; the dependency is directed and legitimate. The contract declares
`users` below `sessions` and continues to forbid the reverse. No code changes. Note
that `sessions/models.py` imports `users` only under `TYPE_CHECKING` (string-based
relationship and foreign key), so the sole runtime coupling is the test factory.

**D3 — tooling (revised 2026-09-21).** Three sensors, each given the invariants it
is actually able to decide:

- **import-linter** for the import graph (contracts in `pyproject.toml`).
- **ast-grep** for invariants expressible as observable syntactic structure.
  Declarative YAML rules, each with `valid` and `invalid` cases run by
  `ast-grep test`. MIT, 15 MiB, measured at 0.03s on this tree.
- **Runtime introspection tests** for invariants that need resolved types.

ast-grep is explicitly **not** treated as a semantic analysis engine. It reads
syntactic structure; it does not resolve types, data flow, symbols or the call
graph. A rule such as "every query is effectively user-scoped" is out of its reach
and is not claimed. See AC-B2.

Rejected: tach (a second module map beside `pyproject.toml`, duplicating
import-linter). pytest-archon (0.0.x, a year without release, import-graph only).
Hand-written `ast` visitors (the maintenance burden is the thing being avoided).
semgrep (47.6 MiB and 66 packages, LGPL-2.1, 1.70s per pass; and its natural
formulation of the AC-B4 rule was silently dead — it matched nothing, including a
deliberate violation, while looking green).

**D4 — delivery.** Structural rigor. Two slices, A then B, described in `acs.md`.

## Approval

Gate 1 approved by the human on 2026-09-21, covering this revision including the
amendments D1 and D2. The approval covers intent and scope only; the acceptance
criteria carry their own approval in `acs.md`.
