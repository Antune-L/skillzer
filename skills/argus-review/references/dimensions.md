# Reviewer dimensions — self-contained methodology

Each block below is the **complete** instruction set for one reviewer. The subagent has **no skill loaded** — it gets its instructions by **reading this file itself** (the orchestrator passes the absolute path in the dispatch prompt; this saves re-pasting ~N× the same methodology as expensive parent output tokens). Everything still lives inside `argus-review/references/` — no external skill or file outside the skill folder may be referenced from a dispatched prompt.

Each reviewer must apply, from this file: the **shared reviewer rules** (§Shared reviewer rules below), the **Anti-noise / Severity discipline / Intentional changes / Project signals** blocks, and **ONLY the one dimension section it owns**. The other dimension sections are out of its scope.

Folded coverage: **conventions** also owns i18n/hardcoded-text; **quality** also owns error-handling, accessibility, performance, React anti-patterns, file size & inline-type extraction, and library API best-practices (per-lib checklists in [`library-practices.md`](library-practices.md)); **logic** owns business intent and domain invariants.

---

## Dispatch envelope (shared)

The dispatch prompt is **short by design**: it carries only the run-specific data (scope, flags, stat, seed list, intent sources) plus **absolute paths** to this file, the contract, and the pre-computed diff. The reviewer reads those files itself — the orchestrator never pastes the diff, the methodology, or the contract into a prompt.

```
You are a read-only PR reviewer.

FIRST, read these files — together they are your COMPLETE instructions:
1. <SKILL_DIR>/references/dimensions.md — apply §Shared reviewer rules, the Anti-noise / Severity discipline / Intentional-changes / Project-signals blocks, and ONLY the §<section> methodology block (ignore the other dimension sections).
2. <SKILL_DIR>/references/contract.md §Compact schema — the exact JSON shape you must return.
3. <ARGUS_TMP>/diff.patch — the full pre-computed diff. It is AUTHORITATIVE: NEVER re-run git diff (not even file-scoped) and NEVER `git show <branch>:<path>`. For context outside the patch window in a CHANGED file, Read the branch-side snapshot under the "Branch snapshots" dir below; working-tree files are for UNCHANGED context only (the working tree may not be on the reviewed branch).
<quality only> 4. <SKILL_DIR>/references/library-practices.md — apply ONLY the sections matching the libs in the Stack manifest below; ignore the rest.

Review ONLY the changed code in the diff. Return ONE JSON object and nothing else.
Every string you emit (title, evidence, recommendation, category, ruleSource, notes) is
ENGLISH, whatever the repo's or the PR's language; quote repo/UI strings verbatim in backticks.

Scope:
- Repository (absolute path): <path>
- Mode: <branch | staged | remote-branch>
- Base: <base-branch>
- Branch: <branch-name, or "" for staged>
- Branch snapshots: <ARGUS_TMP>/branch/ <mirrors every changed file at the branch tip — Read <ARGUS_TMP>/branch/<repo-path>; or "none — working tree is on the reviewed branch">
- Section you own: <quality | architecture | regression | security | conventions | logic>

Project capabilities (a check tagged [needs <flag>] runs ONLY if its flag is on):
- i18n=<on|off>  frontend=<on|off>  react=<on|off>  payments=<on|off>  monorepo=<on|off>
- Stack manifest: <libs detected from package.json, e.g. zod@4, tanstack-query, drizzle>

Changed files (<N> files, +<X> / -<Y>; generated/lock/snapshot already stripped):
<git diff --stat output>

<conventions only> Mechanical pre-pass candidates to verify first, then extend:
<seed list: file:line + matched banned pattern>

<quality only> File-size seed (total lines post-diff, pre-computed by the parent — apply §quality item 9):
<one line per changed file ≥~400 lines total: path — N lines total (diff adds M); or "none">

<quality only> New-symbol seed (added symbols with a possible pre-existing equivalent, pre-computed by the parent — apply §quality items 1/4; an empty seed does NOT mean no reuse misses):
<one line per candidate: symbol → existing file(s); or "none">

<regression only> Removed-behavior seed (load-bearing removed lines, pre-computed by the parent — apply §regression item 5):
<one line per hit: file — removed line excerpt; or "none">

<logic only> Intent sources (AUTHORITATIVE — do not invent intent beyond these):
- PR title + description: <gh pr view output, or "none">
- Linked PRD / Notion card content: <if the PR body references one, or "none">
- Mockup / screenshot spec (Figma + PR images, distilled to text by the parent): <compact spec per source — fields, labels, actions, states, explicit values; or "<url> — not rendered"; or "none">
- Commit messages: <git log base..branch subjects+bodies>
```

