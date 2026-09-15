---
name: tdd-implementation
description: Implement an approved plan.md against its promoted Gherkin spec.feature using outside-in (double-loop) TDD — the acceptance scenario is the outer loop, unit tests are the inner loop. Use this skill once a feature's plan.md has been approved by feature-spec-workflow and it's time to write code. Do not use for throwaway exploratory spikes explicitly flagged as such, or for one-line mechanical fixes with no behavior to specify.
---

# TDD Implementation (Outside-In / Double-Loop)

Implements an approved feature by working from its promoted acceptance
scenario down to unit-level code, never the other way around. Code is not
written speculatively "to make things work" — it's written to make a
specific failing test pass, one test at a time.

## Why double-loop, not "implement then test"

Writing tests after the implementation tends to describe what the code
already does, not specify what it must do — those tests pass but don't
meaningfully constrain behavior, which is exactly what shows up later as
a poor mutation score under `just mutate`. Writing the test first forces
it to fail for the right reason before anything makes it pass, which is
what makes it trustworthy evidence afterward.

This project already has the outer loop for free: the `.feature` file
promoted by the `feature-spec-workflow` skill is a failing acceptance test
before any code exists. This skill adds the inner loop underneath it.

## Prerequisites

- `plan.md` for this feature has been approved (see `feature-spec-workflow`).
- The corresponding `.feature` file has been promoted to
  `features/<domain>/<name>.feature` — if it's still sitting in
  `docs/specs/`, stop and promote it first rather than implementing
  against an unpromoted spec.
- `python-patterns` and `python-testing` rules apply automatically to any
  `.py` file touched — follow them without being reminded.

## Workflow

### Step 1 — Confirm the outer loop is RED

Run the acceptance suite for this feature's scenario:

```bash
uv run behave features/<domain>/<name>.feature
```

It should fail — usually because the step definitions don't exist yet, or
because they import production code that doesn't exist yet. That import
error **is** an acceptable RED state; don't treat it as a blocker to route
around. If the scenario unexpectedly passes already, stop and tell the
user rather than proceeding — something is already implemented, or the
scenario doesn't test what it's supposed to.

### Step 2 — Pick the smallest unit of behavior needed to progress

Look at what the failing scenario needs next (a function, a method, a
route handler) and drop into the inner loop for that one unit — resist
the urge to implement the whole feature in one pass.

### Step 3 — Inner loop: RED → GREEN → REFACTOR

1. **RED** — write a failing unit test for the smallest next piece of
   behavior. Run it, confirm it fails, and confirm it fails for the
   reason you expect (not a typo or import error).
2. **GREEN** — write the minimal production code to make that test pass.
   Minimal means minimal — don't implement adjacent behavior the current
   test doesn't require, even if you can see it coming; it gets its own
   RED first.
3. **REFACTOR** — clean up (naming, duplication, complexity) with the
   test suite green as a safety net. Re-run the unit tests after every
   refactor step, not just at the end.

Mock via the project's Protocol adapters (`LLMClient`, `EmbeddingClient`,
`RerankerClient`, `FileStorage`, `DocumentParser`) injected through DI —
see `python-testing` for the fake-vs-patch distinction. Never let a unit
test make a real external call.

### Step 4 — Re-run the outer loop

After each inner-loop cycle, re-run the behave scenario from Step 1. If
it still fails, return to Step 2 for the next unit of behavior it needs.
If it passes, move to the next scenario in the `.feature` file and repeat
from Step 1.

### Step 5 — Before handing off

Once every scenario in the promoted `.feature` file passes:

```bash
uv run pytest --cov=app --cov-report=term-missing
ruff check .
uv run ty check .
```

Fix anything these surface. Do **not** run `just crap` or `just mutate`
yourself and do not declare the feature "reviewed" — those are the
`review-orchestrator`'s job, run against a clean diff with a context that
deliberately excludes your reasoning here. Running them yourself and
folding the result into your own report would blur the separation that
makes that review meaningful.

## When strict double-loop TDD is overkill

For a genuinely mechanical change with no branching logic to specify (for
example, exposing an already-validated field on an existing response
model), the inner loop's ceremony can be skipped — but never skip the
test itself. Implement directly, then immediately write the test that
would have driven it, before considering the change done. If you're
unsure whether a change qualifies as "mechanical," default to the double
loop — it's cheap when the behavior is simple and valuable when it isn't.

## What this skill does not do

- It does not edit `spec.feature` to make a scenario pass. If a scenario
  turns out to be ambiguous, contradictory, or wrong once you're
  implementing it, **stop implementing immediately, end your turn, and
  describe the problem to the user** — don't quietly adjust the
  acceptance contract to match whatever you built, and don't guess at
  the "most reasonable" resolution yourself either. This is a deliberate
  exception to the general default of picking a reasonable interpretation
  and proceeding: an acceptance scenario is the one artifact in this
  pipeline the user explicitly approved as the contract, so resolving its
  ambiguity is the user's call, not something to infer silently. Wait for
  their reply before touching the scenario or the implementation again.
- It does not invoke `review-orchestrator` automatically. Implementation
  and review are separate steps handed off explicitly, not chained
  silently within this skill.

## Committing

Commit locally after each acceptance scenario turns green (Step 4),
using the conventional commit format from `git-workflow` — this keeps
commits small and matches the TDD rhythm rather than bundling a whole
feature into one commit at the end. Local commits don't need to be
asked for; they're reversible and stay on the feature branch.

**Never `git push`, force-push, or open a pull request without explicit
confirmation from the user** — pushing touches shared state even on a
feature branch (CI runs, others may see it), so it gets the same
confirm-before-acting treatment as any other action with external
effects. Finishing the last scenario in a `.feature` file is not, by
itself, permission to push.