---
name: argus-review
description: 'When asked to review a PR or branch ("review this PR", "PR review", "argus", before merging), fan the diff out to parallel read-only reviewers and return a severity-ranked verdict; optionally post inline via gh.'
---

# Argus — autonomous PR review

> Argus Panoptes, the hundred-eyed watchman. This skill fans the diff out to several independent reviewers at once, then judges what they saw.

**Self-contained by design.** Argus assumes nothing else is installed: it dispatches default `general-purpose` subagents; each reviewer gets its methodology by **reading files** inside `argus-review/references/` and the run's scratch dir (absolute paths carried in the prompt — never pasted content). A path costs one line as parent output; the reviewer reads it as cheap input tokens.

**Coordinator + read-only.** Argus never edits code and never reviews code itself in the parent. It dispatches, validates structured replies, aggregates a verdict, and (only when asked) posts findings to a PR.

Rules below marked "(incidents.md)" were distilled from real incidents logged in [`references/incidents.md`](references/incidents.md) — consult that file only when questioning or revising a rule, never during a normal run.

## When to use / not use

Use: "review this PR / branch", "review against `<base>`", "argus", self-review before opening or merging a PR, after a refactor.
Not: quick pass on uncommitted scratch work (review inline), debugging a failure, applying fixes (argus is read-only), repo-wide audits (every reviewer is diff-scoped).

## Invocation & scope

| Invocation                     | Meaning                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------- |
| `argus`                        | Current branch vs base — **light** (4 reviewers: quality, conventions, regression, logic) |
| `argus --full` (or "complet")  | Current branch vs base — **full** (6 reviewers + adversarial verifier)                    |
| `argus <base>`                 | Current branch vs an explicit base (e.g. a stacked feature branch)                        |
| `argus <branch> --base <base>` | A colleague's branch — `git fetch origin <branch>` first                                  |
| `argus --staged`               | Staged changes only (`git diff --cached`)                                                 |
| `argus --post[=<PR#>]`         | After reviewing, post findings inline on the PR via `gh` ([`references/posting.md`](references/posting.md)). Combine with any scope. |

