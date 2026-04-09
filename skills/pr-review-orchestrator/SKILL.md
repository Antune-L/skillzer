---
name: pr-review-orchestrator
description: "Orchestrate a full PR review in two phases: (1) run simplifier to clean up recent changes, then (2) dispatch code-review, architecture-review, and regression-check as parallel subagents and aggregate findings into one severity-ranked report. Trigger on 'review this PR/branch', 'PR review', or before merging a feature branch."
---

# PR Review Orchestrator

Run a complete PR-style review in two phases:

1. **Cleanup phase** — invoke the `simplifier` skill to apply mechanical simplifications on recently modified code. This is the only phase that edits code.
2. **Review phase** — dispatch three specialized analyses in parallel, then merge their outputs into one structured report. **Read-only.**

The cleanup phase runs first so the review phase operates on the cleaned-up diff — otherwise reviewers would flag nits that `simplifier` would immediately remove.

## When to use

- User asks for a "PR review", "branch review", "review this end-to-end"
- Before merging a feature branch
- Before requesting a human review (self-review pass)
- After a major refactor or feature completion

**Do not use** for: a quick review on uncommitted changes (use `code-review` directly), or for debugging a specific bug (use `systematic-debugging`).

## Scope modes

| Invocation | Scope passed to subagents |
|---|---|
| `/pr-review-orchestrator` (no arg) | Current branch vs `main`/`master` |
| `/pr-review-orchestrator <branch>` | Colleague's branch (`git fetch origin <branch>` first) |
| `/pr-review-orchestrator --staged` | Staged changes only |

Detect base branch via `git config init.defaultBranch`, fall back to `main` then `master`. Ask the user if neither exists.

**Skip cleanup phase** on colleague branches — never edit someone else's code. Run the review phase only.

## Procedure

1. **Resolve scope** — determine the diff range and changed files. Verify the branch exists; fetch if remote.
2. **Phase 1 — Cleanup** (own branches only; skip on `<colleague-branch>` mode):
   - Invoke the `simplifier` skill directly (`Skill("simplifier")`) with the list of changed files in scope.
   - Wait for it to finish and apply its edits.
   - Re-run the diff command to pick up the new state.
   - Announce to the user: "Phase 1 complete — simplifier applied N edits. Starting review."
3. **Phase 2 — Review: dispatch subagents in parallel** via the Agent tool — see [`references/dispatch.md`](references/dispatch.md) for exact prompts and subagent types.
   - Subagent A → runs the `code-review` skill (quality + reuse + dead code)
   - Subagent B → runs the `architecture-review` skill (cross-boundary + macro patterns)
   - Subagent C → `regression-checker` agent (blast-radius analysis)
   - **All three must be in the same message** for true parallelism. Sequential dispatch defeats the purpose.
4. **Wait** for all three reports. Do not start aggregation before all return.
5. **Normalize findings** — each subagent returns findings with severities. Map them onto the unified scale (`critical / warning / nit`) and the three report sections (Quality / Architecture / Blast radius).
6. **Dedupe carefully** — the three perspectives are complementary by design:
   - `code-review` handles local quality (DRY, SOLID, dead code)
   - `architecture-review` handles cross-boundary concerns (coupling, package deps, pattern divergence)
   - `regression-check` handles consumer impact
   - Only collapse findings if the message is **literally identical**. Do not merge a "local DRY" finding with an "architecture divergence" finding even if they touch the same file.
7. **Output aggregated report** — see [`references/report-format.md`](references/report-format.md) for the full template.

## The Iron Rule

**The review phase (Phase 2) never edits code.** The cleanup phase (Phase 1) is the only permitted write, and it delegates entirely to `simplifier` — this skill itself does not edit anything. After Phase 1 completes, no further edits happen regardless of what the user asks mid-report. If they want fixes applied, ask them to invoke `code-review` with an explicit fix request or edit manually.

