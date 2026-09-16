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
itself: give it no summary, rationale or account of what you did. Never
describe your own checks as independent approval. Address its findings,
then rerun the affected checks and the affected review.

QA, documentation consolidation, human merge and cleanup follow
docs/development/workflow.md. Branch, commit and worktree conventions are
in the git-workflow skill. Publishing, pushing and merging follow the
user's explicit authorization.
