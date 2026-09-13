# Incident log — real-world failures behind the rules

Each SKILL.md rule marked "(incidents.md)" was distilled from one of these. This file is the
evidence base; it is NOT loaded during a normal run. Consult it only when questioning or
revising a rule, or when adding a new incident.

Format: `incident → rule it produced`.

## Subagents bypassing the pre-computed diff (PR #318, Aug 2026)

- **Reviewing origin/feat/global-feedback from a kanban slot worktree checked out on another
  ref**, verifiers/reviewers issued dozens of per-file `git diff base...branch -- <file>` and
  `git show <branch>:<file> | sed` calls: the monolithic `diff.patch` was awkward to consult
  per-file, and no branch-side file content was readable via `Read` since the working tree
  wasn't on the reviewed branch.
  → Step 2 snapshots every changed file at the branch tip into `$ARGUS_TMP/branch/<path>`
  whenever the reviewed branch is not the current HEAD; envelopes forbid file-scoped
  `git diff` and `git show <branch>:<path>` and point at the snapshot dir instead.

## Duplicate posting

- **sofrapa #112 "pk tu répètes"** — argus ran 2–3× on the same PR (pattern also seen across
  fftir/sofrapa) and reposted points humans or earlier runs had already made.
  → `--post` must dedupe against ALL existing PR threads (humans + prior argus runs) before posting.

## Severity inflation (confirmation-seeking findings raised the verdict)

- **fftir #260** — confirmation-seeking warnings raised the verdict; the user rejected the review.
- **sofrapa #186** — "Confirm this is intentional" posted as a `warning`.
- **sofrapa #174** — "confirm this script cannot run against a production database" as `warning`.
- **fftir #328** — three "…or confirm with design" warnings in one review.
- **fftir #327** — a warning was implemented, then reverted by the author as "fix: rollback slop
  feedback": the finding borrowed an invariant from a sibling hook and applied it where the author
  had deliberately diverged.
  → Mechanical severity-inflation guard: demote confirmation-seeking / speculative / unbacked-mockup
  / intent-stated-refactor findings to `nit` in the parent, before any verifier dispatch.

## Unsourced library-behavior claims

- **sofrapa #101 ("slop") and #117 ("CF la doc de better-auth")** — the only 2 dismissed criticals
  across ~113 posted findings; both were unsourced claims about better-auth semantics.
  → A critical/warning whose proof lives in a third-party lib must cite the lib's docs (context7)
  or be downgraded to a question/nit.

## False-positive clusters (down-weight to nit-or-skip)

- **sofrapa #117** — intentional refactor changes matching the PR's stated intent flagged as issues;
  only their *unhandled consequences* are findings.
- **fftir #311 / #312** — extract-helper / dedup suggestions on small twins (≲30 lines,
  2 occurrences) repeatedly dismissed "not worth" / "no biggie" / "false".
- **fftir #311** — edge-case flagged that TanStack Table already handles natively; check the lib's
  docs before flagging.
- **fftir #327** — sibling-invariant transplanted to a context where the author deliberately
  diverged (see above, reverted as slop).

## Posting mechanics

- **sofrapa #183** — comments posted one-by-one minted 13 timeline entries for a single run.
  → One batched review request; placeholder/probe reviews banned.
- **fftir #325 / #326** — "in progress" / permission-probe reviews submitted.
  → Never submit probe reviews; delete an accidental PENDING review before the run ends.
- **sofrapa #185** — `REQUEST_CHANGES` submitted while only nits were actually posted (dedupe +
  line-validation had dropped the warnings).
- **fftir #310** — warnings posted under a neutral `COMMENT` event.
  → The review `event` is recomputed from the FINAL posted set, never from the pre-posting report.
- **sofrapa #183 / #184** — reviewer `notes[]` ("not rendered", "could not verify") counted and
  posted as nits.
  → `notes[]` never become findings, counts, or PR comments.

## Endorsing others' claims