Conflating review and edit (beyond the scoped Phase 1 cleanup) is what makes PR reviews drift into unrelated changes.

## Output shape (summary)

```
# PR Review — <branch> vs <base>

## Phase 1 — Cleanup
Simplifier applied N edits across M files. (Or: "Skipped — colleague branch.")

## Phase 2 — Review

### Summary
| Section       | Critical | Warning | Nit |
|---------------|----------|---------|-----|
| Quality       | X        | Y       | Z   |
| Architecture  | X        | Y       | Z   |
| Blast radius  | X        | Y       | —   |

Top themes: <2-3 sentences>

### Quality (from code-review)
<grouped by file>

### Architecture (from architecture-review)
<grouped by concern: cross-package, divergence, reinvention, layer leak>

### Blast radius (from regression-check)
<grouped by changed symbol>

### Recommended next actions
1. <prioritized list of fixes the user should consider>
```

Full template with example findings: [`references/report-format.md`](references/report-format.md).

## Rules

- **Phase order is fixed.** Cleanup → Review. Never swap, never skip review, never run review before cleanup.
- **Parallel dispatch only in Phase 2.** All three Agent calls in one message.
- **Never edit in Phase 2.** Read-only is non-negotiable after cleanup.
- **Skip Phase 1 on colleague branches.** Never modify someone else's WIP.
- **Never re-read files yourself.** Trust the subagents' output. Re-reading wastes the parent context — the whole point of subagents is to keep the parent lean.
- **Do not skip subagents.** If a section returns "no findings", still include it with that result. Empty sections are signal, not noise.
- **No invented findings.** If all three subagents report nothing, the output is "No findings". Do not pad.

## Gotchas

- **Simplifier edits before review.** If the user expects a review of the exact diff they wrote, Phase 1 will surprise them. Announce Phase 1 explicitly before running it so they know edits are happening.
- **Simplifier on a colleague branch is forbidden.** Explicit guard in the procedure — the detection is based on the scope mode (`/pr-review-orchestrator <branch>`).
- **Subagents do not share state.** Each one needs the scope (branch / files) explicitly passed in its prompt. Do not assume they can `git status` and figure it out.
- **Colleague branches must be fetched first.** The dispatch step must include `git fetch origin <branch>` before the Agent calls — otherwise subagents work on stale or missing refs.
- **`regression-checker` agent vs `regression-check` skill.** This skill dispatches the **agent** (`subagent_type: "regression-checker"`), not the skill — see [`references/dispatch.md`](references/dispatch.md) for the distinction and why it matters.
- **`code-review` and `architecture-review` are both skills** and need `general-purpose` subagents with the skill-name in the prompt. See dispatch.md.
- **Subagent context is fresh.** Each prompt must be self-contained: scope, base, branch name, what the parent project is. No "as we discussed".
- **Large diffs (50+ files):** warn the user upfront that the review may take longer; consider asking them to narrow the scope to specific paths. Also consider whether Phase 1 simplifier should be scoped to a subset.
- **Token budget:** the parent context only sees the final three reports. If a subagent returns 10k+ tokens of raw output, instruct it (in the dispatch prompt) to summarize before returning.
- **Overlap between code-review and architecture-review.** Both skills have explicit scope rules (see their SKILL.md files). Trust them — do not try to dedupe aggressively at the orchestrator level.

## Composability

- **`simplifier`** — invoked in Phase 1. The only skill that edits code in this orchestration.
- **`code-review`** — dispatched as Subagent A in Phase 2. Source of local quality/reuse/dead-code findings.
- **`architecture-review`** — dispatched as Subagent B in Phase 2. Source of cross-boundary, macro pattern, and macro wheel-reinvention findings.
- **`regression-checker` (agent)** — dispatched as Subagent C in Phase 2. Source of blast-radius analysis.
- **`coding-convention`** — not invoked directly; `code-review` already references it.
- **`systematic-debugging`** — not invoked; this skill is for review, not bug investigation.
