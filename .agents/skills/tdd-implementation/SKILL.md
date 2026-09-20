---
name: tdd-implementation
description: Implement an authorized change using the approved acceptance contract and a proportional test-first workflow. Supports features with or without Gherkin and small bug fixes.
---

# Development

Read the current feature's approved artifacts when present. Retain the
user's chosen scope and respect domain authorization and transaction
boundaries.

## Preconditions

Use the task's dedicated worktree, or the checkout explicitly authorized
for the current work. Use just setup for the API/test environment.
A bug needs a reproduction; a feature needs the human-approved intent and
ACs. Business/structural work also needs its plan and resolved significant
decisions. Do not manufacture missing product choices.

Work one slice at a time. If the authorized change turns out to contain a
real, independently deliverable boundary, say so and confirm the split
before implementing. Size alone is not that boundary: an indivisible
behaviour is delivered whole rather than cut into slices nobody can
demonstrate.

## Three rules that govern the loop

**One vertical slice at a time.** One failing test, the minimal
implementation that satisfies it, then the next. Do not write several
failing tests up front, and do not implement ahead of the current red test.
A slice crosses the layers it needs and ends in observable behaviour; if
your next test cannot be observed without a later slice, the split is
horizontal and wrong.

**Test at chosen public boundaries, not internal details.** Pick the
boundary before writing the test and say which it is: the HTTP route, a
service's public method, or a domain behaviour. Do not assert on private
helpers, on the shape of a generated query, or on call ordering between
internals. A refactor that preserves behaviour must leave the tests green —
if it does not, the test was bound to a detail.

**No tautological assertions, no mocking internal collaborators.** An
assertion must be able to fail for a real reason: never re-implement the
production computation in the test and compare the two, never assert only
that a mock was called, and never assert a literal the test itself just
built. Repositories, services, sessions and the database are internal
collaborators — use the real ones, with the real PostgreSQL. Mock only what
crosses a genuine external boundary: a third-party HTTP API, the clock,
randomness.

## Test-first implementation

1. For a behavioral change, write the smallest meaningful failing test and
   verify that it fails for the intended reason.
2. Implement enough to satisfy it, then refactor with tests green.
3. Use unit tests for pure logic and integration tests with real PostgreSQL
   for database behavior. Never replace the project's DB with mocks.
4. If useful Gherkin exists, bind it with pytest-bdd in
   features/steps/test_<behavior>.py and use it as the outer acceptance loop.
   Without Gherkin, the appropriate pytest tests provide that loop.
5. Use just test <test-path> for focused runs, just test-unit and
   just test-integration for level selection, and just bdd for Gherkin.
   Do not run behave or invent commands absent from the Justfile.

Mechanical edits do not require synthetic tests; validate the actual
affected behavior or format instead. Never alter approved ACs or scenarios
merely to make tests pass. Escalate ambiguity that changes the contract.

## Verification and review

Run just check. Fix failures and report any genuine execution limitation.
A check result only describes the code as it stood when it ran; any later
edit invalidates it.

Hand off to the existing review-orchestrator. It derives the change set
itself: give it no summary, rationale or account of what you did. Tell it
which slice this is when the feature is split, so conformance is judged
against the criteria that slice claims. Never edit the AC-to-slice mapping
to make a review pass: a criterion you cannot deliver returns to the human,
it does not move. Never describe your own checks as independent approval.
Address its findings, then rerun the affected checks and the affected
review. After the last slice, ask for the whole-contract review before
presenting the feature for merge.

QA, documentation consolidation, human merge and cleanup follow
docs/development/workflow.md. Branch, commit and worktree conventions are
in the git-workflow skill. Publishing, pushing and merging follow the
user's explicit authorization.
