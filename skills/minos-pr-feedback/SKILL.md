---
name: minos-pr-feedback
description: 'Triage and fix reviewer comments on a GitHub PR via gh. When the user has feedback on a PR (from a human or a bot like gemini-code-assist) and wants the pertinent items fixed — "j''ai des retours sur la PR", "résous/corrige ce qui est pertinent", "retours de gemini-code-assist", "lis les commentaires de la PR via gh" — fetch every comment thread, triage by relevance, and apply only the pertinent fixes; drop nits, skip resolved/outdated threads. Auto-resolves the PR number from the current branch. Does NOT post comments — publishing findings is argus-review --post.'
---

# minos-pr-feedback — triage and fix reviewer comments on a PR

> Minos, judge of the dead, who weighs each soul and pronounces its fate. This skill weighs each reviewer comment — apply or dismiss — and acts only on those that earn it.

A reviewer (human or a bot like `gemini-code-assist`) left comments on the PR. Fetch them, **triage by relevance**, and **apply only the pertinent fixes** — drop nits. The genuinely uncovered workflow: existing review skills review *your* diff, they don't consume *others'* comments. This is the step the user otherwise does by hand on nearly every PR.

## When to use

- "j'ai des retours sur la PR N", "résous/corrige ce qui est pertinent", "les plus pertinents à corriger"
- "retours de gemini-code-assist, qu'en penses-tu ?", "lis les commentaires de la PR via gh"

## When NOT to use

- **Generating** a review of a diff → that is `argus-review` / `pr-review-orchestrator`. This skill consumes existing comments; it does not fan out reviewers.
- **Posting** our own findings to a PR → that is `argus-review --post`. This skill never publishes comments.
- Replying to a reviewer in prose without changing code → just answer; no skill needed.
- A single obvious comment the user already pasted inline → just fix it.

## Resolve the target PR

Never ask the user for the PR number when it is derivable.

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
PR=$(gh pr view --json number -q .number)            # current branch → its open PR
# named branch instead of current:  gh pr view <branch> --json number -q .number
```

- An explicit number in the prompt always wins (even a fuzzy "PR 67 j'imagine" — verify it matches the branch, correct it if not).
- No PR for the branch → tell the user. Never invent a number.

## Procedure

Full `gh` commands and the triage rubric: [`references/procedure.md`](references/procedure.md). Essentials:

1. **Resolve the PR** (above).
2. **Fetch all three comment sources** — comments live in three different GitHub APIs; fetching only one misses feedback:
   - inline review comments (`/pulls/{PR}/comments`),
   - review summaries + state (`/pulls/{PR}/reviews`),
   - top-level conversation comments (`/issues/{PR}/comments`).
3. **Drop noise** — skip comments on resolved threads, `outdated`/superseded lines, and the user's own. Bots (`gemini-code-assist`, `coderabbitai`, …) post a verbose summary + many inline nits — judge each on merits, not by volume.
4. **Triage each surviving comment** into `apply` / `skip-nit` / `skip-wrong`, each with a one-line reason (rubric in `procedure.md`). Default: only `apply` the genuinely pertinent; **nits are skipped** unless the user said otherwise.
5. **Present the triage table first** (comment → verdict → reason), then **apply the `apply` set** as real code changes — grouped, smallest diff, reusing existing project patterns.
6. **Check regressions** on changed symbols (per the user's workflow) and run typecheck/lint on touched files.
7. **Commit + push the applied fixes** — stage only the files minos touched, commit with a conventional message, and push to the PR's head branch so the PR updates. Only after checks pass; skip entirely if nothing was applied or if a check failed. See [`references/procedure.md`](references/procedure.md) §6.
8. **Do not auto-reply or resolve threads** unless asked — the standing instruction is "pas besoin de répondre, applique ce qui te semble pertinent".
9. **Report**: what was applied (file:line), what was skipped and why (nit / out-of-scope / wrong), counts, and the pushed commit sha.

## Gotchas

- **Three comment APIs, not one.** Inline comments, review summaries, and conversation comments are separate endpoints. "J'ai des retours" can land in any of them — fetch all three or miss feedback.
- **PR# is derivable — never ask.** Resolve from the branch; the user routinely doesn't know it ("67 j'imagine"). Verify a user-given number against the branch.
- **Bots are nitty.** `gemini-code-assist` / `coderabbitai` mix a few real findings into many nits and style preferences. Triage on merits; the user wants "ce qui est pertinent", not all of it.
- **Skip resolved/outdated threads.** Re-fixing a resolved comment is noise. Filter on thread resolution + `outdated`/`position: null`.
- **Don't auto-reply, don't post comments.** Never publish review comments back to the PR (that is `argus-review --post`). Committing + pushing the fixes is separate and expected — it updates the PR diff, it does not post conversation.
- **Apply respects project conventions.** Fixes are real code — reuse existing components/patterns, no `as` casts, minimal diff, check regressions (same standards as any code change).
- **Heavy commit hooks ≠ stuck commit — never `--no-verify`.** Some repos (e.g. fftir-thot's lefthook) run `pnpm i --frozen-lockfile` + full-monorepo turbo lint/format/check-types on pre-commit: several minutes, longer than the default 2-min Bash timeout. Run `git commit` with `timeout: 600000` (or `run_in_background`) and wait. Do NOT kill lefthook/turbo processes, do NOT fall back to `--no-verify` (it also skips commitlint and transcrypt). If the hook genuinely fails, report the failure instead.
- **Commit only the files minos touched, push only on the PR's head branch.** Never `git add -A` (the working tree may hold unrelated changes); never push a broken tree (checks gate the commit) or a branch that isn't the PR head (flag instead). Risky fixes still get flagged in the report even though they're pushed.
