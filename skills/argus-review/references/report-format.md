# Aggregated report format

Template for Argus's final output. Verdict + confidence header, per-section findings, one global action list. Self-contained.

## Structure

```
# Argus — <branch> vs <base>  [light | full]

**Verdict:** <blocking | needs-attention | pass> · **Confidence:** <high | medium | low>
**Scope:** <N> files (+<X> / -<Y>) · <K> generated/lock/snapshot files ignored
**Reviewers:** quality · conventions · regression[ · architecture · security]

## Summary

| Section      | Critical | Warning | Nit |
|--------------|----------|---------|-----|
| Quality      | X        | Y       | Z   |
| Architecture | X        | Y       | Z   |  ← omit row in light
| Regression   | X        | Y       | —   |
| Security     | X        | Y       | —   |  ← omit row in light
| Conventions  | X        | Y       | Z   |
| **Total**    | **X**    | **Y**   | **Z** |

(Only rows for dispatched reviewers. Security never has nits.)

---

## Quality        — grouped by file
## Architecture   — grouped by concern (full only)
## Regression     — grouped by changed symbol
## Security       — grouped by vulnerability class (full only)
## Conventions    — grouped by rule family
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

## What NOT to include

- Raw diff blocks — the user already has `git diff`.
- File contents quoted at length — reference `file:line`.
- Praise or filler ("Great PR overall!"). Findings only.
- Speculation about intent — stick to what the diff shows.
- Recommendations to add new dependencies — flag if a reviewer slipped one in.

## Footer

```
_Read-only review. To post these inline on the PR, re-run with `--post` (default: all severities, nits included). To fix, edit manually or invoke a fix-capable tool._
```
