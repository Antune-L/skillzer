---
name: code-review
description: "Full code review (own branch or colleague's) for code principles violations and reinvented-wheel patterns. Trigger at end of coding or on any branch."
---

# Code Review

Branch-aware code review combining **code principles** analysis and **reuse detection**. Produces structured findings grouped by file with severity levels.

## Usage

- `/code-review` — review current branch vs its base
- `/code-review feat/xyz` — review a colleague's branch
- `/code-review feat/xyz main` — explicit base branch

## Procedure

### 1. Determine scope

```bash
# Own branch (no argument)
BASE=$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master)
git diff $BASE...HEAD --name-only

# Colleague's branch (argument provided)
git fetch origin <branch> --quiet
BASE=$(git merge-base origin/<branch> main 2>/dev/null || git merge-base origin/<branch> master)
git diff $BASE...origin/<branch> --name-only
```

If the base branch is neither `main` nor `master`, detect from git config or ask user.

Only review **changed files**. Ignore lock files, generated code, and migration files unless they contain hand-written logic.

### 2. Load diff context

For each changed file, read the full diff to understand changes. Read the full file when needed to check surrounding code (e.g., nearby helpers).

### 3. Detect project ecosystem

Before reviewing for reuse: read `package.json` (all deps), identify the component library (`components/ui/`), locate shared utilities (`lib/`, `utils/`, `hooks/`), and note project-specific patterns.

### 4. Review — Code Principles

Apply the full checklist from [`../code-principles-review/references/checklist.md`](../code-principles-review/references/checklist.md) across all changed files. Covers: DRY, SOLID, KISS, and library/component reuse.

Additionally check for **dead code & complexity** not covered by that checklist:
- Unreachable branches, unused variables/imports/exports
- Nested ternaries, deeply nested callbacks
- Functions exceeding ~50 lines without clear justification

For each suspected DRY or reuse violation, search the codebase (`Grep`/`Glob`) to confirm before flagging.

### 5. Output findings

Group by file. For each finding:

```
### `path/to/file.ts`

#### [critical] L42-L58 — Duplicated validation logic
The email validation regex is identical to `lib/validators.ts:L12`.
**Suggestion:** Import `emailSchema` from `lib/validators`.

#### [warning] L103 — Premature abstraction
`createGenericHandler<T>` has a single caller.
**Suggestion:** Inline directly. Extract only if a second use case emerges.

#### [nit] L77 — Unused import
**Suggestion:** Remove unused `useState` import.
```

Severity:
- **critical** — maintenance pain or bugs. Must fix.
- **warning** — real benefit, lower urgency. Should fix.
- **nit** — taste-level, low impact. Consider.

### 6. Summary

```
## Summary

| Severity | Count |
|----------|-------|
| Critical | X     |
| Warning  | Y     |
| Nit      | Z     |

**Key themes:** [1-2 sentences on main patterns across files]
```

If no findings, state it — do not invent issues.

## Rules

- Only review changed code — do not flag pre-existing issues in untouched lines
- Do not recommend adding new dependencies; only flag reuse of already-installed packages or native APIs
- Do not flag standard library usage (`Array.prototype`, etc.) as reinvention
- DRY applies at 2+ actual duplications, not hypothetical future ones
- SOLID applies differently to React components vs backend — a component combining render + simple hook is not SRP violation
- Do not auto-fix — present findings only. User decides what to action.

## Composability

- **`code-principles-review`** — this skill delegates the principles checklist to it. If `code-principles-review` is updated, this skill benefits automatically.
- **`codex-review`** — after presenting findings, follow the `codex-review` protocol: apply verification gates before claiming the review is complete, and when the user acts on findings, follow the code-review-reception protocol (technical rigor, no performative agreement, verify before implementing).
- **`coding-convention`** — defer naming, formatting, and file-placement issues to this skill.

## Gotchas

- When reviewing a colleague's remote branch, always `git fetch` first — local refs may be stale.
- `git merge-base` can fail if branches share no common ancestor (e.g., orphan branches). Fall back to asking the user for the base commit.
- On large diffs (50+ files), prioritize files with the most logic changes over config/style-only changes to stay within context budget.