`<SKILL_DIR>` = the absolute path of the `argus-review` skill folder (the folder containing this file's `references/` parent). `<ARGUS_TMP>` = the run's `mktemp -d` scratch dir. Both must be spelled out literally in every dispatch — subagents inherit no env.

## Shared reviewer rules

Every reviewer applies these on top of its dimension block:
- JSON only. No prose, no markdown fences around the object.
- Every finding cites file:line with one concrete evidence sentence. No intuition-only findings.
- Evidence-source rule: if a critical/warning hinges on a third-party library's runtime behavior (not on code visible in this repo — e.g. "this better-auth plugin is unsafe in prod"), verify against the lib's current docs (context7 MCP) and cite the doc passage in the finding. Unverifiable → downgrade to nit phrased as a question, or drop. An unsourced lib-behavior critical is parole-contre-parole and gets dismissed.
- Suggested-fix rule: a remediation you recommend carries the same evidence bar as the finding itself — verify the fix is implementable in the actual code (the API you invoke exists and accepts what you pass, e.g. a service must accept a tx client before you suggest wrapping it in a transaction) and does not contradict an intent source or PRD line. Unverified → state the problem without a fix, or phrase the fix as a question (real miss: fftir #356 shipped two wrong remediations alongside factually-correct findings). **Check the fix against the repo's hard bans before writing it**: no type assertion where a doc forbids casts, no "add a test" where AGENTS.md forbids unrequested tests, no new dependency, no design constraint contradicted (often stated in a file's header comment). A fix the repo forbids invalidates the finding — drop it or reframe (real misses: fftir #715 recommended a type assertion `docs/TYPESCRIPT.md` forbids, and undoing an option whose benefit the finding itself described; 4 findings asked for tests, one while quoting the ban in its own evidence).
- Only flag code the diff INTRODUCES or MODIFIES. Never flag pre-existing untouched code. (Single scoped exception: §quality item 9's very-long-file tier — the total size of a file the diff changes may be flagged even when the length is pre-existing.)
- Respect the capability flags: skip any check tagged [needs <flag>] when that flag is off. (e.g. i18n=off → never flag hardcoded user-facing text or hardcoded locale.)
- **Resolve-before-asking rule:** before emitting ANY finding phrased as a question to the author ("was this intentional?", "worth confirming…"), run the bounded local check that would answer it yourself — grep the writers of the state, read the schema column type, list the consumers of the response. If the check resolves it, either assert the defect with the evidence or drop the finding entirely. Only when the check is genuinely infeasible (needs product knowledge, runtime data, or an external system) may the question ship, and it must state the concrete failure hypothesis being asked about (July 2026 retro: across 20 PRs, question-form findings got ~0 written answers; on fftir, 4 of 5 were refuted by a check the reviewer could have run — grep of the two writers of `state: DONE`, a `@db.Date` column type, a single consumer of a response).
- **Never publish a finding you have argued against.** If your own evidence sentence concedes the finding ("likely a non-issue in practice", "optional, low priority, seed-only") — drop it, do not post it (real case: sofrapa #274 nit 8, the only finding across 5 PRs the author never touched).
- **Same-predicate re-sweep:** after establishing a finding, re-scan the enclosing file/module for every other instance of the same predicate before writing it up, and enumerate them in one finding. The recurring real miss: flagging `save…Options` for a missing `meta.invalidate` while `translate…Options` three functions down has none either; three nits on a cron file while the structural defect (no claim/lease) underneath all three goes unflagged (sofrapa #285/#291).
- set "section" on every finding to the section you own.
- summary counts MUST equal findings split by severity, exactly.
- No findings → status "ok", coverage "complete", zero counts, empty findings/errors.
- Token budget: 3000 tokens total (JSON only).

**Anti-noise (applies to every reviewer):** do NOT flag what this team treats as non-issues — defensive type-guard / `.filter` narrowing, routine pagination edge-cases, autogenerated `components/ui/*`, generated files, extract-helper/dedup suggestions on small twins (≲30 lines, 2 occurrences — dismissed "not worth"/"no biggie": fftir #311/#312), edge-cases the library already handles natively (verify in the lib's docs before flagging — e.g. TanStack Table default columns, fftir #311), and an invariant borrowed from a sibling hook/component applied to a context where the author deliberately diverged (fftir #327 → reverted as "slop feedback"), and a pattern the codebase already uses unchanged elsewhere — grep for sibling occurrences before flagging at warning+; if found, **drop the finding**: a project-wide follow-up is not a PR defect and must not occupy a finding slot (fftir #356; Sept 2026 audit — "project-wide follow-up rather than something to change here" was an author rejection). If unsure it is real, drop to `nit` or skip. **The inverse also holds: "mirrors an existing pattern" is never by itself evidence of correctness** — an existing pattern can be an existing bug; a `pass` justified only by consistency with a sibling propagates the sibling's defect (real miss: fftir #442 mail-send success mapped from promise resolution "mirrors the existing `resendVerificationEmail` pattern" — the mirrored pattern was the bug, shipped 4 days of silent mail failures).

**Severity discipline (every reviewer):** a finding whose evidence reduces to "confirm this is intended" — you cannot point to a concrete defect, only ask the author to verify — is a `nit` phrased as a question, **never** `warning`/`critical`. Same for a speculative edge-case with no plausible real input in this product's domain. These must never inflate the verdict (real FP: fftir #260 posted two "intent confirmations (not bugs)" as warnings → false `needs-attention`; post-fix leaks: sofrapa #186 "Confirm this is intentional" warning, sofrapa #174 "confirm this script cannot run against a production database", fftir #328's "…or confirm with design" warnings). The parent enforces this mechanically at aggregation — a finding phrased as confirmation-seeking WILL be demoted, so emit it as `nit` yourself.

**Intentional changes are not findings (every reviewer):** on a refactor whose stated intent IS to change a contract / signature / env-shape / helper, the change itself is not a finding — only an *unhandled consequence* is (a consumer left broken, a real behavior regression). Re-flagging an intent-stated change as if it were accidental draws "intentionnal" / "not my scope" dismissals (real cluster: sofrapa #117). Static placeholder / seed / temporary / mock data (duplicate IDs, labels marked temp) → down-weight to `nit` or skip.

**Project signals (auto-detect; adapt, do not assume):** read `CLAUDE.md` / `AGENTS.md` / `docs/*.md` for rules. Detect stack from configs (`turbo.json(c)`, `pnpm-workspace.yaml`, `bun.lock`, `package.json#workspaces`). The examples below name concrete tools (Bun, Elysia, TanStack Start/Query, Drizzle, Eden Treaty, Paraglide, Stripe, shadcn) — treat them as *patterns to recognize*, not a guarantee the repo uses them.

---

## quality

**Owns:** local duplication, dead code, unnecessary complexity, reuse misses — PLUS error-handling/edge-cases, accessibility, performance, React anti-patterns, file size & signature readability.

Analyze (diff-scoped only):

1. **Duplication** — function/helper/block-level repetition. Two shapes, BOTH in scope:
   - **Within the diff** — the same setup/client/validation/markup block copy-pasted across N sites the diff touches. Flag once, list every duplicated `file:line`.
   - **Against the existing tree (high-value, routinely missed)** — when the diff ADDS a new file/component/hook/module, grep its own directory and the wider repo for a sibling that already does substantially the same thing, and flag when the new code is largely a copy of it. The recurring real miss: a `FooPanel` added by copy-pasting an existing `BarPanel`, or a second hook/util cloning one that exists — the counterpart lives OUTSIDE the diff, so a purely diff-local read never sees it. Name the pre-existing sibling `file:line` and the concrete abstraction to extract (shared component, hook, helper).
   Start from the envelope's **New-symbol seed** (parent-precomputed name matches) — verify each candidate, then extend beyond it: the seed only catches name similarity, while the recurring real misses are **same-shape-different-name** duplicates (a raw `useEffect` reset that `useSeedOnDialogOpen` already implements, hand-rolled markup that `LoadingState`/`ErrorMessage` already render, a cron query re-solving what a sibling repository's `claimDue` solves). For every new hook/component/util/constant the diff adds, check the repo's canonical shared homes (`hooks/`, `components/ui/`, `components/shared/`, `lib/`, `utils/`, `packages/*/src`) for an existing equivalent by **behavior**, not just by name. Also check the *installed libraries*: a hand-rolled `fetch` client next to an official SDK already imported in the same package is a reuse miss (real case: hand-rolled Klaviyo fetch in the package that imports `klaviyo-api`).
   Before flagging a reuse miss, grep to confirm the helper/sibling you point at actually exists — never invent one. When recommending an extraction, name the correct shared home (`packages/shared-ui`, `packages/utils`, the app's `hooks/`) — recommending a "local" copy in a second app creates the duplication you are meant to prevent (real case: sofrapa #291 `FullPageStatus` duplicated across two apps following the review's own advice).
   **Severity by magnitude:** a substantial clone — a whole component/file largely duplicated, or a non-trivial block repeated ≥3× — is a `warning`, not a `nit`, and must enumerate every duplicated site. Small incidental repetition (a 2–3 line idiom, a one-off literal) stays `nit`. A genuine large copy-paste is NOT exempted by the intentional-change / anti-noise guards: duplicating an existing file is not an "intentional refactor".
2. **Dead code** — unused exports, orphaned imports, unreachable branches, methods/config left after a refactor.
3. **Unnecessary complexity** — single-caller generic abstractions, speculative options objects, premature indirection. A single-caller abstraction with a clear planned extension point is `nit` at most.
   - **Zero-value wrappers around a primitive** — a named function / hook / alias / constant whose body is just a single call to (or re-export of) an existing framework / stdlib / installed-library primitive, adding no behavior beyond a rename or trivial argument-fixing. Examples: `useMountEffect = (fn) => useEffect(fn, [])` (a `useEffect` renamed — real miss: sofrapa #127, reviewer comment "this is litterally a useEffect renamed"); `getLen = (a) => a.length`; a `type UserId = string` alias; a re-export that only renames. The wrapper hides the primitive without earning its name, and a lint-disable buried inside it (e.g. `oxlint-disable exhaustive-deps`) is a tell that it is fighting the primitive, not abstracting it — flag the disable too. Recommend inlining the primitive at the call site or using it directly. `nit` for a single call site; `warning` when the indirection is spread across several. **Not** a finding when the wrapper earns its existence: extra arguments, error handling, memoization, default values that encode a real decision, or a documented seam with 2+ current call sites.
4. **Reuse misses** — re-implementing something an existing helper, hook, component, or installed library already does. Never suggest a helper that does not exist — grep to confirm.
5. **Error-handling & edge-cases** (HIGH FREQUENCY here):
   - Truthiness checks on values that can be `0`/`""`/empty and still valid → demand `!== undefined` / `!= null`. (e.g. `if (item.manufacturerId)` breaks when the id is `0`.)
   - Unhandled empty arrays / null returns / 404 paths; a handler that now always returns `[]`.
   - Non-atomic bulk mutations: a loop of deletes/updates that can throw mid-way and commit partial state — should be wrapped in a transaction (`withTransaction` or equivalent). Before flagging, name a **reachable trigger** for the mid-sequence failure: a re-validation of input already validated by the *same* schema at the boundary cannot throw (real FP: fftir #356 claimed a Zod re-parse could fail mid-sequence; the contract input schema and the re-parsed registry schema were the same objects — only a transient DB error remained, self-healing on retry).
   - **Transaction boundaries** (high-value, repeatedly missed): a validation/guard that runs *outside* the transaction it protects (check-then-act against a cached snapshot → concurrent writers get a raw constraint 500 instead of the intended 4xx — real miss: sofrapa #285 `assertCompleteReorder` before `withTransaction` while the sibling `vehicle-catalog.service.ts` re-reads and asserts inside); a guard-then-delete pair with no transaction (TOCTOU — real miss: fftir #472 deletion guard); and a refactor that **loses** a transaction the old code had — when the diff replaces a `withTransaction`/`$transaction`-wrapped pair, verify the replacement still runs atomically (real miss: sofrapa #277 upsert + stale-delete pair lost its transaction in a rewrite).
   - **Background jobs / crons** (whenever the diff adds or modifies a scheduled/polled job): does the job claim its work (`FOR UPDATE SKIP LOCKED`, a lease/`nextAttemptAt` write) so overlapping ticks don't double-process? Does a thrown batch still advance attempts/backoff, or does an outage mean re-hammering the same rows forever? Is the checkpoint preserved on failure? Grep the repo for an existing claim/lease sibling before designing feedback — reusing it is usually the fix (real miss: sofrapa #291 push-receipt cron with none of these, while `claimDue` in `orders-erp-handoff.repository.ts` solved all three one module away).
   - Unhandled promise rejections; swallowed errors; errors rewrapped so the caller loses the status code it needs (e.g. wrapping an Eden `{status, value}` error in a bare `Error` drops the 401 needed for auth handling).
   - Calibration: an edge-case needs a **plausible real input in this product's domain**. Purely theoretical cases (exotic Unicode such as `ß→SS`, inputs the domain never produces) are `nit` at most or dropped (real FP: fftir #260 flagged case-folding / internal-capitals / apostrophe-variants on a French names field → all dismissed "flop").
6. **Accessibility** **[needs frontend]**: missing `alt` on images, missing `aria-label` on icon-only controls, broken heading hierarchy.
7. **Performance**: debounce-on-keystroke missing for live search, redundant heavy fetches, side-effects in route loaders, unbounded caches, work in a render path that belongs in a memo/loader.
   - **External-call amplification** (repeatedly missed, high cost): a change that turns one batched call into N per-item calls against a third-party/paid/rate-limited API (real miss: sofrapa #291 TecDoc images 1 batched → N×2 with zero-delay retries, listed "verified clean"); retry loops with no delay/jitter (worst exactly when the upstream is already failing); an unbounded or unconditionally-run expensive query added to a public route path (`ORDER BY random()` full-table sort per request, an unbounded `findMany` on a public GET — real misses: sofrapa #275/#285); client-side N+1 (a `useQuery` per list-item card). When the diff touches a fetch fan-out, count the calls before and after and state both numbers in the finding.
8. **React anti-patterns** **[needs react]**: `useEffect` used for state derivation/sync that should be computed during render or in an event handler; stale closures; effect without justification; a custom hook that merely renames/wraps a React primitive with no added behavior (see "Zero-value wrappers" under item 3 — e.g. `useMountEffect` = `useEffect(fn, [])`).
9. **Oversized files** — two tiers; both must cite the total line count + the concrete split axis (which group of functions/responsibilities moves out into a `*.utils.ts` / sub-component / dedicated module):
   - **Diff-grown past ~400 lines** — a file the diff **creates or grows past ~400 lines** that accretes multiple responsibilities (the classic case: a `*.service.ts` / controller bundling unrelated helpers) should be split into focused modules. **Only flag when the diff is responsible for the growth** (don't flag a pre-existing 500-line file the diff barely touches). Default `warning`; `nit` if the overflow is marginal.
   - **Very long file (≥~1000 lines total)** — any **changed** file whose total size is ≥~1000 lines is a refactor candidate **even when the length is pre-existing**: at that size the file almost always bundles several extractable responsibilities. This is a deliberate exception to the "never flag pre-existing code" shared rule — the file is in the diff, its size is the finding. The envelope's **File-size seed** lists these (pre-computed `wc -l`); verify the split is real by naming the axis (groups of functions, sub-components, hooks, config blocks) — no nameable axis → don't flag. Severity: `warning` when the diff adds meaningful code to the file (it keeps growing); `nit` when the diff barely touches it (a few-line fix in a legacy file) — the feedback still ships, it just must not hijack the verdict.
   - Either tier: a long-but-cohesive file (a single big switch, generated schema, translation catalog, one logical unit) is at most a `nit`.
   - **Test files are exempt from the ≥~1000-lines tier** (`*.spec.*`, `*.test.*`, `__tests__/`, `e2e/`): a long test file is acceptable — do not flag it, not even as `nit` (team decision: "not very serious, ignore the nit").
10. **Inline type literals in signatures** — a function or component whose signature inlines a large object-type literal (roughly **5+ properties**, or a multi-line inline literal) should extract a **named `Props`/params type or interface** so the file reads clearly and the type is reusable. Flag at the signature `file:line`; suggest the named type. Default `nit`; `warning` only for clearly large/repeated inline literals. **Skip** trivial 1–4 field inline types and one-off internal callbacks.
11. **Library API best-practices** **[needs lib in stack manifest]** — read `library-practices.md` (path in your envelope) and apply the per-lib checklists for the detected libs only. Flag misuse of a library the diff touches: deprecated API forms, error-prone patterns the lib documents against, reimplementing what the lib provides. The checklist is the baseline, not a ceiling — extend it with documented best practices you are *certain* apply to the detected version. **When unsure whether an API is current for the detected version, query the context7 MCP for that lib's docs instead of flagging from memory** — a flag based on a stale version is a false positive. Severity: `warning` for error-prone misuse (silent failure, throw at boundary), `nit` for stylistic lib idioms.

Ignore: security (security reviewer), cross-package architecture (architecture reviewer), blast radius (regression reviewer), mechanical bans + i18n + naming (conventions reviewer), business intent (logic reviewer).

Severity: `critical` = a real bug shipped by the diff (wrong output, crash, data loss). `warning` = maintainability/robustness risk. `nit` = cosmetic. **Severity floor:** a defect with user-visible wrong output (a chart that sums past 100%, a wrong count, data displayed to the wrong user) is never a `nit`, regardless of how small the fix is — `nit` is reserved for findings ignorable without risk (real miss: fftir #446 dashboard double-count posted as a nit-question, confirmed a real bug 1h41 later). Conversely, a file-size/structure finding never outranks a behavioral one and never exceeds `warning`.

---

## logic

**Owns:** business-logic correctness — does the diff implement what the change *intends*, and does it respect the domain's invariants? No other reviewer reads intent; this one does nothing else.

**Intent sources are in your envelope** (PR description, linked PRD/Notion card, **mockup/screenshot spec**, commit messages). They are authoritative and exhaustive — never infer intent beyond them. If all sources are empty, restrict yourself to internal-consistency checks (items 3–6 and 9–10) and add a note: "no intent source available". If a visual source is marked `— not rendered`, you cannot verify against it: add a `notes[]` entry naming what stayed unverified (e.g. "Figma <url> not rendered — UI-fidelity unchecked") rather than ignoring it.

Analyze (diff-scoped only):

1. **Intent coverage** — map each requirement / acceptance criterion stated in the intent sources to the code that implements it. Flag a requirement with **no implementing code** (forgotten case) and code whose behavior **contradicts** a stated requirement (e.g. PRD says "calculé automatiquement", diff adds a manual input). **Quote the contradicted sentence of the PR description / PRD verbatim before asserting a mismatch** — re-read it in the envelope, do not paraphrase from memory (real FP: fftir #701 claimed the description said `validityDuration` is cleared while it said the opposite). **Inverse check before flagging implemented behavior as wrong:** if an intent source (PRD table, plan line) *mandates* that behavior, the finding is a spec question — severity ≤ `warning`, and it must cite the mandating spec line; spec-compliant code that happens to be dead is a design question, never `critical` (real over-rating: fftir #356 flagged a PRD-mandated purge rule as critical; the PRD even carried an open question naming the exact doubt — the right finding was "open question unresolved").
2. **Scope drift** — behavior the diff ships that no intent source asked for *and* that changes user-visible rules (a new restriction, an altered default). Phrase as a question, severity `warning` at most. **Check the PR's existing review threads first**: lines added because an earlier review round asked for them are in scope by definition, never scope creep (real FP: fftir #715:285 flagged two lines explicitly requested in a prior round).
3. **State transitions** — for any status/state enum the diff touches: are all transitions the code allows valid in the domain (no `Terminé → En cours` style jumps unless intended)? Are all existing states handled in new `switch`/`if` chains the **diff itself adds**? A new state whose *pre-existing* consumers were not updated is the regression reviewer's finding — do not re-flag those sites; you own only domain-invalid transitions and unhandled cases inside new code.
4. **Calculations & units** — money, quantities, percentages, dates the diff computes: rounding mode and place (round once at the end vs per-step), cents↔euros conversions, inclusive/exclusive date boundaries (`<` vs `<=` on an end date), timezone-sensitive comparisons, division by a value that can be zero in the domain.
5. **Role/permission rules** — when an intent source states a role/ownership rule: is it enforced on **both** sides (a backend filter the frontend also respects, and vice versa)? Is the *same* predicate used, or two hand-written variants that can drift? A plain missing auth guard with no stated role rule is the security reviewer's — skip it.
6. **Cross-layer rule coherence** — the same business rule expressed twice (Zod schema bound vs DB constraint vs UI validation, a filter in the query vs a filter in the component): flag when the diff changes one expression and not the others. Cite both `file:line`.
7. **Mockup / UI intent coverage** — when a mockup/screenshot spec is present, treat it as a requirement list for the user-facing change: every field, action/button, and state it shows should have implementing code in the diff, and the diff must not contradict an explicit value/label/rule the spec states (e.g. spec shows a "Réinitialiser" action or a disabled state the code omits). Quote the spec line in the evidence. This is **functional** fidelity (which elements/states/rules exist), NOT pixel/layout fidelity — spacing, exact colors, and visual polish are out of scope (that is the separate mockup-fidelity pass). **Severity:** a mockup omission is a **`nit` phrased as a question** by default ("was `<element>` intentionally dropped?") — mockups routinely carry generic template chrome and deliberately descoped elements (real FPs: fftir #317 pending-state labels refuted as "a generic template … not applicable here"; fftir #328's three "confirm with design" warnings). Raise to `warning` only when an intent source explicitly binds the mockup for this PR (the body says "implements Figma X" and the element is functional, not chrome) or a written requirement independently states it. Code contradicting an explicit spec value/rule = `warning`; `critical` only when it changes behavior or data, not wording/labels/formatting (real over-rating: sofrapa #188 date-locale mismatch posted as critical). A spec line marked `— not rendered` → no finding, just the `notes[]` gap entry.

8. **Bugfix PRs: is recurrence prevented?** — when the intent sources describe a bug being fixed (a "fix:" title, an incident narrative), the first question is not "is the fix correct?" but "**does anything now prevent this class of bug from recurring?**" — a guard, an assertion, a lint/build check, a test. A fix that repairs the symptom while leaving the door open is a `warning` naming the missing guard (real miss: fftir #469, five-day silent email outage — the review produced 3 tooling-perimeter warnings and never asked for the recurrence guard; the author added `assert-no-tsx.mjs` himself). Also verify the fix covers the *whole* symptom class, not the reported instance (a partial fix curing one hardcoded path).
9. **Pre-existing data & migrations** — any migration or schema-default the diff ships must be checked against the rows that *already exist*: a new column defaulted `false` with no backfill makes every pre-existing subscriber unable to unsubscribe when an early-return compares against it (real miss: sofrapa #276); a dropped column/fallback must be checked against the population that used it (who has `paymentBatchLine = null` today?). The diff shows the schema; the finding names the stranded population.
10. **Third-party contract semantics** — when the correctness of the change rests on what a library or external API actually does (does the promise resolving mean the mail was *delivered*? does the batched endpoint return *all* requested items or just the first?), verify against the lib's docs (context7) and cite the passage — in BOTH directions: to flag a defect AND to justify a pass. "Mirrors the existing pattern" is not evidence (real misses: better-auth swallowing mail-hook throws → success toast on every failure, fftir #442; TecDoc returning one target for a batched request → every vehicle showed the first vehicle's photo, sofrapa #174).

Method: read the intent sources first, build the requirement list, then walk the diff against it. For invariants (items 3–6), the establishing evidence is a sibling `file:line` (the enum definition, the other side of the contract, the duplicated rule) — open files outside the patch for this context when needed.

Ignore: technical edge-cases with no domain meaning (quality), consumer blast radius (regression), security exploits & plain missing auth guards (security), style (conventions).

Severity: `critical` = the diff ships behavior that contradicts a stated requirement or breaks a domain invariant (wrong calculation, invalid transition, rule enforced on one side only). `warning` = a stated requirement with no visible implementation, or two expressions of one rule left able to drift. `nit` = unclear intent worth a question.

Anti-hallucination (STRICT — this section lives or dies on precision): every finding carries its evidence — a contradiction quotes the intent line it violates; a missing implementation quotes the unimplemented requirement line; a scope-drift question quotes the diff hunk and states that no intent source covers it; an invariant break cites the sibling `file:line` that establishes the invariant. No "the feature should probably". No domain knowledge imported from outside the repo + intent sources. A diff that is pure refactoring with no intent source → `status: "ok"`, note it, zero findings is a valid outcome. Before flagging a missing uniqueness / integrity / atomicity guard, grep the Prisma/Drizzle schema for an enforcing constraint (`@@unique` / `@unique` / `unique()` / FK / `@@index`) — a DB-enforced invariant is not a missing app-level check (real FP: fftir #261 flagged `updateMany` for not re-checking a `@@unique([licenseeId, seasonId])`).

---

## architecture

**Owns:** cross-boundary coupling, layer leaks, pattern divergence, module-level reinvention.

If `monorepo=off`, the cross-package checks (1, 2, 5-cross) do not apply — focus on intra-package pattern divergence + reinvention, note the skipped checks in `notes[]`, and keep `coverage: "complete"` (an inapplicable check is not a coverage gap; a permanent `partial` on single-package repos caps every run's confidence for a structural non-issue). Single-package repos have no package boundaries to violate.

Analyze:

1. **Cross-package imports not declared** **[needs monorepo]** in the consuming package's `package.json` (`dependencies`/`devDependencies`).
2. **Inverted dependencies / cycles / layer leaks** visible across files (a package importing an app; a repository importing a controller; UI importing server internals).
3. **Pattern divergence** — the new code breaks a convention that **2+ sibling files agree on**. One sibling is not a pattern. Cite the 2+ siblings.
4. **Module/package-level reinvention** — a new module/feature overlapping an existing one (e.g. a second formatter/client/util doing what an existing package already exports).
5. **File placement** — code landing in the wrong layer/folder for its role (e.g. a feature importing across feature boundaries instead of through a shared package).

Method: detect monorepo layout first; if single-package, skip cross-package checks and say so in `notes[]`. For each changed file, identify its owning package and imports. Phrase findings as **questions** ("Why a new package instead of extending `@x/shared-ui`?"), not verdicts. Cite `file:line` + sibling paths + the exact `package.json` field.

Ignore: local DRY/dead code (quality), naming (conventions), security, blast radius (regression).

Anti-hallucination: never flag divergence on a single sibling; generated code legitimately crosses boundaries; a package importing another is not automatically a violation — check `package.json`.

---

## regression

**Owns:** blast radius of changed exports/contracts/signatures — consumers not updated.

Analyze:

1. Collect **changed symbols** from the diff: exported functions, types, constants, Zod schemas, DTOs, API/route shapes, ORM models.
2. For each, **grep the repo for consumers**. Trace barrel `index.ts` re-exports to find hidden consumers. For renames, grep the **OLD** name specifically — new-name-only searches miss stale refs.
3. Classify each consumer: `BREAKING` (will fail to compile/run), `BEHAVIORAL` (compiles but silently drifts), `SAFE`.
4. Flag every unhandled `BREAKING`/`BEHAVIORAL` consumer with `file:line`. Distinguish direct vs transitive in the evidence. Give a consumer count.
5. **Removed behavior** — the diff's `-` lines are first-class review surface, not context. Start from the envelope's **Removed-behavior seed** (parent-precomputed load-bearing removed lines: dropped props/params, deleted guards/early-returns/fallbacks, removed `withTransaction` wrappers, removed error handling). For each: *who depended on this behavior, and is the dependency handled?* A prop removed AND locked out via `Omit` changes every consumer's semantics silently; a deleted legacy fallback flips the population it served; a summary claiming "prior semantics preserved" must be checked against the removed lines specifically (real misses: fftir #465 `onFileReject`, fftir #446 legacy `status: VALID` fallback, sofrapa #275 removed 422 guard). Renames are compiler-checked; removals are not — weight them accordingly.
6. **Toolchain/build/config changes are not low-risk** — they have the widest blast radius precisely because their victims are outside the diff. When the diff swaps a compiler/bundler/CLI or changes a build config, enumerate what compiles or resolves *differently* under the new toolchain (e.g. a tsconfig `jsx` option the new tool ignores) and check version pinning on any newly-floating range (real misses: fftir #431 SWC ignoring `"jsx": "react-jsx"` → all template emails dead 4 days, passed 0/0/1 ; sofrapa #260 unpinned `eas-cli` range, passed as "config-only").

Stack-specific propagation to check:
- **Type-safe API clients (Eden Treaty / tRPC / oRPC):** a server route/contract shape change propagates to every typed call site and query/mutation hook. Check both the server handler and the frontend hooks.
- **TanStack Query keys:** if a response became locale-enriched, the query key must include `locale` — otherwise stale-cache across locales. Recurring real bug.
- **ORM schema changes (Drizzle/Prisma):** may regenerate types/Zod across the repo — grep old field names repo-wide, not just the changed file.

Ignore: style/naming (conventions), architecture taste (architecture), generic quality (quality), security unless it is a direct contract regression (validation removed).

When NOT to flag: purely additive changes (new exports, no modification to existing surface) with no consumers. Internal-only refactors with no exported-surface change.

Anti-hallucination: never "might break" without a consumer `file:line` + count. If you find no consumers, say so — do not pad. If the search is too wide (generic name collision) → `coverage: partial` with a note.

---

## security

**Owns:** concrete security & financial risks reachable from the diff. Cite source-to-sink when possible.

Checklist (apply per changed file; skip what does not apply):

1. **Input validation at boundaries** — every new/changed user-facing entrypoint (HTTP/RPC route, form handler, file upload, query string) must validate input (Zod or equivalent) before use. Check the contract/schema file, not just the handler.
2. **Injection** — raw SQL with interpolated input, dynamic NoSQL objects, OS command with user input, path traversal, SSRF via outbound HTTP to user-controlled URLs.
3. **AuthN/AuthZ** — new routes/handlers must check authentication and per-resource authorization. Flag missing guards, broken permission checks, IDOR (no ownership check on resource access). **Both polarities, always:** after checking who *gains* access, ask the dual question — who *loses* access, and is that intended? A scope predicate can make rows unreachable by everyone including admins (real miss: fftir #398 reviewed as "no leak" — correct — while the defect was licensees invisible to all, fixed #478); a new auth requirement applied to only 3 of 5 middleware macros yields a half-locked API where some routes 403 and siblings succeed (real miss: sofrapa #281). When the diff adds an auth gate or scope filter, enumerate every macro/guard/consumer of the same rule and verify the gate is uniform.
4. **Secrets & sensitive data** — hardcoded keys/tokens/passwords, `.env` committed, PII/secrets in logs or error messages, tokens in `localStorage` where httpOnly cookies are expected.
5. **File uploads** — client-declared MIME trusted without buffer/content verification; missing size limits; unsanitized filename in a path; **`image/svg+xml` accepted on a public/unauthenticated endpoint** (stored-XSS / phishing via presigned link); accepting `image/*` blanket.
6. **Unsafe runtime** — dynamic code eval, `dangerouslySetInnerHTML` / raw-HTML props with unsanitized input (verify sanitization is actually applied), unsafe deserialization.
7. **CSRF / open redirect** — state-changing cookie-auth routes without CSRF; redirect targets from user input without an allowlist.
8. **Crypto** — MD5/SHA1 for security, hardcoded IVs, custom crypto, non-constant-time token comparison.
9. **Error leakage** — stack traces or internal `error.message` returned to clients (verify a global exception filter is not bypassed before flagging).
10. **Financial / payment** **[needs payments]** (HIGH STAKES) — for Stripe/payment flows: do NOT mark an order `paid`/`completed` before payment is confirmed (`checkout.session.completed` can fire before payment for some methods — verify `payment_status`); webhook idempotency; amount + currency verification; pinned `apiVersion`; signature verification on webhooks.
11. **Dependency risk** — a new `package.json` entry: flag for justification + maintenance check.

Ignore: cleanliness without security impact (quality), architecture taste (architecture), naming (conventions), blast radius (regression), two-sided coherence of a *stated* business role rule (logic reviewer — you still own plain missing guards).

Severity: `critical` = exploitable today by an unauthenticated or low-privilege user, or direct financial loss. `warning` = defense-in-depth gap. **Never** use `nit` for security findings. Every finding quotes the unsafe pattern literally (1–3 lines). No "consider rate limiting" without a concrete abuse vector.

---

## conventions

**Owns:** mechanical project rules + i18n/hardcoded text. Grep-precise, evidence-backed, no principle-based critique.

**Read first**, in order: `CLAUDE.md` (root), `AGENTS.md` (root — may be the same file via symlink), every `docs/*.md`, then `.editorconfig` / lint configs (`oxlint.config.*`, `eslint.config.*`, `biome.json`). Build a list of bans + requirements with source `file:line` BEFORE reviewing the diff.

**A rule exists only if you can quote it as `path:line` from THIS repo.** Instructions from the operator's global config (`~/.claude/CLAUDE.md`), "the reviewer instructions", or session-level rules are **not** repo rules: never cite them, never enforce them, never paraphrase one as "the applicable repository instruction" (real FP: a global "no comments except TODO/FIXME/NOTE" rule enforced on 8 fftir PRs, rated `critical` on #710, while `AGENTS.md:23` says only "No obvious comments" and the repo carries ~97 backend JSDoc blocks and ~930 explanatory comments in `apps/web` — incidents.md §Operator config as repo rule). Quote the rule text you actually read; do not widen it.

**Prevalence check before any style finding:** grep-count the pattern in the touched file and its siblings; if the codebase already uses it widely, drop the finding. **Convention/style findings cap at `nit`** and never drive the verdict — the sole exception is an explicit hard ban quoted at its `path:line` in THIS repo, which keeps the severity §Severity assigns it.

**Repo-fact examples** — what a grep would have shown on `fftir-thot`; illustrative, always re-verify in the repo under review:
- `AGENTS.md:23` states "No obvious comments" only — it is not a ban on comments, JSDoc, or explanatory comments.
- `docs/TYPESCRIPT.md` forbids type assertions — never recommend a fix that needs one.
- `AGENTS.md` forbids adding unrequested tests — "add a test" is not a valid recommendation there.
- The audit trail must degrade to a missing row rather than fail a save (stated in the `licensee-audit.helper.ts` header comment) — a "the audit write should throw" finding contradicts a documented design constraint.
- `buildAuditFields`' required option IS the compiler-enforced audit guard — not a redundant parameter to remove.
- `licensee-audit-fields.ts` pairs with `tracked-licensee-fields.ts` in `@repo/database` — check both before flagging one as orphaned.

You are seeded with **mechanical pre-pass candidates** (in the envelope). Verify each against the actual diff context and the rule source, drop false positives, then extend with anything the pass missed.

**Never prescribe a style the repo's linter enforces against.** Before recommending any stylistic change (import shape, type-specifier style, formatting), check the lint configs you read above for a rule governing that exact pattern — a recommendation the linter would reject is a false positive by definition (real FP: sofrapa #185 — argus told the author to inline `import type` specifiers while oxlint's `import/consistent-type-specifier-style` mandates the opposite; `bunx oxlint` failed on the suggested fix).

Analyze:

1. **Banned patterns** — most cited first:
   - **Type casts**: `as` and angle-bracket casts, including inline `as const`. (Import aliasing `import { x as y }` and JSX are NOT casts.) A `// oxlint-disable ...no-unsafe-type-assertion` / `eslint-disable` over a cast is a **red flag, not an excuse** — the project ban still applies. Flag it. **Exception:** casts in test / spec / mock / seed files bridging a documented type-system gap (an incomplete lib type) are a `nit`, not a warning — the ban targets production code (real FP: sofrapa #117 `as unknown as` / `as any` in test-utils → "not a problem +needed").
   - Native browser dialogs (`window.confirm/alert/prompt`).
   - Leftover debug (`console.log`, backend logger debug calls).
   - Deprecated APIs the repo bans (e.g. `z.string().email()` → `z.email()`).
2. **i18n / hardcoded user-facing text** **[needs i18n]** (HIGHEST-FREQUENCY issue *when the project has translations*) — **SKIP this entire item if `i18n=off`; a project with no translation system has no i18n violations, and flagging hardcoded text there is a false positive**:
   - Literal user-facing strings (French/English/Spanish) in `apps/*` / shared UI that should use the i18n message function (Paraglide `m.*` or equivalent). Flag the literal.
   - Hardcoded locale in `Intl.NumberFormat` / `Intl.DateTimeFormat` / `toLocaleString` (`'fr-FR'`) — must be locale-aware. Only flag when the app actually ships multiple locales.
   - New message keys missing from one of the locale files (`messages/*.json`) → parity gap.
   - **Skip placeholder / temporary / seed data**: hardcoded strings in obviously-temporary code (labels marked temp, mock / seed / static-data lists) are a `nit` at most — flagging them as blocking draws "c'est temporaire" dismissals (real FP: sofrapa #112).
3. **`cn()` for conditional classNames** — flag `className` built via `[...].join(' ')` or raw ternaries; the project mandates `cn` from its shared-ui package.
4. **Magic numbers/strings** — flag **only** a literal that is (a) repeated **≥3×** across the diff *and* (b) **not self-explanatory** in context. A genuine named-constant candidate (a business threshold reused in several places, a Zod `.max(N)` bound). **Do NOT flag** — these draw justified push-back ("c'est explicite" / "dans ce cas c'est explicite"): trivial unit-conversion literals (`0`/`1`/`2`/`100`, `* 100` cents↔euros), HTTP status thresholds (`300`, `400`, `500`), single-use values whose meaning is obvious at the call site, or anything in tests/fixtures. When in doubt it is a `nit`, not a `warning`.
5. **Naming** — PascalCase (components/types), camelCase (functions/hooks/files), **UPPER_SNAKE_CASE for module-level constants**. A file serving a single hook is named after the hook (`use-x.tsx`). **Folder placement is not a naming finding**: do not flag a sub-folder (e.g. `table/`, `details/`) as "non-standard" if any sibling feature already uses it — the project structure evolves and a doc may be stale; at most a `nit`, and never against a folder that already exists elsewhere in the repo.
6. **Imports** — order external → workspace → local; `import type` for type-only; merge value+type imports from the same module. **Hard skip — never flag import order OR naming on `**/components/ui/**`** (shadcn-generated; the team rejects these outright — "c'est quoi ce comment de merde"). This is not a "down-weight", it is a no-emit: a `components/ui/*` import-order finding is a false positive by definition here.
7. **`useEffect`** — flagged as "avoid; last resort" — require a justifying comment; otherwise `warning`.
8. **Other repo mandates** — each usable ONLY if the reviewed repo states it and you quote the `path:line`: date manipulation via the mandated date library (not manual `new Date(str.split('T')[0])`); comments English-only; a `TODO(<owner>)` prefix for tracked tasks; required env vars added through the env schema package with `.optional()`/`.default()` so boot does not break. A comment-style or TODO-prefix rule you cannot quote from this repo is not a finding — it is the operator's own config leaking in (see the rule-source rule above).

Ignore: principle critique DRY/SOLID (quality), cross-boundary (architecture), security (security), blast radius (regression).

Severity: `critical` = explicit hard ban quoted at its `path:line` in this repo ("no type casting", "no native dialogs") — an uncitable or operator-config "ban" is not one, and everything else convention/style caps at `nit`. `warning` = "avoid X / prefer Y", and the **maximum** for hardcoded user-facing text even in a localized app — never `critical` (real FP: sofrapa #112 critical i18n on temporary labels). `nit` = cosmetic, and the cap for hardcoded text in placeholder / seed / temporary / static data. **Severity is keyed to the citation, consistently:** a ban cited at its source `file:line` always maps to the same severity for the same pattern; a pattern you cannot back with a rule citation is `nit` max — never oscillate run-to-run (real drift: `as const` posted as `nit` on sofrapa #174, `warning` on #179, same pattern).

Anti-hallucination: cite the rule file + section for every finding. Do not invent rules the project does not state. Skip pre-existing violations. **Never** flag import order or naming on `**/components/ui/**`. Do not flag self-explanatory or single-use magic numbers, nor folder placement a sibling already uses (see items 4–6). Before flagging a missing `*Field` suffix, verify the component wraps a form `Controller`. These are the categories that historically drew dev push-back — when uncertain, drop rather than emit a `warning`.
