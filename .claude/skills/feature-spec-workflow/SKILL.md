---
name: feature-spec-workflow
description: Scaffold a new feature through a staged, human-validated specification workflow (feature.md -> acs.md -> spec.feature -> plan.md) before any code is written, then promote the validated Gherkin spec into the project's executable behave/pytest-bdd test tree. Use this skill whenever the user asks to start, scaffold, or kick off a new feature, ticket, or piece of work, or mentions writing acceptance criteria, Gherkin scenarios, or an implementation plan for something not yet built. Also trigger on phrases like "new feature", "nouvelle feature", "let's spec this out", or when the user describes a need and expects it to be turned into a structured spec rather than immediate code. Do not use this skill for bug fixes, small tweaks, or when the user explicitly asks to skip straight to implementation.
---

# Feature Spec Workflow

A staged workflow that turns a plain-language need into a validated, layered
specification before any implementation begins, then hands off a clean
executable artifact to the codebase's real test tree. Each layer constrains
and informs the next: business intent (`feature.md`) narrows into testable
criteria (`acs.md`), which translate into executable scenarios
(`spec.feature`), which finally ground a technical plan (`plan.md`).

This skill deliberately keeps two directory trees separate, because they
serve different readers and evolve on different axes:

- **`docs/specs/<number>-<short-name>/`** — the planning trail. Organized
  chronologically, because _when_ and _in what order_ a decision was made
  is the useful signal here (a later feature's plan may depend on an
  earlier one's decisions). Never executed by any test runner.
- **`features/<domain>/`** — the executable Gherkin suite that `behave` or
  `pytest-bdd` actually runs. Organized by business domain (mirroring the
  codebase's own module boundaries), because six months from now, a failing
  test should be findable by _what it tests_, not by _when it was written_.
  A single domain file often accumulates scenarios from several unrelated
  planning timelines — that's expected, not a smell.

Stages 1-4 write only into `docs/specs/`. A final promotion step moves the
validated scenario into `features/`, renamed by domain instead of by
number.

## Why this exists

Skipping straight from a vague request to code is where ambiguity hides.
Each stage below exists to catch a specific kind of ambiguity early, while
it's still cheap to fix:

- `feature.md` catches scope creep — is the "why" actually clear?
- `acs.md` catches missing edge cases, in a form a non-technical stakeholder
  can still validate.
- `spec.feature` catches criteria that sound fine in prose but turn out to
  be untestable or contradictory once forced into a concrete scenario.
- `plan.md` catches technical dead ends before they're implemented.
- Promotion (Stage 5) catches domain misclassification — if you can't name
  a clean domain for the scenario, that's often a sign the feature itself
  is still too broad or crosses a boundary that hasn't been thought through.

Producing all five in one shot defeats the point. Validate one layer with
the user before writing the next — a mistake caught at `feature.md` costs a
sentence to fix; the same mistake caught at `plan.md` may cost a rewrite of
all three preceding files.

## Prerequisites

Before starting, read the project's `CHARTER.md` and `CLAUDE.md` if they
exist — they define stack choices, architectural invariants, and
conventions that every later stage (especially `plan.md`) must respect.
If neither file exists, proceed without them but do not invent constraints
that weren't stated.

## Workflow

Run the five stages below in strict order. **Stop after each stage and wait
for explicit user approval before starting the next one.** Do not write
production code at any point in this workflow — that begins only after
`plan.md` is approved, and only if the user asks for it separately.

Determine the feature's planning directory before Stage 1: look for an
existing `docs/specs/` directory, find the highest existing number, and use
the next one (zero-padded to 3 digits, e.g. `003`). If no `docs/specs/`
directory exists, create it and start at `000`. Derive a short kebab-case
name from the user's request for the folder suffix (e.g.
`docs/specs/003-user-signup/`). This number is a planning-trail identifier
only — it never appears in the file that lands in `features/`.

### Stage 1 — `feature.md`

Capture intent only. Write:

- **Intention**: 2-4 sentences covering what the feature does and why it
  matters. No implementation detail.
- **Scope**: explicit bullet lists of what's included and what's
  deliberately excluded (excluded items prevent silent scope creep later).
- **Branch**: suggested branch name, `feature/<number>-<short-name>`.

If the request is too vague to write a clear intention, say so and ask for
the missing piece rather than guessing at scope.

Show the file to the user and stop. Do not proceed to Stage 2 until they
approve or request changes.

### Stage 2 — `acs.md`

Once `feature.md` is approved, expand it into acceptance criteria (ACs):
plain, testable statements of behavior, grouped by category (adapt
categories to what's relevant — typical ones are happy path, edge cases,
errors, and security).

This is the layer most prone to a specific failure mode: **implementation
leakage**. An AC that names a class, a function, an endpoint, a table, or
any internal design detail has jumped ahead to Stage 4's job and stops
being verifiable by someone who only knows the product, not the code. If
writing a clean AC requires knowing an implementation detail that hasn't
been decided yet, ask the user instead of inventing one.

Example of the distinction to enforce:

- Leaky (avoid): "The `UserRepository.find_by_email` returns `None` when
  no match exists."
- Clean (use): "Signing up with an email that has no existing account
  succeeds."

Show the file to the user and stop. Do not proceed to Stage 3 until they
approve or request changes.

### Stage 3 — `spec.feature`

Once `acs.md` is approved, translate each AC (or tightly related group of
ACs) into a Gherkin scenario, in the language the user has been using in
this conversation. Use standard Given/When/Then structure (plus And/But as
needed). Keep each scenario to roughly 3-5 steps — a scenario running much
longer usually means it's testing more than one behavior and should be
split.

Apply the same no-implementation-detail rule as Stage 2: scenario steps
describe observable behavior, not internals.

If an AC resists a clean Gherkin translation — it's really a non-functional
requirement, or it's ambiguous about the actual trigger or outcome — flag
it to the user instead of forcing an awkward scenario.

Write this file to `docs/specs/<number>-<short-name>/spec.feature` — it
stays in the planning tree at this stage, not yet in `features/`.

Show the file to the user and stop. Do not proceed to Stage 4 until they
approve or request changes.

### Stage 4 — `plan.md`

Once `spec.feature` is approved, write the technical implementation plan:

- **Architecture**: which modules/files to create or modify, respecting
  every constraint found in `CHARTER.md`/`CLAUDE.md`.
- **Steps**: implementation order, and why that order (e.g. dependencies
  between pieces).
- **Risks**: anything uncertain — a library behaving unexpectedly, a
  performance concern, an integration that hasn't been tested before.
- **Open questions**: any structurally significant decision that should be
  the user's call, not yours. Do not silently resolve these — list them
  explicitly and wait.

Show the file to the user and stop before promoting anything.

### Stage 5 — Promote `spec.feature` into the executable suite

Once `plan.md` is approved, move (don't copy — one source of truth) the
scenario file out of the planning tree and into the project's real
`features/` tree, renamed by domain:

1. Identify the business domain this feature belongs to. Prefer matching
   an existing `app/domains/<domain>/` (or equivalent) module boundary
   named in `plan.md`. If none fits cleanly, ask the user rather than
   guessing a new domain name.
2. Check whether `features/<domain>/` already exists. If not, create it,
   along with `features/steps/` at the top level if it doesn't exist yet —
   step definitions live in one shared `features/steps/` directory, never
   nested per-feature or per-domain, so the test runner can resolve them
   without ambiguity.
3. Move the file to `features/<domain>/<short-name>.feature` — a
   descriptive, domain-scoped name, not the planning number (e.g.
   `docs/specs/004-retrieval-avance/spec.feature` becomes
   `features/rag/hybrid_retrieval.feature`).
4. Leave `feature.md`, `acs.md`, and `plan.md` in `docs/specs/` in place,
   but append a one-line note to `feature.md` recording the promoted
   path (e.g. `Promoted to: features/users/hybrid_retrieval.feature`) so
   the planning record stays traceable to its executable counterpart.
5. Do not generate step definitions in this stage unless the user asks —
   that's implementation work for whichever workflow follows this one.

Show the user the new path and stop. This workflow ends here — do not
begin implementation even if the plan looks complete and unambiguous,
unless the user explicitly asks you to proceed.

## Output structure

```
docs/specs/<number>-<short-name>/    # planning trail, chronological
├── feature.md
├── acs.md
├── spec.feature                     # present only until Stage 5 promotes it
└── plan.md

features/                            # executable suite, organized by domain
├── steps/
│   └── <domain>_steps.py
├── environment.py
└── <domain>/
    └── <short-name>.feature         # the promoted scenario
```

## Handling interruptions and revisions

If the user requests a change partway through (e.g. after seeing
`spec.feature`, they want to revise `feature.md`), make the edit, then
re-check whether it invalidates anything already approved downstream. A
scope change in `feature.md` often requires revisiting `acs.md`. Point this
out rather than silently patching only the file the user mentioned.
