# Subagent Dispatch — Exact Prompts

How to brief each subagent so it returns useful, parent-context-friendly output.

## Phases

This orchestrator has two phases:

1. **Phase 1 — Cleanup:** invoke the `simplifier` skill directly in the parent (not a subagent). Simplifier edits files; the parent needs to see its results and sequence them before Phase 2. Skip Phase 1 entirely on colleague-branch mode.
2. **Phase 2 — Review:** dispatch three subagents in parallel. This file covers Phase 2.

## Phase 1 — Simplifier invocation

```
Skill("simplifier")
```

Then pass the list of changed files as the scope. Wait for edits to complete, re-run `git diff --name-only` to confirm the new state, and announce the edit count before moving to Phase 2.

## Why subagents and not inline skill calls (Phase 2)

Running `code-review`, `architecture-review`, and `regression-check` inline in the parent context would:
- **Bloat the parent context** with raw file reads and intermediate Grep results
- **Force sequential execution** — no parallelism, triple the wall time
- **Lose isolation** — one long review would push the others out of the working set

Subagents solve all three: each gets its own context window, they run in parallel when called in the same message, and only their final report flows back to the parent.

## Subagent A — Quality review (`code-review`)

**Tool:** `Agent`
**`subagent_type`:** `general-purpose`
**`description`:** `PR quality review`

**Prompt template:**

```
Run a code review on this scope:

- Repository: <absolute path or "current working directory">
- Branch: <branch-name>
- Base: <base-branch>
- Diff command: git diff <base>...<branch> --name-only

Use the `code-review` skill for the methodology and checklist. Apply it in read-only mode.

Specifically:
1. List changed files via the diff command above. Skip lock files, generated code, and migrations unless they have hand-written logic.
2. For each changed file, apply the principles checklist (DRY/SOLID/KISS/Reuse) and the dead-code checks from the skill's references.
3. Confirm any DRY or reuse hit by grepping the codebase before flagging. Do not flag from intuition.
4. Return findings grouped by file in this exact format:

### `path/to/file.ts`

#### [critical|warning|nit] L<start>-L<end> — <title>
<one-paragraph explanation>
**Suggestion:** <concrete fix>

End with a counts table:

| Severity | Count |
|----------|-------|
| Critical | X     |
| Warning  | Y     |
| Nit      | Z     |

Constraints:
- Read-only: do not edit any file.
- Only review changed lines, not pre-existing issues.
- Be concise. Total response under 4000 tokens. If you have more findings, prioritize critical and warning over nit.
- Do not invent findings. If nothing applies, say "No findings".
```

## Subagent B — Architecture review (`architecture-review`)

**Tool:** `Agent`
**`subagent_type`:** `general-purpose`
**`description`:** `PR architecture review`

**Prompt template:**

```
Run an architecture review on this scope:

- Repository: <absolute path or "current working directory">
- Branch: <branch-name>
- Base: <base-branch>
- Diff command: git diff <base>...<branch> --name-only

Use the `architecture-review` skill for the methodology and checklist. Apply it in read-only mode.

Specifically:
1. Detect the monorepo layout (turbo.json, pnpm-workspace.yaml, workspaces in root package.json). If none, treat as single package and skip cross-package checks.
2. For each changed file, identify its owning package and extract its imports.
3. Apply the 5 checks from `references/checks.md`:
   - Cross-package imports not declared in package.json
   - Inverted dependencies (packages → apps, cycles)
   - Pattern divergence from 2+ siblings
   - Macro wheel reinvention (new module overlapping an existing one)
   - Intra-package layer leak (only if layering is visibly enforced by other files)
4. Confirm every finding with concrete evidence (file:line, sibling path, package.json field).
5. Phrase findings as questions, not verdicts.
6. Return findings grouped by concern in this exact format:

### <concern name, e.g. "Cross-package coupling">

#### [critical|warning|nit] `path/to/file.ts:L<line>` — <short title>
**Evidence:** <concrete source>
**Question:** <what to ask the user>

End with a counts table:

| Severity | Count |
|----------|-------|
| Critical | X     |
| Warning  | Y     |
| Nit      | Z     |

Constraints:
- Read-only: do not edit any file.
- Only review changed lines and new files, not pre-existing issues.
- Do not flag local-quality issues (DRY at function level, naming, dead code) — those belong to `code-review`, not this skill.
- Do not invent conventions. Only flag patterns that 2+ sibling files actually agree on.
- Be concise. Under 4000 tokens. Prioritize critical and warning over nit.
- If nothing applies, say "No findings".
```

## Subagent C — Blast-radius analysis (`regression-checker`)

**Tool:** `Agent`
**`subagent_type`:** `regression-checker`
**`description`:** `PR blast-radius check`

**Why the agent, not the skill:** the user has a dedicated `regression-checker` subagent (visible in the agent list) optimized for this exact task. Dispatching it directly is cheaper than instructing `general-purpose` to load the skill.

**Prompt template:**

```
Map the blast radius of all changes in this scope:

- Repository: <absolute path or "current working directory">
- Branch: <branch-name>
- Base: <base-branch>
- Diff command: git diff <base>...<branch>

For every changed symbol (function, type, exported constant, component prop, API route), find every consumer in the codebase and flag mismatches:
- Renamed/removed symbols still referenced elsewhere
- Changed signatures with callers passing the old shape
- Modified return types with consumers expecting the old shape
- Removed exports still imported elsewhere

Return findings grouped by changed symbol in this format:

### `<symbol-name>` (in `path/to/file.ts`)
- **Change:** <what changed>
- **Consumers found:** <count>
- **Unhandled:** <list of consumer file:line that still reference the old shape>
- **Severity:** [critical|warning]

End with a counts table:

| Severity | Count |
|----------|-------|
| Critical | X     |
| Warning  | Y     |

Constraints:
- Read-only: do not edit any file.
- Be concise. Under 3000 tokens. Prioritize critical (broken consumers) over warning (deprecated patterns).
- If no consumers are affected, return "No regressions detected" — that is a valid result.
```

## Dispatching all three in parallel

In the parent skill, send **one message** with all three Agent tool calls. Example shape:

```
Agent({
  description: "PR quality review",
  subagent_type: "general-purpose",
  prompt: "<filled Subagent A template>"
})

Agent({
  description: "PR architecture review",
  subagent_type: "general-purpose",
  prompt: "<filled Subagent B template>"
})

Agent({
  description: "PR blast-radius check",
  subagent_type: "regression-checker",
  prompt: "<filled Subagent C template>"
})
```

All three run concurrently. Wait for all to return before aggregating.

## What to do if a subagent fails

- **Agent returns an error** → retry once with the same prompt. If it fails again, surface the error in the final report under a "Subagent failures" section. Do not silently drop a section.
- **Agent returns empty/garbage** → re-dispatch with an explicit reminder of the format constraint. If it still fails, include a note: "Quality review unavailable — investigate manually".
- **Agent times out on a huge diff** → re-dispatch with a narrower scope (specific subdirectories) and warn the user that the review is partial.
