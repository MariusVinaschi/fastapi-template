# AI development workflow

Project logic lives behind `just`, so this workflow runs the same way from a
terminal, a multiplexer, an editor or CI. Choosing and driving those sessions is
outside this repository's scope.

## Work and human decisions

One independent change = one branch = one worktree = one session. Keep the
main checkout clean; implementing agents normally do not share a worktree.
Create worktrees only when authorized. The initial workflow installation is
being completed in the existing `docs/agents-skills-setup` checkout.

| Change | Required path |
| --- | --- |
| Bug / small edit | Development → tests → review |
| Small feature | Feature → human approval → AC → human approval → development → review |
| Business feature | Feature → approval → AC → approval → test classification → useful Gherkin → plan → development → check → review → QA |
| Structural feature | Business path + human approval of significant architecture + human QA where judgment is needed |

The agent proposes rigor and the user may change it. Product/scope decisions,
significant architectural choices and final merge belong to the human.
Once the contract is approved, routine transformations can continue under
the existing implementation authorization without ceremonial extra gates.
The abbreviated bug/small-feature paths include proportional QA: demonstrate
the reproduction or accepted behavior. They do not require an extra human QA
gate unless product judgment is needed.

## One change or several

A feature is not automatically one change, and not automatically several.
Before writing `plan.md`, look for a split and report what you found.

These conditions **trigger the search**. They are signals, never sufficient
reasons on their own:

- a subset of the acceptance criteria looks independently demonstrable;
- the work crosses more than one domain under `app/domains/`;
- the implementation order seems to reach a point where the product is
  already useful to someone;
- the expected diff looks large.

Then **split only when an observable, coherent, independently deliverable
boundary actually exists.** An atomic behaviour may legitimately cross
several domains and have no intermediate state worth shipping. Forcing a
split there produces slices that cannot be demonstrated and reviews that
cannot conclude — worse than one honest larger change. When no such
boundary exists, say so and keep it as one change.

Diff size stays an indicator, never a rule: a configuration change can
touch ten files and remain conceptually tiny, while a single indivisible
behaviour can be long. Size prompts the question; only the boundary
answers it.

Each slice stays **vertical**: it crosses every layer it needs — model,
repository, service, route, tests — and ends in behaviour someone can
observe. Never slice horizontally, all models first and services later:
a horizontal slice cannot be demonstrated, cannot be reviewed against a
criterion, and cannot merge alone.

Slices are ordered so each one is releasable on its own. One slice = one
branch = one worktree = one review. `feature.md` and `acs.md` stay the
shared contract: `acs.md` keeps every criterion and assigns each one
`Slice: <id>`, or `Slice: all` when it is cross-cutting and every slice
must satisfy it.

The mapping is fixed before implementation starts. A criterion that turns
out to be undeliverable returns to the human with what changed and why; it
is never quietly moved to a later slice to let a review pass, and reviewers
check the diff for that edit. A slice review judges only that slice's
criteria plus the cross-cutting ones and reports the rest as **deferred**,
not missing. After the last slice, a whole-contract review judges every
criterion with nothing deferred — that is the gate that catches what each
slice left to the next and nobody delivered. The human merge gate for a
split feature comes after that review, not after the last slice.

Prefer fewer, larger criteria over splitting a single behaviour across
slices: a slice that needs another slice to be observable is horizontal
in disguise.

## Specification in the feature worktree

Use `docs/specs/<ticket-or-timestamp>-<slug>/` with `feature.md`, `acs.md` and,
where useful, `plan.md`. Prefer a ticket ID; without one, use a UTC timestamp
such as `20260916T120000Z-hybrid-retrieval` to avoid parallel numbering races.

- `feature.md`: intention, objective, included and excluded scope. No design.
- `acs.md`: numbered observable criteria, independent of implementation;
  happy paths, meaningful boundaries, failures and security. Record human
  approval briefly, with the accepted revision/date, never invent it.
- After approval, append an AC-to-test mapping: unit, integration and/or
  useful business scenario. Gherkin is optional and never a mechanical copy.
- `plan.md`: an extremely concise, scannable list of affected modules,
  implementation order, test strategy and risks; do not repeat the feature or
  ACs. End with `## Open questions`, using `None` when there are none.
  Significant questions block dependent work and return to the human;
  ordinary technical choices do not.

