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
- `plan.md`: affected architecture/modules, implementation order, test
  strategy, risks and open questions. Significant questions block dependent
  work and return to the human; ordinary technical choices do not.

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
types, complexipy (12 per function) and tests with coverage, stopping at the
first failing gate. Coverage has no new blocking threshold.

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

Human merge is the last gate. Then run `just cleanup` while still inside the
worktree. Separately verify the branch is merged and the checkout is clean
before removing the worktree and local branch. Cleanup never performs Git
removal or removes the shared PostgreSQL service.