- **fftir #317** — gemini-code-assist's null-safety false positive was promoted to
  "higher-priority" in the review body; the Prisma relation was in fact `required`.
  → Ranking/co-signing another reviewer's finding requires the same evidence bar as an own finding.

## Visual intent ignored

- **fftir #282 + audit of 16 PRs** — the logic reviewer never opened a single Figma link or
  screenshot, and punted "confirm against the Figma" instead of checking it (a raw URL is invisible
  to a text-only subagent).
  → The parent resolves Figma/screenshots to a compact textual spec before dispatch; unrenderable
  sources are passed as `— not rendered` lines.

## User-rejected report formats

- The lone `gh pr comment` full-report blob was rejected as "not visual".
  → `--post` is inline-only; the review body is a short verdict + counts.

## Spec-blind criticals & wrong remediations (fftir #356, cross-checked by a 2-agent counter-review)

- **fftir #356 purge rule** — a purge `deleteMany` on `status = LICENSEE_REQUEST` was flagged
  `[critical]` as "can never delete an app-created row". Factually right (dead code), but the rule
  was **mandated verbatim by the feature's PRD** (FR-4 table), which even carried an open question
  flagging the exact doubt; effect was inexecution, not damage. Right call: spec question, ≤ warning.
  → Dead-code / vacuous-claim findings cap at `warning`; before flagging implemented behavior as
  wrong, check whether a PRD/plan line mandates it and cite it.
- **fftir #356 suggested fixes, both wrong** — the same review recommended (a) "purge `EMITTED`
  rows past `expirationDate` instead", contradicting the decided business rule (expired avis stay
  visible as "Périmé"), and (b) "wrap the 5 `setValue` calls in a transaction", inapplicable because
  the service uses the module-level prisma client and accepts no tx client.
  → Suggested remediations carry the same evidence bar as findings: verify implementability against
  the actual code and coherence with decided rules, or phrase as a question / omit.
- **fftir #356 unreachable failure path** — the `[warning]` claimed a mid-sequence Zod re-check
  could throw; the contract input schemas ARE the same registry schema objects the service
  re-parses, so the throw was unreachable for that route. A verifier would likely have caught it,
  but the run was light (no verifier on warnings) and criticals had no verifier either.
  → Mid-sequence-failure claims must name a reachable trigger; `critical` findings get a targeted
  verifier even in light mode.
- **fftir #356 pre-existing pattern** — the flagged multi-`setValue` pattern already existed
  unchanged in two sibling controllers (`email-settings`, `external-links`); the PR followed the
  project idiom rather than introducing it.
  → Grep for unchanged sibling occurrences before flagging a pattern at warning+; note them and
  frame as a project-wide follow-up, not a PR defect.

## July 2026 retro (audit of 20 reviews — sofrapa #271–#291, fftir #446–#479)

Outcome of ~114 inline findings traced one by one + 12 escaped bugs traced from staging-fix PRs
back to their reviewed introducing PRs. Headline: precision was fine (>80% TP, ~0 factual
refutations on sofrapa), recall was the failure mode. Clusters → rules produced:

- **Reuse under-detection (~30 verified misses vs ~6 found)** — detection only fired on
  near-verbatim copies; structural equivalents (`useSeedOnDialogOpen`, `claimDue`, `assertSameSet`,
  `LoadingState`, `useAppForm`, official Klaviyo SDK vs hand-rolled fetch) shipped unflagged; a
  5-copy validator family flagged on #280 grew to 6 copies on #281 with no re-flag; the review's
  own "local component" advice created a cross-app `FullPageStatus` duplicate on #291.
  → New-symbol seed (mechanical-checks.md), behavior-not-name search of canonical shared dirs
  (dimensions.md §quality item 1), extraction target must name the shared home, verifier carve-out
  for evidence-backed clone findings.
- **Removed lines unread** — fftir #465 dropped `onFileReject` + locked it out via `Omit` while the
  summary certified "prior semantics preserved"; fftir #446 removed the legacy
  `status: VALID` fallback; sofrapa #277 lost a `withTransaction`; sofrapa #275 bypassed a 422
  DoS guard. → Removed-line seed + regression item 5.
