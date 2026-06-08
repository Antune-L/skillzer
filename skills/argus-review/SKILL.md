---
name: argus-review
description: 'When asked to review a PR or branch ("review this PR", "PR review", "argus", before merging), fan the diff out to parallel read-only reviewers and return a severity-ranked verdict; optionally post inline via gh.'
---

# Argus — autonomous PR review

> Argus Panoptes, the hundred-eyed watchman who never fully sleeps. This skill is the hundred eyes: it fans the diff out to several independent reviewers at once, then judges what they saw.

**Self-contained by design.** Unlike a dependency-coupled orchestrator, Argus assumes **nothing else is installed** — no companion skills, no custom `pr-*-reviewer` agent types. It dispatches the **default `general-purpose` subagent** and inlines each reviewer's complete methodology into its prompt. Drop the `argus/` folder into any agent setup and it works.

**Coordinator + read-only.** Argus never edits code. It dispatches, validates structured replies, aggregates a verdict, and (only when asked) posts findings to a PR. It does not review code itself in the parent — that would defeat the fan-out.

## When to use

- "Review this PR / branch", "review against `<base>`", "PR review", "argus"
- Self-review before opening a PR or before merging
- After a refactor or feature completion

## When NOT to use

- Quick pass on uncommitted scratch work — review inline, no orchestration needed
- Debugging a specific failure — that is a debugging task, not a review
- Applying fixes — Argus is read-only; fix in a separate step
- Repo-wide audits — every reviewer is diff-scoped

## Invocation & scope

| Invocation                     | Meaning                                                                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `argus`                        | Current branch vs base — **light** (3 reviewers: quality, conventions, regression)                                                       |
| `argus --full` (or "complet")  | Current branch vs base — **full** (5 reviewers)                                                                                          |
| `argus <base>`                 | Current branch vs an explicit base (e.g. a stacked feature branch like `feat/basket`)                                                    |
| `argus <branch> --base <base>` | A colleague's branch — `git fetch origin <branch>` first                                                                                 |
| `argus --staged`               | Staged changes only (`git diff --cached`)                                                                                                |
| `argus --post[=<PR#>]`         | After reviewing, post findings inline on the PR via `gh` (see [`references/posting.md`](references/posting.md)). Combine with any scope. |

**Depth default is light.** Use full for large refactors, new modules, payment/auth/security-sensitive changes, or when the user says "complet"/"full".

**Base resolution (in order):** explicit arg → `git symbolic-ref refs/remotes/origin/HEAD` (strip `origin/`) → `main` → `master` → `dev`. If none exists, ask the user. Stacked feature branches are common — when the user names a base, trust it over the default.

## Reviewer set per depth

| Depth           | Reviewers dispatched                                         |
| --------------- | ------------------------------------------------------------ |
| light (default) | quality · conventions · regression                           |
| full (`--full`) | quality · architecture · regression · security · conventions |

Gaps the classic 5-dimension split misses are **folded in**, not added as new agents (keeps the fan-out cheap). Each folded check is **capability-gated** — it only runs when the project actually has that capability (detected in step 3), so a non-i18n project is never flagged for "hardcoded text":

| Folded check                                                         | Owner        | Runs only if                                             |
| -------------------------------------------------------------------- | ------------ | -------------------------------------------------------- |
| i18n / hardcoded user-facing text / locale-unaware formatting        | conventions  | `i18n` detected (i18n lib or `messages/`·`locales/` dir) |
| Accessibility (alt, aria, headings)                                  | quality      | `frontend` detected (JSX/markup in changed files)        |
| React anti-patterns (`useEffect` misuse, stale closures)             | quality      | `react` detected                                         |
| Payment/financial security (Stripe order-state, webhook idempotency) | security     | `payments` detected (payment SDK / webhook code)         |
| Cross-package boundary checks                                        | architecture | `monorepo` detected                                      |
| Error-handling & edge-cases, performance                             | quality      | always (language-agnostic)                               |

Full per-reviewer methodology: [`references/dimensions.md`](references/dimensions.md). Capability detection: [`references/mechanical-checks.md`](references/mechanical-checks.md).

## Procedure

1. **Resolve scope** — depth, base, branch/staged, `--post`. Verify the branch exists; `git fetch origin <branch>` for remote branches.
2. **Pre-compute the diff once** and reuse it for every reviewer (avoids N× redundant `git diff`/re-reads):
   - File list: `git diff --stat <base>...<branch>` (or `git diff --cached --stat`)
   - Full patch: `git diff <base>...<branch>` (or `git diff --cached`). Save it to `/tmp/argus_diff.patch` so `--post` line-validation reuses it (never re-run `git diff` for posting).
   - **Strip ignored paths** before passing the diff (generated/lock/snapshot — see [`references/mechanical-checks.md`](references/mechanical-checks.md) ignore list). State what was dropped.
   - If the patch exceeds ~60k chars, trim per-file context to ±50 lines and flag the truncation to reviewers.
