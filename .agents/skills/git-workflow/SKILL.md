---
name: git-workflow
description: Apply this repository's branch, worktree, Conventional Commit and human-merge conventions when preparing or delivering a change.
---

# Git workflow

This skill owns branch, worktree and commit conventions. The delivery
sequence itself — check, independent review, QA, documentation
consolidation, human merge, cleanup — is defined once in
docs/development/workflow.md. Follow it there rather than a copy.

One independent change uses one branch, one worktree and one workspace.
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

Merge requires human authorization. Git removal is never automatic:
git worktree remove and git branch -d are separate, explicitly authorized
steps. Never force removal and never delete shared PostgreSQL volumes.
