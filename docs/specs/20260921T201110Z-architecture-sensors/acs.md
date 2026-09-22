# Acceptance criteria — Executable architecture sensors

- Feature: `feature.md` (gate 1 approved 2026-09-21)
- Status: gate 2 approved (2026-09-21); reduced scope approved by the human on
  2026-09-22: direct CLI checks only, without meta-tests or runtime introspection

The observable surface of this feature is the project's own quality gate. A
criterion is met when a deliberately violating change makes the gate fail, and a
conforming change leaves it green. "The gate" means `just architecture-check`, the
`just check` aggregate that contains it, and the equivalent CI job; all three must
always agree.

## Slices

| Slice | Delivers |
| --- | --- |
| **A** | The import graph is enforced, and the layering it asserts is true. |
| **B** | The invariants the import graph cannot see are enforced. |

Slice A includes the D1 module move, because the move is what makes A's contract
honest; shipping the contract with a permanent exception and moving the module
later would deliver an untrue gate. Each slice is releasable alone.

---

## Cross-cutting criteria

**AC-01 — A violation fails the gate.** `Slice: all`
Any invariant covered by this feature, when violated, makes the gate exit non-zero.
Nothing merges green on a violation.

**AC-02 — A failure names the offender.** `Slice: all`
The failure output identifies the offending module and, where the check operates on
source, the line and the construct. A developer can locate the problem without
re-reading the rule documents.

**AC-03 — Local and CI agree.** `Slice: all`
The same invariants are checked by `just check` and by CI, and produce the same
verdict on the same tree. CI cannot pass a tree that fails locally, or the reverse.

**AC-04 — The gate needs no database or application setup.** `Slice: all`
The checks run against source and in-process type information only. They do not
open a database connection or require application configuration.

**AC-05 — Exemptions are specific and perishable.** `Slice: all`
A violation may be deliberately accepted only through a declared exemption that
names **the specific rule it suppresses**. A blanket exemption, suppressing whatever
happens to match, fails the gate. An exemption that no longer corresponds to an
actual violation also fails the gate, so stale exemptions cannot accumulate.
Disabling a check wholesale is not an exemption mechanism.

**AC-06 — No behaviour change.** `Slice: all`
Routes, request and response payloads, status codes, authentication behaviour and
the database schema are unchanged. No Alembic migration is produced.

**AC-07 — The rule documents stop being the enforcement.** `Slice: all`
Each invariant this feature automates is, in the documents that state it, marked as
machine-checked and names the check that enforces it. The review guidance tells
reviewers not to re-verify those invariants by hand. Invariants that remain a matter
of judgment are not marked as checked.

**AC-08 — A dedicated command runs the architecture checks alone.** `Slice: all`
`just architecture-check` runs every invariant of this feature and nothing else: no
formatting, no typing, no application test suite. It does not require `just setup`,
an application database or application configuration. `just check` contains it, so a
full check cannot pass while the architecture command fails.

## Slice A — the import graph

**AC-A1 — Domains stay framework-agnostic.** `Slice: A`
A change in which any module under `app/domains/` imports a web or task-orchestration
framework fails the gate. Indirect imports, through an intermediate module, fail too.

**AC-A2 — Workers never reach the HTTP API.** `Slice: A`
A change in which any module under `app/workers/` imports any module under
`app/api/`, directly or indirectly, fails the gate.

**AC-A3 — The layer order holds.** `Slice: A`
A change in which a lower layer imports a higher one fails the gate. From higher to
lower: the HTTP API and the workers; then `app/domains/sessions`; then
`app/domains/users`; then the shared domain base; then `app/infrastructure`. The
HTTP API and the workers are independent of each other.

**AC-A4 — A repository is private to its domain.** `Slice: A`
A change in which a domain imports another domain's repository, directly or
indirectly, fails the gate — including when the two domains are otherwise allowed to
depend on each other under AC-A3.

**AC-A6 — Infrastructure sits below the domains.** `Slice: A`
After this slice, no module under `app/infrastructure/` imports any module under
`app/domains/`, and the gate enforces it with no exemption declared for it.

**AC-A7 — The move preserves authentication behaviour.** `Slice: A`
Access-token, refresh-token and API-key authentication keep their current behaviour:
same routes, same success responses, same failure status codes and error shapes.
The existing authentication and security tests pass, adjusted for the new import
path and for nothing else.

---

## Slice B — the invariants the import graph cannot see

**AC-B1 — Domain code never commits.** `Slice: B`
A change introducing a transaction commit in a domain repository or a domain service
fails the gate. Deliberate commits outside those roles, such as the test-data
factory, are unaffected.

**AC-B2 — Custom reads declare their scoping.** `Slice: B`
A literal `select(...)` call in a domain repository whose enclosing function
contains neither an application of the authorization scope nor an explicit
system-operation requirement fails the gate. Deliberate unscoped lookups pass only
while declared as exemptions under AC-05.

This criterion is a **syntactic contract, not a proof of authorization.** It
establishes that the scoping ritual is present in the method, and nothing more. It
does not and cannot establish that every execution path is correctly scoped: that
requires type resolution, data flow and call-graph analysis, which no sensor in this
feature performs. Authorization correctness remains a matter for review and for the
authorization tests in the existing suite. A green AC-B2 must never be read as
evidence that a query is safe.

**AC-B3 — Services are built through their factories.** `Slice: B`
A direct call through a bare UpperCamelCase identifier whose name ends in `Service`
or `Repository` fails the gate; application code uses the user-context or
system-context factory instead. Qualified calls, aliases and symbol resolution are
outside this syntactic contract.

**AC-B4 — A missing authorization context is deliberate, never incidental.** `Slice: B`
Passing an empty authorization context at a call site fails the gate. The prescribed
optional parameter in a repository or service constructor signature is not a
violation and does not fail the gate.

---

## Test classification

Everything in this feature is developer-facing tooling. The accepted public
boundary is the command itself: Import Linter and ast-grep scan the real tree and
their non-zero exit status fails the gate. Synthetic tests of the linters are
deliberately outside scope.

| AC | Level |
| --- | --- |
| AC-01, AC-02 | Direct tool execution — each configured sensor reports violations through its CLI. |
| AC-03 | Integration — CI and `just check` invoke the same entry point; verified by inspection of the invocation, not by a duplicate rule list. |
| AC-04 | Direct tool execution — both sensors inspect source/imports only and need no application setup. |
| AC-05 | Tool configuration — unmatched Import Linter ignores and unused or blanket ast-grep suppressions are errors. |
| AC-08 | Integration — the dedicated recipe runs both CLIs and is included in `just check`. |
| AC-06 | Integration — the existing API and migration suites, unchanged. |
| AC-07 | Reviewed by a human; no automated test. |
| AC-A1 … AC-A4, AC-A6 | Direct `lint-imports` execution against the real tree. |
| AC-A7 | Integration — the existing authentication and security suites. |
| AC-B1 … AC-B4 | Direct `ast-grep scan` execution against the real tree. |

**Gherkin: none.** There is no business actor and no product behaviour here. The
observable subject is a developer running a command, and a Gherkin scenario would
restate the criterion without adding a shared vocabulary with a stakeholder.
Writing one would be the mechanical translation `features/README.md` warns against.

## Approval

Gate 2 approved by the human on 2026-09-21. On 2026-09-22 the human approved the
reduced contract: AC-09, AC-A5, AC-B5 and AC-B6 were removed; direct CLI execution
replaces architecture meta-tests, and B2/B3 are limited to source forms ast-grep can
resolve. The remaining slice assignment is unchanged.