Write executable Gherkin directly into `features/<domain>/<behavior>.feature`.
The existing specification and TDD skills live in `.agents/skills/` and are
copied verbatim into `.claude/skills/`; a test keeps the copies identical, so
edit the `.agents/` source. Read only the current feature and
relevant architecture/domain guidance, not every file in docs.

A changed scope or contract requires renewing the affected human approval.
An already approved, sufficiently explicit plan is existing authorization,
not a reason to restart specification from scratch.

## Development, review and QA

Use the existing TDD skill, then `just check`. It runs lint, format verification,
types, complexipy (12 per function), the architecture gate and tests with coverage,
stopping at the first failing gate. Coverage has no new blocking threshold.

`just architecture-check` runs the structural checks alone, needs no database and no
`just setup`, so it is usable while writing. Reviewers do not need to duplicate the
gate's exact syntax/import checks, but they still review architectural intent, scope,
exceptions and semantic correctness. What each gate covers, and what it explicitly
does not establish, is in the architecture documentation.

Use the existing review-orchestrator and Python/FastAPI reviewers. Start them
without implementation history (Codex: `fork_turns="none"` when available).
Give raw diffs, additions, check results and relevant constraints, never the
implementer's reasoning. Include branch changes and pending work: compare
the working tree against the branch's merge-base and inventory untracked
files with `git ls-files --others --exclude-standard`. Do not stage files
just to review them. Reviewers can inspect adjacent source to prove findings.

Review runs just check itself rather than trusting a result recorded by the
implementer. If tooling cannot provide independent
context, disclose the limitation and use a new discussion. Review remains
read-only; implementation addresses findings and repeats affected checks.

QA maps the accepted criteria to demonstrated behavior. Automate verifiable
checks; ask the human for product judgments automation cannot settle. A green
test suite alone does not establish that the intended product was delivered.

After the technical and contract review reaches `Approve`, classify merge
risk independently on that approved, unchanged diff. Reversibility is
`two-way`, `conditional` or `one-way`; blast radius is `low`, `medium` or
`high`. The assessment cites evidence in the diff, states the worst credible
failure, explains rollback or recovery, and names the required depth of human
review. A `one-way` change or `high` blast radius does not become safe because
automated gates pass: it requires explicit migration, rollout and recovery
consideration before merge.

Do not classify merge risk when review returns `Warning` or `Block`; report it
as not assessed and resolve the review first. Any material diff change makes
both the review verdict and risk assessment stale, so repeat the affected
checks and the full independent review before assessing risk again.

## Documentation and delivery

Before presenting the change for merge, consolidate:

| Information | Durable destination |
| --- | --- |
| Product behavior | Tests, Gherkin, product documentation |
| Architectural decision and rationale | ADR or architecture documentation |
| Current operation or interface | Relevant current documentation |
| Intermediate reasoning | Remove |

Plans normally disappear before merge. Preserve the valuable why from feature
documents elsewhere; remove AC documents only after their contract survives
in tests and documentation. Never delete unreviewed user documents blindly.
The repository should describe its current system, not accumulated agent notes.

After consolidation, the agent prepares a Conventional Commit-style PR title
and a body using the final diff, accepted contract, verification results and
merge-risk assessment. Preparation is local and automatic. It performs no
remote operation and presents the exact base branch, title and body.

Pushing and creating the PR share one explicit, single-use human gate. The
agent asks permission to push the named current branch to the named remote and
create the PR against the shown base with the shown title and body. Approval
does not authorize force-push, merge, extra comments or labels, another remote
mutation, or cleanup. A material change to the diff, base, title or body
invalidates approval; a changed diff also invalidates its checks, review and
risk classification.

Keep the PR body concise: summarize what and why, list delivered ACs and actual
verification, then reduce merge risk to its classification plus one sentence
covering failure and recovery. Do not paste full reviewer reports; mention
documentation only when it helps understand the change. Creating the PR
returns its URL but never implies merge authorization. Human merge is the last
gate. Then run `just cleanup` while still inside the worktree. Separately
verify the branch is merged and the checkout is clean before removing the
worktree and local branch. Cleanup never performs Git removal or removes the
shared PostgreSQL service.
