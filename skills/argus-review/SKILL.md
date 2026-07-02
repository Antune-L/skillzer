---
name: argus-review
description: 'When asked to review a PR or branch ("review this PR", "PR review", "argus", before merging), fan the diff out to parallel read-only reviewers and return a severity-ranked verdict; optionally post inline via gh.'
---

# Argus — autonomous PR review

> Argus Panoptes, the hundred-eyed watchman who never fully sleeps. This skill is the hundred eyes: it fans the diff out to several independent reviewers at once, then judges what they saw.

**Self-contained by design.** Unlike a dependency-coupled orchestrator, Argus assumes **nothing else is installed** — no companion skills, no custom `pr-*-reviewer` agent types. It dispatches the **default `general-purpose` subagent** and inlines each reviewer's complete methodology into its prompt. Drop the `argus-review/` folder into any agent setup and it works.

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
| `argus`                        | Current branch vs base — **light** (4 reviewers: quality, conventions, regression, logic)                                               |
| `argus --full` (or "complet")  | Current branch vs base — **full** (6 reviewers)                                                                                          |
| `argus <base>`                 | Current branch vs an explicit base (e.g. a stacked feature branch like `feat/basket`)                                                    |
| `argus <branch> --base <base>` | A colleague's branch — `git fetch origin <branch>` first                                                                                 |
| `argus --staged`               | Staged changes only (`git diff --cached`)                                                                                                |
| `argus --post[=<PR#>]`         | After reviewing, post findings inline on the PR via `gh` (see [`references/posting.md`](references/posting.md)). Combine with any scope. |

**French prose aliases** (the user invokes in French — map, don't ask): "commente/commentaire direct(ement) sur la PR", "met les commentaires sur la PR", "poste sur la PR" → `--post`; "complet"/"full" → `--full`; "mode light" → light; "PR <N>" **combined with a posting phrase** → `--post=<N>` (a bare "review la PR 113" is a read-only review of that PR's branch — never auto-post without posting intent). When `--post` has no number, **auto-resolve it from the branch** (`gh pr view <branch> --json number -q .number`) and announce the resolved PR# — only ask when no open PR exists or resolution is ambiguous.

**Depth default is light.** Use full for large refactors, new modules, payment/auth/security-sensitive changes, or when the user says "complet"/"full".

**Base resolution (in order):** explicit arg → `git symbolic-ref refs/remotes/origin/HEAD` (strip `origin/`) → `main` → `master` → `dev`. If none exists, ask the user. Stacked feature branches are common — when the user names a base, trust it over the default.

## Reviewer set per depth

| Depth           | Reviewers dispatched                                                  |
| --------------- | --------------------------------------------------------------------- |
| light (default) | quality · conventions · regression · logic                            |
| full (`--full`) | quality · architecture · regression · security · conventions · logic  |

**`logic` is the business-logic reviewer** — it derives the *intent* of the change (PR description, linked PRD/Notion card, **Figma mockups / screenshots**, commit messages) and verifies the diff actually implements it: state transitions, calculations, role-based rules, front/back contract coherence, and UI element/state coverage against the mockup. No other dimension owns "does the code do what the feature wants?".

Gaps the classic 5-dimension split misses are **folded in**, not added as new agents (keeps the fan-out cheap). Each folded check is **capability-gated** — it only runs when the project actually has that capability (detected in step 3), so a non-i18n project is never flagged for "hardcoded text":

| Folded check                                                         | Owner        | Runs only if                                             |
| -------------------------------------------------------------------- | ------------ | -------------------------------------------------------- |
| i18n / hardcoded user-facing text / locale-unaware formatting        | conventions  | `i18n` detected (i18n lib or `messages/`·`locales/` dir) |
| Accessibility (alt, aria, headings)                                  | quality      | `frontend` detected (JSX/markup in changed files)        |
| React anti-patterns (`useEffect` misuse, stale closures)             | quality      | `react` detected                                         |
| Payment/financial security (Stripe order-state, webhook idempotency) | security     | `payments` detected (payment SDK / webhook code)         |
| Cross-package boundary checks                                        | architecture | `monorepo` detected                                      |
| Error-handling & edge-cases, performance                             | quality      | always (language-agnostic)                               |
| Zero-value wrappers/aliases around a primitive (no added behavior)   | quality      | always (language-agnostic)                               |
| File size (>~400 lines → split) & inline-props-type extraction       | quality      | always (size); typed code (inline-type)                  |
| Library API best-practices (Zod, TanStack Query, Drizzle, …)         | quality      | lib detected in the stack manifest (step 3)              |