**French prose aliases** (map, don't ask): "commente/poste sur la PR" → `--post`; "complet"/"full" → `--full`; "mode light" → light; "PR <N>" **combined with a posting phrase** → `--post=<N>` (a bare "review la PR 113" is a read-only review — never auto-post without posting intent). When `--post` has no number, auto-resolve it from the branch (`gh pr view <branch> --json number -q .number`) and announce it; ask only when no open PR exists or resolution is ambiguous.

**Depth default is light.** Use full for large refactors, new modules, payment/auth/security-sensitive changes, or on request.

**Base resolution (in order):** explicit arg → `git symbolic-ref refs/remotes/origin/HEAD` (strip `origin/`) → `main` → `master` → `dev`. If none exists, ask. Stacked bases are common — when the user names a base, trust it over the default.

## Reviewer set per depth

| Depth           | Reviewers dispatched                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------ |
| light (default) | quality · conventions · regression · logic                                                       |
| full (`--full`) | quality · architecture · regression · security · conventions · logic **+ adversarial verifier** |

**Full mode adds a verification pipeline** ([`references/verifier.md`](references/verifier.md)): as each reviewer's reply validates, its `warning`/`critical` findings are immediately dispatched to a verifier agent prompted to *refute* them, while the remaining reviewers still run. `intentional` findings are dropped, `unsourced` ones demoted to `nit`, before dedupe and verdict. Verifier failure is fail-open.

**Light mode verifies criticals only:** any `critical` that survives the severity-inflation guard is dispatched to the same verifier flow even in light mode — most light runs have zero, so the cost is marginal, and an unverified critical drives a `blocking` verdict (incidents.md §Spec-blind criticals). Warnings are never verified in light.

**`logic` is the business-logic reviewer** — it derives the *intent* of the change (PR description, linked PRD/Notion card, Figma mockups / screenshots, commit messages) and verifies the diff implements it: state transitions, calculations, role-based rules, front/back contract coherence, UI element/state coverage against the mockup.

Gaps the classic 5-dimension split misses are **folded into existing reviewers**, each **capability-gated** — it only runs when the project has that capability (detected in step 3):

| Folded check                                                          | Owner        | Runs only if                                             |
| --------------------------------------------------------------------- | ------------ | -------------------------------------------------------- |
| i18n / hardcoded user-facing text / locale-unaware formatting         | conventions  | `i18n` detected (i18n lib or `messages/`·`locales/` dir) |
| Accessibility (alt, aria, headings)                                   | quality      | `frontend` detected (JSX/markup in changed files)        |
| React anti-patterns (`useEffect` misuse, stale closures)              | quality      | `react` detected                                         |
| Payment/financial security (order-state, webhook idempotency)         | security     | `payments` detected                                      |
| Cross-package boundary checks                                         | architecture | `monorepo` detected                                      |
| Error-handling & edge-cases, performance                              | quality      | always                                                   |
| Transaction boundaries, background-job claim/lease, external-call amplification | quality | always                                              |
| Reuse against the existing tree (new-symbol seed, step 4)             | quality      | always                                                   |
| Removed-behavior blast radius (removed-line seed, step 4)             | regression   | always                                                   |
| Toolchain/build-config blast radius & version pinning                 | regression   | always                                                   |
| Access-loss dual check (who *loses* access, uniformity across guards) | security     | always                                                   |
| Recurrence guard + pre-existing-data/backfill on fix & migration PRs  | logic        | always                                                   |
| Zero-value wrappers/aliases around a primitive                        | quality      | always                                                   |
| File size (diff-grown >~400 → split; any changed file ≥~1000 lines → refactor candidate even if pre-existing; test files exempt from the ≥1000 tier) & inline-props-type extraction | quality | always (size); typed code (inline-type) |
| Library API best-practices (Zod, TanStack Query, Drizzle, …)          | quality      | lib detected in the stack manifest (step 3)              |
| ORM migration hygiene (hand-written migrations, snapshot drift)       | quality      | `drizzle` or `prisma` in the stack manifest              |

Per-reviewer methodology: [`references/dimensions.md`](references/dimensions.md). Capability detection: [`references/mechanical-checks.md`](references/mechanical-checks.md). Per-library checklists: [`references/library-practices.md`](references/library-practices.md).

## Procedure

1. **Resolve scope** — depth, base, branch/staged, `--post`. Verify the branch exists; `git fetch origin <branch>` for remote branches.
2. **Create the scratch dir, pre-compute the diff once to a file** — reviewers read the file; the parent never holds the patch (only the `--stat`):
   - `ARGUS_TMP=$(mktemp -d "${TMPDIR:-/tmp}/argus.XXXXXX")` — unique per run; echo the path and **carry it literally into every later command** (env doesn't persist across Bash calls).
   - File list: `git diff --stat <base>...<branch>` (or `--cached --stat`).
   - Full patch: `git diff <base>...<branch> > "$ARGUS_TMP/diff.patch"` — redirect straight to the file, never echo the patch.
   - **Strip ignored paths** (generated/lock/snapshot — exclude pathspecs per mechanical-checks.md ignore list). State what was dropped.
   - Patch > ~60k chars (`wc -c`) → trim per-file context to ±50 lines and flag the truncation to reviewers.
   - **Snapshot branch-side files when the reviewed branch is NOT the current HEAD** (remote branch, stacked base, kanban slot on another ref): `git diff --name-only <base>...<branch> | while IFS= read -r f; do mkdir -p "$ARGUS_TMP/branch/$(dirname "$f")" && git show "<branch>:$f" > "$ARGUS_TMP/branch/$f" 2>/dev/null || true; done` (deleted files just skip). Reviewers/verifiers `Read` these for context on changed files instead of running `git show <branch>:<path>` themselves. Branch checked out → skip and pass `Branch snapshots: none — working tree is on the reviewed branch` in every envelope.
3. **Detect capabilities + stack manifest** (mechanical-checks.md §Capability detection): `i18n`, `frontend`/`a11y`, `react`, `monorepo`, `payments`, plus `libs=…` from `package.json`. **Check the per-repo cache first** (mechanical-checks.md §Cache — keyed on the package manifests, stored in the common git dir): a hit replaces the whole detection with one command. Compute once; pass the flags into every dispatch. The quality reviewer reads library-practices.md itself. **A reviewer must skip a sub-check whose capability is off** — that flag would be a false positive, not a finding.
   **Gather intent sources** for `logic`: PR title+body (`gh pr view --json title,body`), linked PRD/Notion card, `git log <base>..<branch> --format='%s%n%b'`. Pass verbatim — the reviewer must not invent intent. (Full mode reuses the same sources in every verifier envelope — gather once.)
   **Resolve visual intent into text in the parent — never hand a raw image/Figma URL to a subagent** (text-only agents can't see it — incidents.md):
   - **Figma links** in the PR body → Figma MCP (`get_screenshot` + `get_design_context`/`get_metadata`), distill a **compact textual spec**: fields, labels, actions, visible states, explicit values/rules. MCP unavailable → record `"figma <url> — not rendered"`.
   - **Screenshots** → fetch (`gh api <url> > $ARGUS_TMP/shot-N.png`, then `Read`), distill the same spec. Unfetchable → `"screenshot <url> — not rendered"`.
   - Pass the specs as the **Mockup / screenshot spec** intent source. A `— not rendered` line MUST still be passed so the reviewer flags the gap instead of silently skipping.
4. **Run the mechanical pre-pass** (mechanical-checks.md) — cheap grep over the diff for mechanically-detectable bans → seed list of candidate hits with `file:line`, passed to the **conventions** reviewer as "pre-found candidates — verify each against the rule source, then extend." Also `wc -l` + `--numstat` the changed files → **file-size seed** (files ≥~400 lines total, with diff-added counts) passed to the **quality** reviewer (mechanical-checks.md §File-size count). Also extract added top-level symbols and grep the tree for existing equivalents → **new-symbol seed** to **quality** (§New-symbol seed — reuse is the top measured recall gap), and grep the patch's load-bearing removed lines (dropped props/guards/transactions/fallbacks) → **removed-behavior seed** to **regression** (§Removed-line seed).
5. **Dispatch all reviewers in a single message** (true parallelism). Each is a `general-purpose` subagent (never a custom `pr-*-reviewer` type) whose prompt = the dispatch envelope from dimensions.md: run-specific data only (scope, capability flags, `--stat`, seed list, intent sources) + **absolute paths** to `dimensions.md`, `contract.md`, `$ARGUS_TMP/diff.patch` (and `library-practices.md` for quality). **Never paste the diff, methodology, or contract into a prompt.**
6. **Collect replies; in full mode, verify in pipeline.** As each reply arrives: validate against [`references/contract.md`](references/contract.md) (parse JSON, required fields + enums, recount findings vs `summary`), then apply the severity-inflation guard (§Verdict rules). **Full:** remaining warnings/criticals → immediately dispatch one verifier per verifier.md (findings verbatim + intent sources + paths to `verifier.md` and the diff) without waiting for other reviewers. **Light:** remaining `critical` findings only → same verifier flow; warnings are not verified. Zero remaining eligible findings → no verifier. Nits are never verified.
7. **Wait** for every reviewer and verifier, apply verdicts (`real` → keep, `intentional` → drop, `unsourced` → demote to `nit`), recompute counts. Verifier failure after one retry → fail-open: keep findings, note "unverified".
8. **Aggregate** — merge sections, dedupe, per-section + global counts.
9. **Compute verdict + confidence** (below).
10. **Render** per [`references/report-format.md`](references/report-format.md).
11. **If `--post`** — first **dedupe against existing PR threads, all authors** (humans + prior argus runs — incidents.md) per posting.md §Dedupe. Then post **one PR review with each finding anchored inline at `file:line`**, all severities included, and the short English body of posting.md §Review body — exhaustive contents (verdict + counts + mandatory coverage line). **Set the review `event` from the verdict**: `REQUEST_CHANGES` on `blocking`/`needs-attention`, `COMMENT` on a nits-only `pass`, `APPROVE` on a zero-finding `pass`. Never post the report as a single comment blob. Announce the resolved PR#.
12. **Cleanup** — `rm -rf "$ARGUS_TMP"`, always, even on a failed/aborted review.

The parent never re-reads files or re-reviews code. Trust the structured replies.

## Verdict rules

First match wins: `blocking` — any `critical` · `needs-attention` — no critical, ≥1 `warning` · `pass` — neither. Verdict goes in the report header.

**Severity-inflation guard** (mechanical; apply to each reply as it validates in step 6, before any verifier dispatch): demote to `nit` any `warning`/`critical` that is confirmation-seeking ("confirm this is intended/intentional", "or confirm with design", "please verify"), a speculative edge-case with no plausible real input, a mockup-omission with no written requirement backing it (dimensions.md §logic item 7), or an intent-stated refactor change with no unhandled consequence (dimensions.md §Severity discipline). Reviewers keep leaking these at `warning` despite the prompt rule, so the parent enforces the cap mechanically (incidents.md §Severity inflation). Additionally **drop entirely** (not demote) any finding whose own evidence text argues against itself ("likely a non-issue in practice", "optional, low priority") and any finding the reply's `notes[]` or the verifier already refuted — a self-refuted finding posted anyway is pure noise (incidents.md §July 2026 retro). The drop list is literal, in either language: "not a defect", "not a bug" / "pas un bug", "the trigger is unproven", "may be unreachable" / "non atteignable", "latent", "pre-existing and untouched by this PR" / "préexiste" / "hérité de", "project-wide follow-up rather than something to change here", "maintainability preference, not a defect", "question rather than a finding", "not a privilege escalation", "accepted operational risk". **A question never occupies a finding slot** — it is dropped, or becomes one `Open questions:` line in the body (max 2 questions total) (incidents.md §Sept 2026 audit). Additionally, **cap at `warning` any `critical` whose demonstrated effect is only that code never executes or a shipped claim is vacuous** (dead rule, unreachable branch, no-op guard) — `critical` requires concrete damage (wrong output, crash, data loss, security), and spec-mandated dead code is a design question, not a blocker (incidents.md §Spec-blind criticals). The verdict must never read `needs-attention`/`blocking` off non-bugs.

## Confidence rules

`high` — every reviewer `status: "ok"` + `coverage: "complete"` · `medium` — exactly 1 `partial`/`error` · `low` — 2+.

## Dedupe rules

Conservative **within a section**. Collapse two findings **iff all** match: same `section`, `file`, `line` (or both omitted), `severity`, normalized `title` (case-insensitive, trimmed).

**Cross-section clustering (mandatory, on top of the above).** Two findings on the same `file` whose lines are equal or within ±25 with ≥50% title-token overlap are ONE finding, kept at the max severity, with `also flagged by: <sections>` recorded internally (never posted — posting.md §Deny-list). Consequences: never two comments on one `path:line`; never concatenate two reviewers' write-ups with a bare `---`; a multi-file pattern is ONE anchor plus "same pattern at X, Y" (max 2 named) or one file-level anchor per file, never a comment enumerating other files; a finding carried in the review body is never also posted inline. Security findings never collapse **only when the finding is an actual security claim** — a section-`security` finding about a11y, style, or maintainability collapses like any other (incidents.md §Sept 2026 audit).

**Re-runs.** Prior threads are fetched before posting (posting.md §Dedupe); open the body with `N previous findings resolved · M still open · K withdrawn`. Never open a new thread within ±10 lines of one of your own still-open threads — reply in it instead.

## Failure handling

- Error reply → retry once, same prompt. Still failing → mark failure, list under "Subagent failures".
- Malformed/prose output → retry once with "emit the JSON object only". Still bad → coerce to `status: "error"`.
- Counts mismatch (`summary` ≠ recount) → unreliable → mark failure.
- Timeout on a huge diff → re-dispatch the failed reviewer only, narrower path scope, `coverage: partial`.
- Never silently drop a reviewer. A missing section is a bug; an empty section is signal — keep it with "No findings."
- Verifier failure → retry once; still failing → **fail-open**: keep the findings, flag "unverified". Verifier failures never count against confidence.

## Anti-noise

Do **not** re-flag what the team has repeatedly judged non-issues: defensive type-guard / `.filter` narrowing, routine pagination edge-cases, autogenerated `components/ui/*` import order, generated files. Findings need a concrete `file:line` + evidence — no intuition-only flags.

**A repo rule is a line in the REVIEWED repo**, quoted as `path:line` (`AGENTS.md`, `CLAUDE.md`, `docs/*.md`, lint config). The operator's global `~/.claude/CLAUDE.md`, "the reviewer instructions", and session-level rules are **never** repo rules: never cite them, never enforce them, never let them raise a verdict (incidents.md §Operator config as repo rule). Convention/style findings cap at `nit` and never drive the verdict, except an explicit hard ban quoted at its `path:line` in the reviewed repo (dimensions.md §conventions).

Down-weight to `nit`-or-skip — FP clusters from real review data (incidents.md §FP clusters):
- intentional refactor changes matching the PR's stated intent (only their *unhandled consequences* are findings);
- static placeholder / seed / temporary data; type casts in test/mock files;
- hardcoded user-facing text on a localized project (never `critical`);
- confirmation-seeking or speculative-edge-case findings (a `nit` question at most — must not raise the verdict);
- extract-helper / dedup suggestions on small twins (≲30 lines, 2 occurrences);
- edge-cases the library already handles natively — check the lib's docs before flagging;
- an invariant borrowed from a sibling hook/component applied where the author deliberately diverged;
- a pattern the codebase already uses unchanged elsewhere — grep for sibling occurrences before flagging at warning+; if found, **drop it**: a project-wide follow-up is not a PR defect and never occupies a comment slot (incidents.md §Spec-blind criticals, §Sept 2026 audit);
- a test file ≥~1000 lines — long test files are fine, skip entirely (no `nit`).

## Gotchas

- **Scratch files live in a per-run `mktemp -d` dir, never at fixed `/tmp/argus_*` paths** — fixed paths get clobbered by concurrent runs. Repeat the literal path in each Bash call; `rm -rf` at the end.
- **Sandboxed slots (kanban) deny compound assignments like `VAR=$(mktemp -d …)`.** If a scratch-dir command is denied once, fall back immediately to `mkdir -p /tmp/argus-<pr-number-or-branch>` (unique per PR — kanban never runs the same PR in two slots) instead of retrying mktemp variants (~2 min lost fumbling per run on PR sofrapa#275).
- **Reviewers share no state.** Each prompt carries base, branch, mode, absolute repo path, and the literal absolute paths to `dimensions.md` / `contract.md` / `$ARGUS_TMP/diff.patch`. If a reviewer can't read a path, retry once with the content inlined (fallback only).
- **One message for all dispatches.** Sequential dispatch kills parallelism — observed drift: dispatches issued one per turn added ~100 s before the last reviewer even started (PR sofrapa#275). (Verifier dispatches are the exception by design: each fires as its reviewer returns — that IS the pipeline.)
- **The verifier sees warnings/criticals in full mode, criticals only in light mode.** Never nits, never findings the guard already demoted. Most runs dispatch 0–3 verifiers, not 6.
- **Verifier drops are reported, not silent** — per-section "filtered by verifier" count. Verdict and `--post` event come from the post-verification set.
- **Never re-run `git diff` (even file-scoped) or `git show <branch>:<path>` in a reviewer/verifier.** `$ARGUS_TMP/diff.patch` is authoritative; `$ARGUS_TMP/branch/<path>` carries the branch-side snapshot of every changed file when the branch isn't checked out — `Read` those. Working-tree reads/greps are for unchanged files only. The parent never echoes the patch either. (Observed drift on PR #318: dozens of per-file `git diff` and `git show | sed` calls from verifiers because only the monolithic patch existed and the slot worktree wasn't on the reviewed branch.)
- **Strip generated/snapshot/lock files before dispatch** — noise; the user always asks to ignore them.
- **Default base may be `dev`, not `main`.** Detect via `origin/HEAD`; honor an explicit base arg.
- **`--post` is inline-only.** One PR review with findings anchored at `file:line`; short verdict+counts body. Never a full-report `gh pr comment` blob, never both (incidents.md). A zero-finding `pass` is an `APPROVE` review (empty `comments[]`), not a comment. Validate each finding's line against the diff hunks before posting so they anchor.
- **`--post` sets the review state, not just comments** — `event` derived from the verdict, **recomputed from the FINAL posted set** (after dedupe drops and line-validation), never from the pre-posting report (incidents.md §Posting mechanics).
- **One batched review request; placeholder/probe/empty reviews are banned.** Never post comments one-by-one (each mints an empty review), never submit "in progress"/probe reviews, never submit a review with an empty body AND empty `comments[]`, and never submit a second review to change the state of the first — the `event` is computed once from the FINAL posted comments and never narrated in the body. Praise ("Good job !") and meta-narration ("revue reformulée", "findings reposted below") are banned as bodies; delete an accidental PENDING review before the run ends (incidents.md §Review event & timeline pollution; posting.md §Hard ban).
- **Reviewer `notes[]` are never findings** — "not rendered"/"could not verify" stay out of `findings[]`, counts, and PR comments; at most one `Unverified: …` line in report and body (incidents.md).
- **Endorsing another reviewer's claim = asserting it.** Co-signing a human/bot finding needs the same evidence bar as an own finding — verify against schema/docs first, or say nothing (incidents.md §Endorsing).
- **Never merge.** `APPROVE` only posts the review state — never `gh pr merge` (nor `--auto`). Merging stays a human action.
- **`--post` posts all severities — nits included**, anchored inline and marked `[nit]`. Only drop nits if the user explicitly asks.
- **Everything argus emits is English** — report, review body, verdict word, counts, severity words, every comment — regardless of the repo's, the PR's, the CLAUDE.md/AGENTS.md's or a reviewer's language. Repo/UI strings are quoted verbatim in backticks; `« »` only inside such a verbatim quote; domain nouns use the code identifier (`league`, not "the ligue"). posting.md §Language runs the mechanical check before posting (incidents.md §Sept 2026 audit).
- **JSON-only replies.** Prose around the object is a failure — retry once, then mark failure.
- **No new dependencies.** A reviewer recommending a library is surfaced as a flag, not acted on.
- **`logic` findings need a cited intent source** — quote the PR description / PRD / mockup spec / commit line contradicted, or name the violated invariant with the sibling `file:line`. No source → hallucination → drop. No intent sources at all → internal-consistency checks only + note in `notes[]`.
- **Visual intent must be rendered to text in the parent** (step 3), never handed to a subagent as a URL (incidents.md §Visual intent). The reviewer checks **functional** fidelity (elements/states/rules), not pixel layout.
- **Lib-behavior claims need a doc citation** (context7 lookup, passage quoted) or downgrade to question/nit (incidents.md §Unsourced claims). Checks are version-aware: unsure whether an API is current → query context7 rather than flag from memory.
- **The user's next message after a report is often "corrige ce qui est pertinent".** Argus stays read-only — the fix is a separate step; don't pre-emptively edit.
- **Positive assertions carry the finding evidence bar.** No "verified as delivered / checks out / clean" claim without the backing `file:line` checks — the July 2026 retro's worst misses all sat in areas the summary had certified clean (report-format.md §What NOT to include). The coverage line (per-dir file/finding counts, scoped from the file list, never the PR title) is the honest substitute.
- **The review is a snapshot — say so, and check for drift when posting.** Record the reviewed HEAD sha in the report; on `--post`, if the branch tip has moved past the reviewed sha, say which commits are unreviewed and offer a targeted re-run instead of silently posting against a stale tree (two of the July 2026 retro's escaped bugs landed in post-review commits merged minutes later).
- **Suggested fixes carry the same evidence bar as findings.** A remediation recommended in a finding must be verified against the actual code (the API supports it — e.g. never suggest wrapping service calls in a DB transaction without checking the service accepts a tx client) and against the stated spec/decided business rules (never propose behavior a PRD or recorded decision forbids). Unverifiable → phrase the fix as a question or state the problem without a fix; a wrong remediation costs more than none (incidents.md §Spec-blind criticals).

Everything a reviewer needs lives in `argus-review/references/` and the run's scratch dir, reachable by path from every dispatch. No external skills, no external contract files.
