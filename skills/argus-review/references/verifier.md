# Adversarial verifier — refute findings before they reach the verdict

**Full mode only.** The verifier is a second-opinion agent whose job is the *opposite* of a reviewer's: it receives the `warning`/`critical` findings of ONE reviewer and tries to **refute** each of them. It exists because reviewers keep leaking three known false-positive clusters despite prompt rules: intent-stated refactor changes, temporary/placeholder data, and confirmation-seeking or unsourced claims. A finding that survives an adversarial read is worth posting; one that does not must never raise the verdict.

**Pipeline, not barrier.** The orchestrator dispatches one verifier per reviewer **as soon as that reviewer's reply validates** — it never waits for the whole fan-out. Verification of a finding needs no cross-reviewer context. Only dedupe + verdict (which already wait for everyone) run after all verifiers return.

## What gets verified

- Only `warning` and `critical` findings. Nits are never dispatched — they cannot raise the verdict.
- The orchestrator applies the mechanical severity-inflation guard (SKILL.md §Verdict rules) to the reviewer's reply **first**; findings it demotes to `nit` are not sent either.
- A reviewer whose reply has zero remaining warnings/criticals gets **no verifier** — zero cost.

## Verdicts and how the orchestrator applies them

| Verdict | Meaning | Orchestrator action |
|---|---|---|
| `real` | Survives the adversarial read: concrete defect, evidence holds, not explained by the PR's stated intent | Keep finding + severity unchanged |
| `intentional` | The flagged change matches the PR's stated intent / is placeholder-seed-temp data, and no unhandled consequence is shown | **Drop** from findings; count under "filtered by verifier" in the report |
| `unsourced` | Evidence reduces to confirmation-seeking, a speculative edge-case with no plausible real input, or an uncited third-party-lib behavior claim | **Demote to `nit`**, rephrase as a question |

**Tie-breaking is adversarial:** when genuinely uncertain whether a finding is real, the verifier must choose `intentional` or `unsourced` — the cost of a posted false positive (human dismissal, reverted "slop feedback") exceeds the cost of a demoted maybe.

**Fail-open on verifier failure:** if the verifier errors or returns an invalid reply after one retry, the orchestrator keeps that reviewer's findings **unchanged** (as if all `real`) and notes "unverified" in the report. The verifier is a false-positive filter — its failure must never delete a potentially real bug. Same rule per-finding: an id missing from `verdicts[]` is treated as `real`.

## Dispatch envelope

```
You are an adversarial finding verifier for a PR review. Your job is to REFUTE
the findings below, not to confirm them. When uncertain, refute.

FIRST, read these files:
1. <SKILL_DIR>/references/verifier.md §Verdicts — your complete methodology and output shape.
2. <ARGUS_TMP>/diff.patch — the authoritative diff. Do NOT re-run git diff. Read
   only the hunks relevant to the findings below; open repo files only for
   context outside the patch window.

Scope:
- Repository (absolute path): <path>
- Base: <base-branch>  Branch: <branch-name>
- Reviewer section under verification: <section>

Intent sources (AUTHORITATIVE for judging "intentional" — do not invent intent):
- PR title + description: <gh pr view output, or "none">
- Linked PRD / Notion card content: <or "none">
- Mockup / screenshot spec: <compact spec, "<url> — not rendered", or "none">
- Commit messages: <git log base..branch subjects+bodies>

Findings to verify (JSON, verbatim from the reviewer):
<the reviewer's warning/critical findings array>

For EACH finding, actively try to kill it:
- Does the PR's stated intent explain the change? An intent-stated contract /
  signature / env-shape change with no broken consumer shown → "intentional".
- Is the flagged data placeholder / seed / temp / mock? → "intentional".
- Does the evidence reduce to "confirm this is intended" or "verify with
  design/author" — no concrete defect pointed at? → "unsourced".
- Is it a speculative edge-case with no plausible real input in this product's
  domain? → "unsourced".
- Does the proof rest on a third-party lib's runtime behavior with no doc
  citation in the finding? Check the lib's current docs (context7 MCP); if the
  docs contradict the claim or you cannot confirm it → "unsourced".
- Otherwise, re-read the cited file:line in the patch: does the defect
  concretely exist as described? Only then → "real".

Return ONE JSON object and nothing else:
{
  "agent": "verifier",
  "version": "1.0.0",
  "section": "<section under verification>",
  "verdicts": [
    { "id": "<finding id, verbatim>", "verdict": "real|intentional|unsourced",
      "reason": "<one concrete sentence: what refuted it, or why it survives>" }
  ],
  "errors": []
}
Rules: one verdict per finding id, ids verbatim, no extra ids. Token budget
1500 tokens (JSON only).
```

`<SKILL_DIR>` / `<ARGUS_TMP>` — same literal-absolute-path rule as every other dispatch (subagents inherit no env).

## Orchestrator validation

1. Parse JSON (strip accidental fences). Unparseable → retry once with the standard "JSON only" nudge → fail-open.
2. `verdicts[].id` must each match a dispatched finding id; unknown ids are ignored, missing ids default to `real`.
3. `verdict` enum valid; invalid value on an entry → that entry defaults to `real`.
4. Apply actions (keep / drop / demote) to the reviewer's findings **before** they enter aggregation. Recompute the reviewer's `summary` counts after application.

## Report surface

The report lists, per section: `filtered by verifier: N intentional dropped, M demoted to nit` (omit the line when zero). Dropped findings never appear in findings tables nor on the PR; demoted ones appear as nits. A fail-open ("unverified") section is flagged in the report header notes.
