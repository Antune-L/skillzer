# Adversarial verifier — refute findings before they reach the verdict

**Full mode: all warnings/criticals. Light mode: criticals only** (SKILL.md §Reviewer set — an unverified critical drives a `blocking` verdict, so even light runs dispatch a verifier for surviving criticals; most light runs have zero). The verifier is a second-opinion agent whose job is the *opposite* of a reviewer's: it receives the `warning`/`critical` findings of ONE reviewer and tries to **refute** each of them. It exists because reviewers keep leaking three known false-positive clusters despite prompt rules: intent-stated refactor changes, temporary/placeholder data, and confirmation-seeking or unsourced claims. A finding that survives an adversarial read is worth posting; one that does not must never raise the verdict.

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

**Carve-outs the adversarial tie-break must NOT kill:**
- **Evidence-backed duplication findings.** A reuse/clone finding that names the pre-existing sibling `file:line` is not refutable by "matches an existing pattern elsewhere" or "N copies already exist" — N existing copies are the *argument for* extraction, not against the finding (real bad drop: sofrapa #271, a valid 5th-copy pagination finding dropped on exactly this ground while the same PR promoted the shared component that covered it). Refute it only by showing the cited sibling does not exist or is not substantially equivalent.
- **Magnitude-bearing intentional changes.** "The PR intends this change" only supports `intentional` when the *magnitude* is also plausibly intended. Before dropping a finding about a widened limit/relaxed guard/removed cap as intent-stated, state the before→after magnitude in the reason; an intent line saying "relax rate limits" does not cover a silent ×360 widening across 60+ routes (real bad drop: sofrapa #275 — reported as "a rate-limit relaxation … checked out as intended" with no magnitudes).

**Fail-open on verifier failure:** if the verifier errors or returns an invalid reply after one retry, the orchestrator keeps that reviewer's findings **unchanged** (as if all `real`) and notes "unverified" in the report. The verifier is a false-positive filter — its failure must never delete a potentially real bug. Same rule per-finding: an id missing from `verdicts[]` is treated as `real`.

## Dispatch envelope

```
You are an adversarial finding verifier for a PR review. Your job is to REFUTE
the findings below, not to confirm them. When uncertain, refute.
Every string you emit (reason, errors) is ENGLISH, whatever the repo's or the PR's
language; quote repo/UI strings verbatim in backticks.

FIRST, read these files:
1. <SKILL_DIR>/references/verifier.md §Verdicts — your complete methodology and output shape.
2. <ARGUS_TMP>/diff.patch — the authoritative diff. NEVER re-run git diff (not
   even file-scoped) and NEVER `git show <branch>:<path>`. Read only the hunks
   relevant to the findings below. For context outside the patch window in a
   changed file, Read <ARGUS_TMP>/branch/<repo-path> (branch-side snapshot,
   when present); working-tree files are for unchanged context only.

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
- Does the finding's recommended fix violate a repo doc — a type assertion where
  `docs/TYPESCRIPT.md` forbids casts, "add a test" where AGENTS.md forbids
  unrequested tests, a new dependency, a documented design constraint? Then the
  finding is refuted: → "unsourced" (or "intentional" when the doc mandates the
  current behavior).
- Does it enforce a rule that is NOT quotable as path:line in THIS repo — the
  operator's global config, "the reviewer instructions", a paraphrase widened past
  what the repo doc says? → "intentional" (not a repo rule, nothing to fix).
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

The report lists, per section: `filtered by verifier: N intentional dropped, M demoted to nit` (omit the line when zero), **followed by one line per dropped/demoted finding: its title + the verifier's reason verbatim, including any before→after magnitude**. A drop summarized as "checked out as intended" with no evidence is not reportable — the user must be able to audit every drop (the two audited bad drops of the July 2026 retro were both invisible one-liners). Dropped findings never appear in findings tables nor on the PR; demoted ones appear as nits. A fail-open ("unverified") section is flagged in the report header notes.