3. **Detect project capabilities** ([`references/mechanical-checks.md`](references/mechanical-checks.md) §Capability detection) — deterministically resolve which folded checks even apply: `i18n`, `frontend`/`a11y`, `react`, `monorepo`, `payments`. Compute once in the parent; pass the flags into every dispatch. **A reviewer must skip a sub-check whose capability is off** — flagging "hardcoded text" on a project with no i18n is a false positive, not a finding.
4. **Run the deterministic mechanical pre-pass** ([`references/mechanical-checks.md`](references/mechanical-checks.md)) — cheap grep/ripgrep over the diff for high-frequency, mechanically-detectable bans. This produces a **seed list** of candidate convention/security hits with `file:line`. Pass the seed list into the **conventions** reviewer's prompt as "pre-found candidates — verify each against the rule source, then extend." Deterministic recall on the highest-frequency category, zero extra agents.
5. **Dispatch reviewers in a single message** (true parallelism). For each, send a `general-purpose` subagent (the default — **never** a custom `pr-*-reviewer` type) whose prompt = the shared envelope + that dimension's full methodology block + the pre-computed diff + the active capability flags + the compact contract. Build prompts per [`references/dimensions.md`](references/dimensions.md) §Dispatch.
6. **Wait** for every reply before aggregating.
7. **Validate each reply** against [`references/contract.md`](references/contract.md) — parse JSON, check required fields + enums, recount findings vs `summary`. Mismatch → failure handling below.
8. **Aggregate** — merge sections, apply dedupe, compute per-section + global counts.
9. **Compute verdict + confidence** (rules below).
10. **Render** the report per [`references/report-format.md`](references/report-format.md).
11. **If `--post`** — post **one PR review with each finding anchored inline at `file:line`** per [`references/posting.md`](references/posting.md): default **all severities — critical, warning, and nits**, each anchored inline, concise verdict + counts in the review body. **Never** post the full report as a single `gh pr comment` issue blob (and never both). Confirm the target PR# first.

The parent never re-reads files or re-reviews code. Trust the structured replies.

## Verdict rules

First match wins:

- `blocking` — any `critical` finding in any section
- `needs-attention` — no critical, ≥ 1 `warning` in any section
- `pass` — no critical, no warning

Verdict goes in the report header, before the summary table.

## Confidence rules

- `high` — every dispatched reviewer returned `status: "ok"` and `coverage: "complete"`
- `medium` — exactly 1 reviewer is `partial` or `error`
- `low` — 2+ reviewers are `partial` or `error`

## Dedupe rules

Conservative. Collapse two findings **iff all** match: same `section`, same `file`, same `line` (or both omitted), same `severity`, normalized `title` equal (case-insensitive, trimmed). **Never** dedupe across sections. **Security findings never collapse**, even on a shared line.

## Failure handling

- Error reply → retry once, same prompt. Still failing → mark failure, list under "Subagent failures".
- Malformed/prose output → retry once with: "Previous reply was not valid JSON — emit the JSON object only, no prose, no fences." Still bad → coerce to `status: "error"` + failure note.
- Counts mismatch (`summary` ≠ recount of `findings`) → unreliable → mark failure.
- Timeout on a huge diff → re-dispatch the **failed reviewer only** with a narrower path scope; flag `coverage: partial`.
- Never silently drop a reviewer. A missing section is a bug; an empty section is signal — keep it with "No findings."

## Anti-noise

The mechanical pass and reviewers must **not** re-flag what the team has repeatedly judged non-issues: defensive type-guard / `.filter` narrowing, routine pagination edge-cases, autogenerated `components/ui/*` import order, generated files. Down-weight to `nit` or skip. Findings need a concrete `file:line` + evidence — no intuition-only flags.

## Gotchas

- **Reviewers share no state.** Each prompt must carry base, branch, mode, absolute repo path, the diff, and its full methodology block. Generic agents have no skill loaded — inline everything.
- **One message for all dispatches.** Sequential dispatch kills parallelism.
- **Never re-run `git diff` in a reviewer.** The inlined patch is authoritative; reviewers open files only for context outside the patch window.
- **Strip generated/snapshot/lock files before dispatch** — they are noise and inflate the diff. The user always asks to ignore `snapshot.json` & friends.
- **Default base may be `dev`, not `main`.** Detect via `origin/HEAD`. Stacked feature-branch bases are common here — honor an explicit base arg.
- **`--post` is inline-only.** One PR review (reviews API) with findings anchored at `file:line`; the review body is a short verdict+counts summary, not the rendered report. **Never** `gh pr comment` the full report as a single conversation blob, and never post inline _and_ a full-report comment — the lone blob is "not visual" and the user rejects it. `gh pr comment` is allowed only for a zero-finding `pass`. Validate each finding's line against the diff hunks before posting (see posting.md) so they actually anchor instead of folding into the body.
- **`--post` posts all severities — nits included.** The user wants nits in the comments too. Anchor nits inline at `file:line` like any other finding; mark them `[nit]` in the comment body so they read as low-priority. Only drop nits if the user explicitly asks for critical+warning only on a given run.
- **JSON-only replies.** Prose before/after the object is a failure — retry once, then mark failure.
- **No new dependencies.** If a reviewer recommends adding a library, surface it as a flag, do not act on it.

## What this skill deliberately does NOT depend on

- No external skills.
- No external contract file outside `argus/references/`.

Everything a reviewer needs is inlined at dispatch time. That is the whole point.
