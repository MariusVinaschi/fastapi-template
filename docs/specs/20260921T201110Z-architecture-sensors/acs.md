# Acceptance criteria — Executable architecture sensors

- Feature: `feature.md` (gate 1 approved 2026-09-21)
- Status: gate 2 approved (2026-09-21), amended with AC-08 at the same approval

The observable surface of this feature is the project's own quality gate. A
criterion is met when a deliberately violating change makes the gate fail, and a
conforming change leaves it green. "The gate" means `just check-architecture`, the
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

**AC-04 — The gate needs no database and no network.** `Slice: all`
The checks run against source and in-process type information only. They do not
open a database connection or make a network call.

**AC-05 — Exemptions are named, justified and perishable.** `Slice: all`
A violation may be deliberately accepted only through a declared exemption carrying
its target and a written reason. An exemption that no longer corresponds to an
actual violation fails the gate, so stale exemptions cannot accumulate. Disabling a
check wholesale is not an exemption mechanism.

**AC-06 — No behaviour change.** `Slice: all`
Routes, request and response payloads, status codes, authentication behaviour and
the database schema are unchanged. No Alembic migration is produced.

**AC-07 — The rule documents stop being the enforcement.** `Slice: all`
Each invariant this feature automates is, in the documents that state it, marked as
machine-checked and names the check that enforces it. The review guidance tells
reviewers not to re-verify those invariants by hand. Invariants that remain a matter
of judgment are not marked as checked.

**AC-08 — A dedicated command runs the architecture checks alone.** `Slice: all`
`just check-architecture` runs every invariant of this feature and nothing else: no
formatting, no typing, no application test suite. It is runnable on its own against
an unprovisioned checkout, without `just setup`, a database or a network. `just check`
contains it, so a full check cannot pass while the architecture command fails.

---

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

**AC-A5 — A new domain cannot slip past the boundary.** `Slice: A`
Adding a domain package without the declaration that confines its repository fails
the gate. A contract that is silently inapplicable to a new domain is treated as a
violation, not as a pass.

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

**AC-B2 — Custom reads stay scoped.** `Slice: B`
A custom read in a domain repository that builds a query without applying the
authorization scope fails the gate. The finders that deliberately bypass scoping for
authentication lookups pass only while declared as exemptions under AC-05.

**AC-B3 — Services are built through their factories.** `Slice: B`
A change constructing a domain service or repository directly, rather than through
the user-context or system-context factory, fails the gate.

**AC-B4 — A missing authorization context is deliberate, never incidental.** `Slice: B`
Passing an empty authorization context at a call site fails the gate. The prescribed
optional parameter in a repository or service constructor signature is not a
violation and does not fail the gate.

**AC-B5 — Responses carry no secrets.** `Slice: B`
A schema reachable from any route's declared response model that exposes a stored
credential, a password, a token or a hash fails the gate. Nested schemas and
paginated or otherwise parameterised response models are inspected as well. The
single endpoint that returns a freshly generated API key once passes only while
declared as an exemption under AC-05.

**AC-B6 — Every domain declares its authorization.** `Slice: B`
A domain whose entity has no authorization scope strategy, or whose repository does
not wire one, fails the gate.

---

## Test classification

Everything in this feature is developer-facing tooling. The criteria are
demonstrated by feeding each check a known-violating input and asserting it reports
the violation, then asserting the real tree is clean.

| AC | Level |
| --- | --- |
| AC-01, AC-02 | Unit — a violating fixture produces a non-zero exit and a message naming it. |
| AC-03 | Integration — CI and `just check` invoke the same entry point; verified by inspection of the invocation, not by a duplicate rule list. |
| AC-04 | Unit — the checks run in a process with no database reachable. |
| AC-05 | Unit — a stale exemption fails; an exemption without a reason fails. |
| AC-08 | Integration — the command runs on an unprovisioned checkout and reports every invariant; `just check` fails when it fails. |
| AC-06 | Integration — the existing API and migration suites, unchanged. |
| AC-07 | Reviewed by a human; no automated test. |
| AC-A1 … AC-A6 | Unit — each contract is run against a fixture package containing the violation it targets, and against the real tree. |
| AC-A7 | Integration — the existing authentication and security suites. |
| AC-B1 … AC-B6 | Unit — each sensor is run against violating and conforming fixture sources. |

**Gherkin: none.** There is no business actor and no product behaviour here. The
observable subject is a developer running a command, and a Gherkin scenario would
restate the criterion without adding a shared vocabulary with a stakeholder.
Writing one would be the mechanical translation `features/README.md` warns against.

## Approval

Gate 2 approved by the human on 2026-09-21, covering this revision including AC-08,
which the same approval requested and accepted. The slice assignment above is part
of what is approved and may only change by returning to the human.
