---
name: git-workflow
description: Apply this repository's branch, worktree, Conventional Commit and human-merge conventions when preparing or delivering a change.
---

# Git workflow

This skill owns branch, worktree and commit conventions. The delivery
sequence itself — check, independent review, QA, documentation
consolidation, human merge, cleanup — is defined once in
docs/development/workflow.md. Follow it there rather than a copy.

One independent change uses one branch and one worktree.
Use feature/<id>-<slug> or fix/<id>-<slug>, respecting any required client
prefix. Keep the main checkout clean. An explicitly authorized existing
checkout is a valid exception to creating a dedicated worktree.
Create a worktree only when authorized, from the intended main base, after
checking git status and git worktree list. Never move dirty work silently.
Do not edit another worktree or let multiple implementing agents write
the same checkout by default.

Use just setup inside the authorized checkout. Keep work-in-progress specs
with the implementation on the branch.

Commits use feat, fix, docs, style, refactor, perf, test, build, ci or chore.
Versioning and releases are automated: never bump project.version or create
release tags manually as a routine feature step.

## Pull request preparation and publication

After verification, independent review, QA and documentation consolidation,
prepare a Conventional Commit-style PR title and a body based on the final
diff, accepted contract, actual gate results and merge-risk assessment. This
preparation is local: show the exact base branch, title and body without
creating or changing anything remotely.

Before offering publication, verify that the worktree is clean, the reviewed
commit is the current HEAD, the independent review verdict is `Approve`, and
merge risk was assessed on that unchanged commit. Then ask one explicit
question authorizing both announced operations: push the current branch to
the named remote and create the PR against the named base with the shown title
and body.

That approval is single-use and authorizes nothing else. It does not permit a
force-push, merge, extra comments or labels, edits to another branch, cleanup,
or any other remote mutation. A material change to the diff, base, title or
body invalidates it. A changed diff also requires fresh affected checks,
review and merge-risk classification before a new publication request.

After approval, push only the announced branch, create the PR, and return its
URL. Merge remains a separate human gate. Git removal is never automatic:
git worktree remove and git branch -d are separate, explicitly authorized
steps. Never force removal and never delete shared PostgreSQL volumes.
