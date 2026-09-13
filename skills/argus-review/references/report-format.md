# Aggregated report format

Template for Argus's final output. Verdict + confidence header, per-section findings, one global action list. Self-contained.

## Structure

```
# Argus — <branch> vs <base>  [light | full]

**Verdict:** <blocking | needs-attention | pass> · **Confidence:** <high | medium | low>
**Scope:** <N> files (+<X> / -<Y>) · <K> generated/lock/snapshot files ignored
**Reviewers:** quality · conventions · regression · logic[ · architecture · security]
**Coverage:** <one line per top-level dir in the diff with its file count and finding count — e.g. `apps/server 14 files · 6 findings — apps/mobile 12 files · 0 findings`. Scope comes from the FILE LIST, never from the PR title/description; a dir with many files and zero findings is a visible fact the user can challenge, not a silent implication of "clean" (real misses clustered exactly in the zero-finding dirs of #279/#280).>

## Summary

| Section      | Critical | Warning | Nit |
|--------------|----------|---------|-----|
| Quality      | X        | Y       | Z   |
| Architecture | X        | Y       | Z   |  ← omit row in light
| Regression   | X        | Y       | —   |
| Security     | X        | Y       | —   |  ← omit row in light
| Conventions  | X        | Y       | Z   |
| Logic        | X        | Y       | Z   |
| **Total**    | **X**    | **Y**   | **Z** |

(Only rows for dispatched reviewers. Security never has nits. Full mode: counts are POST-verification — after verifier drops/demotions.)

Full mode, when the verifier filtered anything (omit when all zeros):

```
**Verifier:** <D> intentional dropped · <M> demoted to nit[ · <section(s)> unverified]
```

---

## Quality        — grouped by file
## Architecture   — grouped by concern (full only)
## Regression     — grouped by changed symbol
## Security       — grouped by vulnerability class (full only)
## Conventions    — grouped by rule family
## Logic          — grouped by business rule / intent item
## Subagent failures   (only if any reviewer failed)
## Recommended next actions
```

### Per-finding rendering

```
### `path/to/file.ts`

#### [critical] L42-L58 — Duplicated TecDoc client setup
`createTecdocClient` block repeated verbatim across 5 controllers (also `articles.controller.ts:21`, `categories.controller.ts:30`).
**Fix:** extract to a shared factory in the catalog module.
```

Keep each finding to: severity tag · `file:line` · one-line title · one evidence sentence · one fix sentence. No diff blocks, no long quotes.

## Aggregation rules

1. **Verdict first**, before the summary table (`blocking` / `needs-attention` / `pass`).
2. **Confidence next to verdict** (`high` / `medium` / `low`).
3. **Sort within each section** by severity (critical → warning → nit), then `file` A–Z, then `line`.
4. **Keep empty sections** with one line: `No findings.` (or `No regressions detected.` / `No security findings.`). Empty is signal.
5. **Total row** equals the sum of section rows — recount before emitting.
6. **Recommended next actions are global** — a critical regression and a critical convention ban compete on one prioritized list.
7. **Dedupe before rendering** — collapse only on section + file + line + severity + normalized title. Never across sections; security never collapses.
8. **Subagent failures** section appears only when ≥ 1 reviewer failed; degrade gracefully with the cause and a "re-run manually" hint.

## Recommended next actions

Prioritized, global, actionable. The user picks what to fix.

```
1. **[critical]** `reviews-section.tsx:13` — `[...reviews, ...reviews]` double-counts every review; use `reviews` directly.
2. **[critical]** `article-details-formatters.ts:42` — remove the `as` cast (project hard-ban); annotate the return type instead.
3. **[warning]** Extract the duplicated `createTecdocClient` block into a shared factory.
4. **[warning]** `basket-recap.tsx:26` — replace hardcoded `'fr-FR'` with the active locale.
```

**The rendered report is local, and it is NOT the posted review body.** The body posted to the PR is the short subset defined in posting.md §Review body — exhaustive contents (verdict line + counts table + optional `Unverified:` line + mandatory coverage line + off-diff bullets, ≤ ~150 words). Never widen it with report material.

## What NOT to include

- Raw diff blocks — the user already has `git diff`.
- File contents quoted at length — reference `file:line`.
- Praise or filler ("Great PR overall!"). Findings only.
- Speculation about intent — stick to what the diff shows.
- **Internal-report material in anything posted** — "What was verified as safe" lists, tables of dropped/demoted findings (`| Claim | Why it died |`), fan-out leaks ("6/6 reviewers ok", "raised independently by two reviewers", "the verifier disagreed"), and test/typecheck claims ("105 pass / 0 fail" — argus does not run the suite). posting.md §Deny-list rejects these mechanically (real incidents: fftir #462/#707/#700/#702/#698, sofrapa #442).
- **Any French in an emitted string** — the report is English too (posting.md §Language); repo/UI strings are quoted verbatim in backticks.
- Recommendations to add new dependencies — flag if a reviewer slipped one in.
- **"Verified as delivered" / "checks out" / "verified clean" lists.** A positive assertion carries the same evidence bar as a finding — either cite the specific `file:line` checks that back it, or say nothing about that area (the coverage line already shows what was reviewed). The July 2026 retro's three worst misses all sat inside areas the summary had explicitly certified clean ("locale typing … check out" while the diff made `locale` optional for every mail; "per-vehicle TecDoc image resolution verified clean" while it was a 1→N×2 request amplification). An unverified doubt belongs in one `Unverified:` line, phrased as the concrete in-diff question — never converted into a clean bill of health.

## Footer

```
_Read-only review. To post these inline on the PR, re-run with `--post` (default: all severities, nits included). To apply the fixes, say **« corrige ce qui est pertinent »** (separate step — nits skipped by default)._
```
