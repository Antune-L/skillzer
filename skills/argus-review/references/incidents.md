# Incident log — real-world failures behind the rules

Each SKILL.md rule marked "(incidents.md)" was distilled from one of these. This file is the
evidence base; it is NOT loaded during a normal run. Consult it only when questioning or
revising a rule, or when adding a new incident.

Format: `incident → rule it produced`.

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
