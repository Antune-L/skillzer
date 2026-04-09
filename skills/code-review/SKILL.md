---
name: code-review
description: "Review changed code (session, current branch, or colleague's branch) for principle violations, reinvented wheels, and dead code. Trigger after coding, before merge, or for PR review."
---

# Code Review

Diff-scoped review for software design principles, library reuse, and dead code/complexity. **Read-only** by default — present findings, do not modify.

## Scope modes

| Invocation | Scope |
|---|---|
| `/code-review` (no arg) | **Session** — `git diff` (staged + unstaged) |
| `/code-review --branch` | Current branch vs `main` / `master` |
| `/code-review <name>` | Colleague's remote branch (`git fetch origin <name>` first) |

Detect the base branch via `git config init.defaultBranch` or fall back to `main` then `master`. If neither exists, ask the user.

**Skip:** lock files, generated code, migration files (unless they contain hand-written logic).

## Procedure

1. **Resolve scope** — list changed files for the chosen mode.
2. **Detect ecosystem** — read `package.json` (deps + devDeps), locate `components/ui/`, `lib/`, `utils/`, `hooks/`. Required for reuse detection.
3. **Apply checks** for each changed file:
   - Principles & reuse → [`references/checklist.md`](references/checklist.md)
   - Dead code & complexity → [`references/extra-checks.md`](references/extra-checks.md)
4. **Confirm before flagging** — for any DRY or reuse hit, `Grep`/`Glob` the codebase to confirm the duplication or existing utility actually exists. Never flag from intuition.
5. **Output findings** — see format below. If nothing is found, say so. Do not invent issues.

## Output format

Group findings by file. Each finding:

```
### `path/to/file.ts`

#### [critical] L42-L58 — Duplicated validation logic
The email regex matches `lib/validators.ts:L12`.
**Suggestion:** Import `emailSchema` from `lib/validators`.
```

Severity scale:

- **critical** — bug or maintenance pain. Must fix.
- **warning** — clear improvement, lower urgency. Should fix.
- **nit** — taste-level. Consider.

End with a summary table:

```
| Severity | Count |
|----------|-------|
| Critical | X     |
| Warning  | Y     |
| Nit      | Z     |

Key themes: <1-2 sentences on patterns across files>
```

For concrete before/after examples, see [`references/examples.md`](references/examples.md).

## Rules

- **Read-only.** Present findings; do not edit. The user decides what to action and asks explicitly.
- **Only changed code.** Never flag pre-existing issues in untouched lines.
- **No new dependencies.** Only flag reuse of already-installed packages or native APIs.
- **DRY needs 2+ real duplications.** Never hypothetical future ones.
- **SOLID adapts to React.** A component combining render + a small hook is not an SRP violation.
- **Standard library is not reinvention.** `Array.prototype.filter` over a lodash equivalent is fine.

## Gotchas

- Reviewing a colleague's branch: always `git fetch origin <branch>` first — local refs may be stale.
- `git merge-base` fails on orphan branches with no common ancestor — fall back to asking the user for the base commit.
- Large diffs (50+ files): prioritize files with logic changes over config/style-only changes to stay within context budget.
- A dependency in `package.json` that the codebase never imports is a strong reinvention signal — grep the package name; zero hits often means the team added it then wrote custom code instead.
- Session scope (`git diff`) misses untracked files. If new files are likely, run `git status` and add them to the review set manually.
- Do not flag a single-use helper as DRY — DRY applies at 2+ actual duplications.

## Composability

- **`architecture-review`** — complementary. Handles cross-package coupling, macro pattern divergence, and macro-level wheel reinvention. This skill handles **local** quality (function/variable-level DRY, SOLID, dead code, local complexity). If a finding is about a module boundary, package dependency, or divergence from sibling files, defer to `architecture-review`.
- **`regression-check`** — pair with this skill to map the blast radius of changed symbols. Complementary, not redundant.
- **`coding-convention`** — defer naming, formatting, and file-placement issues.
- **`simplifier`** — defer pure clarity/readability cleanup.
