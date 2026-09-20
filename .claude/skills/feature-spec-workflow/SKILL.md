---
name: feature-spec-workflow
description: Turn a new feature request into human-validated intent and acceptance criteria, then classify tests and plan implementation where needed. Use for new features and scope changes; bugs and mechanical edits can use the short development path.
---

# Feature specification

Read architecture or domain instructions only when the current task needs
them. The rigor levels below mirror docs/development/workflow.md, which
remains the source for the full delivery sequence.

## Choose the necessary rigor

Propose a level; the user can change it:
- Bug or small edit: development, tests, review.
- Small feature: feature, AC, development, review.
- Business feature: feature, AC, useful Gherkin, plan, development, review, QA.
- Structural feature: the business path plus approval of significant
  architectural decisions and human QA when judgment is needed.

Also look for a split before planning, and report what you found. Several
ACs, several domains, a point where the product is already useful, or a
large expected diff are signals to look — not reasons to split. Split only
when an observable, coherent, independently deliverable boundary exists;
an atomic behaviour may cross several domains and have no shippable
intermediate state, and forcing a split there is worse than one honest
larger change. Each slice must be vertical — model through route through
tests, ending in observable behaviour — and releasable alone. Never split
by layer. See docs/development/workflow.md for the full rule.

Work in the feature's worktree. Never create a worktree or change another
checkout without authorization. Keep the primary main checkout clean.
For an existing authorized checkout, continue there.

## Human gate 1: feature.md

Create docs/specs/<id>-<slug>/feature.md with intention, problem/objective,
included scope and explicitly excluded scope. No technical design.
Prefer a ticket ID; otherwise propose a timestamp-based ID to avoid clashes
between parallel branches. Reuse an existing task directory when resuming.

Show the proposed intent and scope. Wait for explicit human approval before
writing acceptance criteria. Record the approval and what version it covers
briefly in the document; never infer approval from file existence.

## Human gate 2: acs.md

Write observable, implementation-independent criteria, each with an AC ID.
Cover happy paths, relevant boundaries, failures and security behavior.
An API contract may name an externally visible endpoint when that is itself
the requested product behavior; do not specify internal classes or tables.

Show the criteria and wait for explicit approval. Record the accepted
version. An approved implementation plan supplied by the user can serve as
existing authorization when it explicitly establishes these decisions;
do not require ceremonial reapproval.

When the feature is split, `acs.md` keeps the **whole** contract and assigns
every criterion to a slice. Give each one `Slice: <id>`, or `Slice: all` for
a cross-cutting criterion that every slice must satisfy — authorization and
transaction boundaries are the usual ones. Assign the mapping before any
implementation starts, as part of the approved contract. It may be revised
only by returning to the human, stating what changed and why; moving a
criterion to a later slice so that a review passes is a contract change
disguised as bookkeeping, and reviewers check the diff for exactly that.

## Transform the approved contract

Classify each AC as unit, integration and/or valuable business scenario.
An AC may need multiple levels. Explain briefly why Gherkin adds value, or
why none is needed. Put this mapping in acs.md, separate from the contract.

Write useful scenarios directly to features/<domain>/<behavior>.feature.
Never mechanically translate every AC or create an intermediate spec.feature.
pytest-bdd bindings belong in features/steps/test_<behavior>.py during
implementation. See features/README.md. Do not add a mandatory Gherkin gate.

For business/structural features, write plan.md with affected modules,
implementation order, test strategy, risks and unresolved decisions.
Significant product or architectural questions require human answers.
Routine implementation choices do not require another approval gate.

Once the work is authorized and decisions are resolved, hand off to the
existing tdd-implementation skill. If the request was specification-only,
stop after delivering the specification.

## Revisions and delivery

A scope change invalidates downstream approval where affected: explain
what changed and return to the relevant gate. Never rewrite the contract
silently to match an implementation.

Documentation consolidation before the human merge gate follows
docs/development/workflow.md. Remove temporary plans and duplicated ACs
only after checking that their useful information survives there.