- **"Right file, wrong dimension"** — in 5 of the 12 escaped bugs the review commented the exact
  defective line as a style/duplication nit (fftir #446 seeder vs partial unique index → broke
  seeding, fixed #452; fftir #398 scope constant → licensees invisible to everyone, fixed #478;
  sofrapa #174 `tecdoc-client.ts` `as const` nit on the function showing every vehicle the same
  photo). → Same-predicate re-sweep rule; jobs/transaction/amplification checks in quality.
- **Question-form findings: ~0% dialogue yield** — zero written answers across sofrapa; on fftir
  4 of 5 refuted by a check the reviewer could run (writers of `state: DONE`, `@db.Date` column
  type, single consumer of a response). Self-refuted findings posted anyway (sofrapa #274 nit 8
  "likely a non-issue" — the only finding never touched; fftir #470 nit 3 published after its own
  verifier refuted the premise). → Resolve-before-asking rule; drop self-refuted findings in the
  parent guard.
- **"Verified clean" was the least reliable output** — the three worst misses sat inside areas the
  summary certified: "locale typing … check out" (#280, `locale` made optional for every mail),
  "no silent-failure path left" (#469), TecDoc images "verified clean" (#291, 1→N×2 amplification).
  → Positive assertions carry the finding evidence bar; per-dir coverage line replaces clean bills.
- **Verifier bad drops, invisible** — #271 valid 5th-copy pagination finding dropped as "matches an
  existing pattern"; #275 ×360 rate-limit widening across 60+ routes dropped as "a rate-limit
  relaxation … intended" with no magnitudes; 6 demoted warnings on #291 all fixed anyway.
  → Verifier carve-outs (clones, magnitudes) + per-drop reasons in the report.
- **Severity anchored to shape, not blast radius** — a cast = "critical" (#271) while a
  user-visible donut double-count = nit-question (fftir #446, fixed 1h41 later); same `formatTo*`
  rule nit on #472, warning on #479. → Quality severity floor (user-visible wrong output never
  `nit`); LOC findings capped and axis-required.
- **Snapshot blindness** — sofrapa #291: a 23-file commit landed 2h11 after the review snapshot,
  9 min before merge, carrying 2 defects + 3 duplications; #280's oil-category bug landed 32h
  post-review. → Record reviewed sha; on `--post`, surface unreviewed commits.
- **Toolchain discount** — fftir #431 (compiler swap) passed 0/0/1 → 4-day silent email outage;
  sofrapa #260 "config-only" → unpinned `eas-cli`. → Regression item 6.
- **Missing dual questions** — security reviewed leaks, never lockouts (fftir #398 "no leak" was
  true and beside the point; sofrapa #281 gated 3 of 5 macros); bugfix PRs never asked "is
  recurrence prevented?" (fftir #469, author added `assert-no-tsx.mjs` himself); migrations never
  checked against pre-existing rows (sofrapa #276 unsubscribe no-op). → Security both-polarities
  check; logic items 8–10.

## Operator config as repo rule (Sept 2026)

- **fftir #697–#719 audit (20 PRs, 28 author replies: 23 rejections)** — the single biggest FP
  cluster (10 of the 23 rejections): findings asserted that "the applicable repository instruction /
  the reviewer instructions prohibit code comments except TODO/FIXME/NOTE". That rule lives in the
  **operator's** `~/.claude/CLAUDE.md`, not in the repo: `AGENTS.md:23` says only "No obvious
  comments", and the repo carries ~97 backend JSDoc blocks and ~930 explanatory comments in
  `apps/web`. It was re-posted on 8 PRs and rated `critical` on #710, making a 14-line PR blocking;
  the author degraded from full rebuttals to "Not obvious" ×4.
  → A convention finding must quote its rule as `path:line` from the reviewed repo; operator/global/
  session instructions are never repo rules; grep-count a style pattern before flagging it;
  convention/style findings cap at `nit` unless they quote an explicit in-repo hard ban.

## Review event & timeline pollution (Sept 2026)

- **12 of 27 reviews carried the wrong event, both directions** — warnings and "blocking" verdicts
  submitted as `COMMENTED` (fftir #697/#698/#702/#710, sofrapa #442/#462), with the body narrating
  it ("posted as a comment, not an approval or change request" on #442; "Review event is COMMENT
  only" on #712 r2); and empty placeholder reviews used to flip the state afterwards (#714/#715
  empty `CHANGES_REQUESTED`, #710 empty `APPROVED`). #715 additionally got a "Good job !" review and
  a "Revue reformulée — …" meta review: 3 timeline entries for one run.
  → The event is computed from the FINAL posted `comments[]` and never narrated; empty reviews,
  second state-flipping reviews, praise bodies and meta-narration bodies are banned; `APPROVE`
  always carries a one-line body.

## Sept 2026 audit — language, internal-report leakage, dedupe, self-refuting findings

- **French / franglais in 12 of 20 PRs** — fully French comment bodies (#715, 24 comments), French
  guillemets wrapping English text (#697/#698/#712: « must also hold VIEW_FINIADA_REPORT »), French
  domain nouns where the code says `league`/`president` (#707), French headers.
  → English-only for every emitted string, mechanically checked before posting (posting.md §Language).
- **The posted body was the internal report** — "What was verified as safe" (#462), a
  `| Claim | Why it died |` table of dropped warnings (#707), fan-out leaks ("6/6 reviewers ok",
  "Demoted to a nit by verification", `<sub>Raised independently by …</sub>` footers), and test
  claims ("bun typecheck passes… 105 pass / 0 fail") argus never ran. #710's review touched only a
  JSDoc and said nothing about the 3 locale files in the same diff.
  → Fixed body contents + mechanical deny-list; the coverage line is mandatory (posting.md).
- **Dedupe failures** — the same defect posted 3× (#714 :61/:73), 4× on one anchor (#461
  `stripe.mapper.ts:352`), 4× at two severities (#461 `useSyncExternalStore`), the same JSDoc at
  :487 and :488 (#711), two reviewers' write-ups concatenated with a bare `---` in 8 comments
  (#715), one finding posted in the body *and* inline (#698), one comment enumerating 6 other files
  (#714/#718). #712's security section posted an a11y finding at `major` while its own summary said
  "non-sécurité".
  → Cross-section clustering (same file, ±25 lines, ≥50% title-token overlap), one comment per
  `path:line`, no `---` merges, security no-collapse only for actual security claims (SKILL.md §Dedupe).
- **Self-refuting and question findings still posted** — 8 of the 28 author replies just paraphrase
  argus's own last paragraph: "Not a defect", "the trigger is unproven", "may be unreachable",
  "project-wide follow-up rather than something to change here", "Maintainability preference, not a
  defect", "Question rather than a finding", "Was landing it in `packages/migration` deliberate?",
  "latent", "pre-existing and untouched by this PR", "not a privilege escalation", "accepted
  operational risk".
  → Literal drop list in the severity-inflation guard (both languages); questions never occupy a
  finding slot.
- **Fixes the repo forbids** — #715 recommended a type assertion `docs/TYPESCRIPT.md` forbids; four
  findings asked for tests on repos whose AGENTS.md forbids unrequested tests, one while quoting the
  ban in its own evidence; #715:22 recommended undoing a required option whose benefit the finding
  itself described.
  → Recommendations are checked against the repo's hard bans before being written; the verifier
  refutes a finding whose fix violates a repo doc.
- **PR description and prior rounds ignored** — #701 claimed the description said `validityDuration`
  is cleared while it said the opposite; #715:285 flagged as scope creep two lines requested in an
  earlier review round; #712 r2 ignored 3 rejections from r1 48 min earlier; the TODO/FIXME rule
  refuted on #711 at 14:16 was re-posted on #719 at 14:34.
  → Quote the contradicted sentence verbatim; check existing threads before a scope finding;
  re-runs read human replies and never re-post a refuted finding.
- **Reference reviews that got it right:** sofrapa #451 and fftir #701 (its non-description parts).