Full per-reviewer methodology: [`references/dimensions.md`](references/dimensions.md). Capability detection: [`references/mechanical-checks.md`](references/mechanical-checks.md). Per-library checklists: [`references/library-practices.md`](references/library-practices.md).

## Procedure

1. **Resolve scope** — depth, base, branch/staged, `--post`. Verify the branch exists; `git fetch origin <branch>` for remote branches.
2. **Create the run's scratch dir, then pre-compute the diff once** and reuse it for every reviewer (avoids N× redundant `git diff`/re-reads):
   - `ARGUS_TMP=$(mktemp -d "${TMPDIR:-/tmp}/argus.XXXXXX")` — unique per run so concurrent reviews never clobber each other. Echo the path and **carry it literally into every later command** (env vars don't persist across Bash calls).
   - File list: `git diff --stat <base>...<branch>` (or `git diff --cached --stat`)
   - Full patch: `git diff <base>...<branch>` (or `git diff --cached`). Save it to `$ARGUS_TMP/diff.patch` so `--post` line-validation reuses it (never re-run `git diff` for posting).
   - **Strip ignored paths** before passing the diff (generated/lock/snapshot — see [`references/mechanical-checks.md`](references/mechanical-checks.md) ignore list). State what was dropped.
   - If the patch exceeds ~60k chars, trim per-file context to ±50 lines and flag the truncation to reviewers.
3. **Detect project capabilities + stack manifest** ([`references/mechanical-checks.md`](references/mechanical-checks.md) §Capability detection) — deterministically resolve which folded checks even apply: `i18n`, `frontend`/`a11y`, `react`, `monorepo`, `payments`, plus the **stack manifest** (`libs=zod@4,tanstack-query,drizzle,…` from `package.json` deps). Compute once in the parent; pass the flags into every dispatch. For each detected lib, paste its checklist from [`references/library-practices.md`](references/library-practices.md) into the **quality** reviewer's envelope. **A reviewer must skip a sub-check whose capability is off** — flagging "hardcoded text" on a project with no i18n is a false positive, not a finding.
   Also **gather the intent sources** for the `logic` reviewer: PR title+description (`gh pr view --json title,body` when a PR exists), the linked PRD/Notion card if the PR body references one, and `git log <base>..<branch> --format='%s%n%b'`. Pass them verbatim in the logic envelope — the reviewer must not invent intent.
   **Resolve visual intent into text in the parent — never hand a raw image/Figma URL to a subagent** (reviewers are text-only `general-purpose` agents; a URL is invisible to them):
   - **Figma mockups** — extract every `figma.com/…?node-id=…` link from the PR body. For each, load the Figma MCP via ToolSearch (`mcp__figma__get_screenshot` + `mcp__figma__get_design_context`/`get_metadata`) and distill a **compact textual spec**: the screen's fields, labels, actions/buttons, visible states, and any explicit values/rules — not a pixel description. If the Figma MCP is unavailable (headless/cron, not connected), record `"figma <url> — not rendered"`.
   - **Screenshots** — extract attachment image URLs (`user-attachments`, `githubusercontent`, `![]()`) from the PR body. Fetch each (`gh api <url> > $ARGUS_TMP/shot-N.png` — auth carries for `user-attachments` — then `Read` it) and distill the same compact spec. If a URL can't be fetched/rendered, record `"screenshot <url> — not rendered"`.
   - Pass the distilled specs as the **Mockup / screenshot spec** intent source. A visual source that exists but couldn't be rendered MUST be passed as a `— not rendered` line so the reviewer flags the gap instead of silently skipping it.
4. **Run the deterministic mechanical pre-pass** ([`references/mechanical-checks.md`](references/mechanical-checks.md)) — cheap grep/ripgrep over the diff for high-frequency, mechanically-detectable bans. This produces a **seed list** of candidate convention/security hits with `file:line`. Pass the seed list into the **conventions** reviewer's prompt as "pre-found candidates — verify each against the rule source, then extend." Deterministic recall on the highest-frequency category, zero extra agents.
5. **Dispatch reviewers in a single message** (true parallelism). For each, send a `general-purpose` subagent (the default — **never** a custom `pr-*-reviewer` type) whose prompt = the shared envelope + that dimension's full methodology block + the pre-computed diff + the active capability flags + the compact contract. Build prompts per [`references/dimensions.md`](references/dimensions.md) §Dispatch.
6. **Wait** for every reply before aggregating.
7. **Validate each reply** against [`references/contract.md`](references/contract.md) — parse JSON, check required fields + enums, recount findings vs `summary`. Mismatch → failure handling below.
8. **Aggregate** — merge sections, apply dedupe, compute per-section + global counts.
9. **Compute verdict + confidence** (rules below).
10. **Render** the report per [`references/report-format.md`](references/report-format.md).
11. **If `--post`** — **first dedupe against existing PR threads (all authors — humans + prior argus runs)** per [`references/posting.md`](references/posting.md) §Dedupe; never repost a point a human or an earlier run already made (real incident: fftir/sofrapa argus runs 2–3× per PR → sofrapa #112 "pk tu répètes"). Then post **one PR review with each finding anchored inline at `file:line`**: default **all severities — critical, warning, and nits**, each anchored inline, concise verdict + counts in the review body. **Set the review `event` from the verdict** — `REQUEST_CHANGES` on `blocking`/`needs-attention`, `COMMENT` on a nits-only `pass`, `APPROVE` on a zero-finding `pass` (clean PR → green-lit) (see posting.md §Review event). **Never** post the full report as a single `gh pr comment` issue blob (and never both). Auto-resolve the target PR# from the branch and announce it ("posting to PR #113"); ask only if no open PR or ambiguous.
12. **Cleanup** — `rm -rf "$ARGUS_TMP"` once the report is rendered (and posted, if `--post`). Always runs, even on a failed/aborted review.

The parent never re-reads files or re-reviews code. Trust the structured replies.

## Verdict rules

First match wins:

- `blocking` — any `critical` finding in any section
- `needs-attention` — no critical, ≥ 1 `warning` in any section
- `pass` — no critical, no warning

Verdict goes in the report header, before the summary table.

**Severity-inflation guard (mechanical, apply at aggregation before computing the verdict):** demote to `nit` any `warning`/`critical` whose evidence or recommendation reduces to confirmation-seeking — text matching "confirm this is intended/intentional", "or confirm with design", "please verify/confirm" — a speculative edge-case with no plausible real input, a mockup-omission with no written requirement backing it (dimensions.md §logic item 7), or an intent-stated refactor change with no unhandled consequence (see [`references/dimensions.md`](references/dimensions.md) §Severity discipline). Reviewers keep leaking these at `warning` despite the prompt rule, so the parent enforces the cap mechanically (real leaks post-fftir #260: sofrapa #186 "Confirm this is intentional" warning, sofrapa #174 "confirm this script cannot run against a production database", fftir #328's three "…or confirm with design" warnings, fftir #327's warning reverted as "fix: rollback slop feedback"). The verdict must never read `needs-attention`/`blocking` off non-bugs.

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

Also down-weight to `nit`-or-skip (FP clusters from real review data): intentional refactor changes matching the PR's stated intent (only their *unhandled consequences* are findings — sofrapa #117), static placeholder / seed / temporary data, type casts in test/mock files, and hardcoded user-facing text on a localized project (never `critical` — sofrapa #112). A finding that only asks "confirm this is intended" or rests on a speculative edge-case is a `nit` question at most — it must not raise the verdict (fftir #260).

Newer FP clusters (2026-07 audit) — same treatment: **extract-helper / dedup suggestions on small twins** (≲30 lines, 2 occurrences) are repeatedly dismissed "not worth" / "no biggie" / "false" (fftir #311/#312) — skip or `nit`; **edge-cases the library already handles natively** (e.g. TanStack Table's empty/default column handling) — check the lib's docs before flagging (fftir #311); **an invariant borrowed from a sibling hook/component and applied to a context where the author deliberately diverged** (fftir #327 — warning implemented then reverted as "fix: rollback slop feedback").

## Gotchas

- **Scratch files live in a per-run `mktemp -d` dir, never at fixed `/tmp/argus_*` paths.** Fixed paths get clobbered by concurrent reviews (two argus runs at once → one review validates lines against the other's diff). Create `$ARGUS_TMP` in step 2, repeat the literal path in each Bash call (env doesn't persist), `rm -rf` it at the end of the run.
- **Reviewers share no state.** Each prompt must carry base, branch, mode, absolute repo path, the diff, and its full methodology block. Generic agents have no skill loaded — inline everything.
- **One message for all dispatches.** Sequential dispatch kills parallelism.
- **Never re-run `git diff` in a reviewer.** The inlined patch is authoritative; reviewers open files only for context outside the patch window.
- **Strip generated/snapshot/lock files before dispatch** — they are noise and inflate the diff. The user always asks to ignore `snapshot.json` & friends.
- **Default base may be `dev`, not `main`.** Detect via `origin/HEAD`. Stacked feature-branch bases are common here — honor an explicit base arg.
- **`--post` is inline-only.** One PR review (reviews API) with findings anchored at `file:line`; the review body is a short verdict+counts summary, not the rendered report. **Never** `gh pr comment` the full report as a single conversation blob, and never post inline _and_ a full-report comment — the lone blob is "not visual" and the user rejects it. A zero-finding `pass` is an `APPROVE` review (reviews API, empty `comments[]`), **not** `gh pr comment`. Validate each finding's line against the diff hunks before posting (see posting.md) so they actually anchor instead of folding into the body.
- **`--post` sets the review state, not just comments.** Once all comments are uploaded the review is submitted with `event` derived from the verdict — `REQUEST_CHANGES` on blocking/needs-attention, `COMMENT` on a nits-only pass, `APPROVE` on a zero-finding pass. Argus no longer defaults to a neutral `COMMENT` for everything; the PR's GitHub review state must reflect the outcome (posting.md §Review event). **The verdict feeding the event is recomputed from the FINAL posted set** — after dedupe drops and line-validation — never from the pre-posting report (real incidents: sofrapa #185 `REQUEST_CHANGES` with only nits actually posted; fftir #310 warnings under `COMMENT`).
- **One batched review request; placeholder/probe reviews are banned.** Never post comments one-by-one (each mints an empty review — sofrapa #183: 13 timeline entries for one run) and never submit "in progress" / permission-probe reviews (fftir #325/#326); delete an accidental PENDING review before the run ends (posting.md §Hard ban).
- **Reviewer `notes[]` are never findings.** "Not rendered" / "could not verify" entries stay out of `findings[]`, out of every counts table, and off the PR as comments — at most one `Unverified: …` line in the report and review body (sofrapa #183/#184 counted them as nits).
- **Endorsing another reviewer's claim = asserting it.** Ranking or co-signing a human/bot finding in the review body needs the same evidence bar as an own finding — verify against the schema/docs first, or say nothing (fftir #317: gemini's null-safety FP promoted to "higher-priority"; the Prisma relation was `required`).
- **Never merge.** `APPROVE` only posts the review state — Argus must not run `gh pr merge` (nor `--auto`, nor enable auto-merge). Approving a clean PR is the most Argus does; merging stays a human action.
- **`--post` posts all severities — nits included.** The user wants nits in the comments too. Anchor nits inline at `file:line` like any other finding; mark them `[nit]` in the comment body so they read as low-priority. Only drop nits if the user explicitly asks for critical+warning only on a given run.
- **JSON-only replies.** Prose before/after the object is a failure — retry once, then mark failure.
- **No new dependencies.** If a reviewer recommends adding a library, surface it as a flag, do not act on it.
- **`logic` findings need a cited intent source.** Every logic finding quotes the PR description / PRD / mockup spec / commit line it contradicts, or names the violated invariant with the sibling `file:line` that establishes it. "The feature probably should…" without a source is a hallucination — drop it. When no intent source exists (no PR body, no PRD), the reviewer limits itself to internal-consistency checks and notes the missing intent in `notes[]`.
- **Visual intent must be rendered to text in the parent, not handed to a subagent as a URL.** A Figma `node-id` link or a `user-attachments` screenshot URL passed raw is invisible to a text-only reviewer (real gap: across 16 recent PRs the logic reviewer never opened a single Figma/screenshot, and punted "confirm against the Figma" on fftir #282 instead of checking it). Step 3 resolves Figma links via the Figma MCP and downloads PR screenshots, distills each to a compact textual spec (fields/labels/actions/states), and passes it as the mockup/screenshot intent source. The reviewer checks **functional** fidelity (which elements/states/rules exist), not pixel/layout fidelity. If a source can't be rendered, it is passed as `— not rendered` so the reviewer flags the unverified gap instead of silently skipping.
- **Lib-behavior claims need a doc citation.** A critical/warning whose proof lives in a third-party lib's semantics (not in repo code) must cite the lib's docs (context7 lookup, passage quoted in the finding) or be downgraded to a question/nit. Empirical basis: the only 2 dismissed criticals across ~113 posted findings were both unsourced better-auth claims (sofrapa #101 "slop", #117 "CF la doc de better-auth").
- **Library checks are version-aware.** The checklist in `library-practices.md` is the baseline; when unsure whether an API is current for the detected version, the reviewer queries the context7 MCP rather than flagging from memory — a stale-version flag is a false positive.
- **The user's next message after a report is often "corrige ce qui est pertinent".** Argus stays read-only — the fix is a separate step, offered by the report footer. Don't pre-emptively edit.

## What this skill deliberately does NOT depend on

- No external skills.
- No external contract file outside `argus-review/references/`.

Everything a reviewer needs is inlined at dispatch time. That is the whole point.
