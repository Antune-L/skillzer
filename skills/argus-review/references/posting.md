# Posting findings inline on the PR (`--post`)

Optional last-mile step. Argus is read-only by default; `--post` (or "poste les findings sur la PR") publishes them as **inline review comments** via `gh`. This is the step the user otherwise does by hand on nearly every review.

**Posting publishes to GitHub — outward-facing. Resolve the target PR# yourself and announce it** ("posting to PR #113") — an explicit number in the prompt wins; otherwise auto-resolve from the branch (§Resolve target). Ask the user **only** when no open PR exists or several candidates match — making the user re-run with the number is the friction this skill exists to remove.

**Review event maps to the verdict** (§Review event): `REQUEST_CHANGES` when the verdict is `blocking` or `needs-attention` (any critical or warning), `COMMENT` for a nits-only `pass`, and **`APPROVE` when there is genuinely zero feedback** (clean `pass`, no findings of any severity — the user wants the merge green-lit in that case).

## The one mechanism: a single PR *review* with inline comments

Each finding is an **inline comment anchored at its `file:line`**, all carried in the `comments[]` array of **one** PR review created via:

```
gh api repos/<owner>/<repo>/pulls/<PR#>/reviews --method POST --input <payload>.json
```

The review `body` is a **concise summary only** — verdict + counts table + any findings that genuinely cannot be anchored (file-level or off-diff). It is **not** the rendered report.

**Hard ban — never do these when there are findings to anchor:**

- ❌ `gh pr comment` / `gh api .../issues/<PR#>/comments` — posts a single conversation-tab blob, not inline. This is the exact "one big comment, not visual" failure the user rejected.
- ❌ Dumping the full rendered report (`report-format.md` output) into the review `body`. The body is a summary; the findings live inline.
- ❌ Posting inline **and also** a full-report issue comment. One review, inline. Nothing else.
- ❌ Posting comments **one by one** — each standalone `POST .../pulls/<PR>/comments` mints its own empty single-comment review in the timeline. Build the full `comments[]` array and submit **one** review request (real incident: sofrapa #183 — 9 empty single-comment reviews, 13 timeline entries for one run). Sole exception: §File-level anchors.
- ❌ Submitting **placeholder / probe / "in progress" reviews** — never create a review to test permissions, reserve a spot, or stream progress; those entries are permanent timeline pollution (real incidents: fftir #325 — three "Argus review — in progress…" placeholders before the real review; fftir #326 — two "(permission probe — ignore)" reviews left visible; sofrapa #183 — two "permission-check artifact" reviews). If a PENDING review was created by accident, delete it (`gh api -X DELETE repos/<o>/<r>/pulls/<PR>/reviews/<id>`) before the run ends; a submitted one cannot be deleted — which is why it must never be submitted.

A `pass` with **zero** findings does **not** use `gh pr comment` — submit an `APPROVE` review via the reviews API with a one-line summary body and an empty `comments[]` (§Review event). `gh pr comment` is the documented last resort only if *not a single finding* could be anchored inline (rare — say so explicitly in the report).

## Defaults (match the user's standing preference)

- **Severity: post all of `critical`, `warning`, and `nit`.** The user wants nits in the comments too. Anchor every nit inline like any other finding; prefix its comment body with `[nit]` so it reads as low-priority. Only drop nits if the user explicitly asks for critical+warning only on a given run.
- **Inline at `file:line`** for every finding whose line is commentable on the PR diff (see line-validation below). Findings with no line (file-level) or whose line is off-diff → post as a **file-level comment** on that file (§File-level anchors) so they still get a resolvable thread; fall back to a review-body bullet only when the file itself is absent from the diff — and never collapse the whole set into the body because a few don't anchor.
- One review per run carrying all inline comments + the concise summary body.
- **Review event derives from the verdict** (see §Review event) — `REQUEST_CHANGES` on blocking/needs-attention, `COMMENT` on a nits-only pass, `APPROVE` on a zero-finding pass.

## Review event

The submitted review's `event` mirrors the Argus verdict so the PR's review state reflects the outcome — a PR with real findings ends up in GitHub's **"Changes requested"** state, a clean one gets **approved**, not a neutral comment:

| Verdict (from SKILL.md verdict rules)        | Findings           | `event`            | GitHub state      |
| -------------------------------------------- | ------------------ | ------------------ | ----------------- |
| `blocking` (≥1 critical)                     | critical/warning   | `REQUEST_CHANGES`  | Changes requested |
| `needs-attention` (≥1 warning, no critical)  | critical/warning   | `REQUEST_CHANGES`  | Changes requested |
| `pass`                                       | nits only          | `COMMENT`          | Commented         |
| `pass`                                       | **zero findings**  | `APPROVE`          | Approved          |

- **Derive the event from the FINAL posted set, never the pre-posting report.** After dedupe drops and line-validation, recount severities across the kept findings (`comments[]` + file-level anchors + body bullets) and map that recount to the event. A warning deduped into an existing thread no longer raises the event (real incidents: sofrapa #185 — the sole warning was folded into gemini's thread, only nits were posted, yet the review went `REQUEST_CHANGES`; fftir #310 and sofrapa #181/#177/#176 — warnings posted under `COMMENT`).
- **`APPROVE` only on a genuinely empty review** — no critical, no warning, **no nits**. The user wants a clean PR green-lit. If even one nit was posted, that is feedback → `COMMENT`, not `APPROVE`.
- The user opts into both ends — Request changes once findings are uploaded, Approve when there is nothing to flag. Do not silently downgrade a blocking/needs-attention review to `COMMENT`, and do not withhold the approve on a clean pass.
- A `REQUEST_CHANGES` review can later be dismissed by the human if they disagree; that is expected and fine.
- An `APPROVE` review carries no inline comments (there are none) — submit it with just the summary body via the reviews API (§Build the review payload), not `gh pr comment`.
- **`APPROVE` sets the review state only — never merge.** Do not run `gh pr merge` (nor `--auto`, nor enable auto-merge). The skill approves; the human merges. If branch protection requires the approval to unblock the merge, that is the human's action afterward, not Argus's.

## Resolve target

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)   # current repo; override explicitly only for cross-repo posting
PR=<PR#>                                            # explicit arg, or:
PR=$(gh pr view <branch> --json number -q .number) # current/named branch → its open PR
HEAD_SHA=$(gh pr view "$PR" --repo "$OWNER_REPO" --json headRefOid -q .headRefOid)
```

If no PR exists for the branch, tell the user (offer to `gh pr create`) — do not invent a PR number.

## Line-validation — make findings actually land inline

GitHub rejects (422) an inline comment whose `line` is not part of the PR diff on the RIGHT side. Reviewers report lines in the new file; many land on context outside a hunk. **Validate deterministically before posting** so findings anchor instead of silently flooding the body.

Build the commentable line set per file from the **already-precomputed diff** (do not re-run `git diff` — reuse the patch from procedure step 2). Each hunk header `@@ -a,b +c,d @@` means the RIGHT side spans lines `c … c+d-1`:

```bash
# commentable RIGHT-side lines per file, from the saved patch in the run's scratch dir
# ($ARGUS_TMP = the mktemp -d path from procedure step 2 — repeat it literally, env doesn't persist)
awk '
  /^\+\+\+ b\// { f=substr($0,7); next }
  /^@@/ { split($3,a,","); ln=substr(a[1],2)+0; inhunk=1; next }
  inhunk && /^[+ ]/ { print f":"ln; ln++ }
  inhunk && /^-/ { next }
  /^diff |^index |^--- / { inhunk=0 }
' "$ARGUS_TMP/diff.patch" | sort -u > "$ARGUS_TMP/commentable.txt"
```

For each kept finding:
1. If `path:line` ∈ commentable set → inline comment.
2. Else if another changed line of the same hunk is close (±3) → snap `line` to it and keep inline (note the snap in the body).
3. Else → off-diff: post **that one finding** as a file-level comment after the review is submitted (§File-level anchors). Only if its file is entirely absent from the diff → summary-body bullet. Do not move the others.

## File-level anchors for off-diff findings

Body-folded findings get no thread, so nobody can reply to or resolve them (real gap: sofrapa #182 — 2 warnings folded into the body, untrackable). For a finding whose line is off-diff but whose **file is part of the diff**, post a file-level review comment right after the review is submitted:

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --method POST \
  -f body="**[warning] section** — <evidence>. <fix>" \
  -f commit_id="$HEAD_SHA" -f path="<file>" -f subject_type="file"
```

- This is the **one sanctioned exception** to the no-one-by-one rule: a handful of deliberate file-level threads, not an unbatched fallback for findings that could anchor inline.
- Count these in the body's counts table like any posted finding; do not also list them as "off-diff" bullets — they have threads now.
- File absent from the diff entirely → summary-body bullet, the true last resort.

## Build the review payload

Map each anchored finding to a comment object: `path`, `line`, `side: "RIGHT"`, `body`. For a multi-line finding add `start_line` + `start_side: "RIGHT"` (start) alongside `line` (end). Compose one review; set `event` from the verdict per §Review event (`REQUEST_CHANGES` for the blocking/needs-attention example below, `COMMENT` for a nits-only/pass run):

```json
{
  "commit_id": "<HEAD_SHA>",
  "event": "REQUEST_CHANGES",
  "body": "## Argus — <verdict> · <confidence>\n\n<counts table>\n\n**Off-diff / file-level findings**\n- `path` — <evidence>. <fix>",
  "comments": [
    { "path": "apps/web/src/features/reviews/reviews-section.tsx", "line": 13, "side": "RIGHT",
      "body": "**[critical] regression** — `[...reviews, ...reviews]` double-counts every review; the `(… avis)` counter is inflated. Use `reviews` directly." },
    { "path": "apps/web/src/features/article/article-details-formatters.ts", "line": 42, "side": "RIGHT",
      "body": "**[critical] conventions** — `as` cast is hard-banned (CLAUDE.md « No type casting »). Annotate the return type or use a type guard." },
    { "path": "apps/web/src/features/article/article-card.tsx", "line": 18, "side": "RIGHT",
      "body": "**[nit] quality** — extract the repeated `border-muted` class to a shared style; cosmetic, non-blocking." }
  ]
}
```

- **Comment body convention:** `**[severity] section** — <evidence>. <recommendation>`. Evidence + fix only; no preamble. **English only** (the report language, regardless of the PR's language). **Never expose the internal fan-out** in a posted comment — no "the logic reviewer rated this critical", no internal confidence levels; the finding stands on its evidence alone.
- **Body when every finding anchored inline:** verdict line + counts table only — omit the "Off-diff" section entirely. Keep it short. **No prose walkthrough, no per-finding commentary, no meta-narration of the review process** (real drift: fftir #310/#311 bodies carried long walkthroughs and gemini meta-commentary).
- **Unverified gaps are not findings.** Reviewer `notes[]` entries — "screenshot `<url>` not rendered", "could not verify X" — never appear in `comments[]` nor in the counts table (real incidents: sofrapa #183/#184 counted "fidelity unverified" as nits). Render them as one short `Unverified: …` line in the body.

## Dedupe against ALL existing threads — humans and bots, not just argus re-runs

Before posting, pull every existing comment on the PR (inline review comments + conversation comments, **all authors** — the PR author, human reviewers, gemini-code-assist, codex):

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --paginate --jq '.[] | "\(.user.login) \(.path):\(.line) :: \(.body)"'
gh api "repos/$OWNER_REPO/issues/$PR/comments" --paginate --jq '.[] | "\(.user.login) :: \(.body)"'
```

Then for each finding:

1. **Same `path:line` already commented (any author)** → skip.
2. **Same topic on the same file already raised by anyone** (semantic match, not just line-exact — e.g. a human already flagged the hardcoded FR labels) → do NOT repost it as a fresh finding. Either skip it, or if argus adds material evidence (extra occurrences, a concrete fix), **reply referencing the existing thread** ("extends @user's point above: …") instead of opening a duplicate.

Reposting a point a human already made — especially the PR's own reviewer — reads as "the bot didn't read the thread" and tanks trust in the whole batch (real incident: sofrapa #112, argus duplicated the user's own earlier comment → "pk tu répètes, ta pas lu ou quoi ?"). Building on an existing thread with credit (sofrapa #103, gemini overlap acknowledged in the finding) is the correct pattern.

3. **Commenting on another reviewer's claim is itself an assertion.** Endorsing, ranking ("higher-priority"), or refuting a human's or bot's finding in the review body requires the same evidence bar as an own finding — open the schema, check the docs first. Real incident: fftir #317, the body promoted gemini's `licensee.user` null-safety claim to "higher-priority" while the Prisma relation is `required`; the author had to refute argus's endorsement. Refuting with a doc citation is high-value (fftir #311, TanStack default columns); an unverified endorsement is a co-signed FP — when unverified, say nothing about it.

## Post

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/reviews" --method POST --input "$ARGUS_TMP/review.json" \
  --jq '{id, state, html_url, inline: (.comments|length)}'
```

Confirm `inline` > 0 (unless the only findings were genuinely off-diff). If it is 0 while findings exist, the lines did not anchor — re-check line-validation before falling back to the body.

**Count-consistency check (mandatory):** the counts table in the review `body` must equal *posted inline comments + file-level anchors + off-diff bullets actually listed in the body*, after dedupe drops. Every finding the table advertises must exist as a trackable item — a table announcing 11 findings with 3 posted and 8 living only in body prose is a posting bug (real incident: sofrapa #188). A summary that announces "1 warning + 3 nits" while only 1 inline comment exists is a posting bug (real incident: fftir #233/#238) — recount after dedupe/line-validation and rebuild the body table from the final `comments[]` + off-diff list, never from the pre-posting report.

## Failure handling

- **422 "line must be part of the diff"** on the whole request — one or more `comments[]` lines are off-diff. Identify the offending comment(s), move **only those** into the summary `body` bullet list, keep the rest inline, and re-post. Never drop a finding silently; never collapse all findings into the body because one failed.
- **403 / not a collaborator** — surface to the user; they may need to post under their own auth.
- **Wrong PR / branch mismatch** — re-resolve `PR` and `HEAD_SHA`; never post to a PR the user did not confirm.

## After posting

Report back: PR#, number of **inline** comments posted (broken down by severity, nits included), number folded into the summary body (with why), the verdict, and the **review state submitted** (`REQUEST_CHANGES` or `COMMENT` — confirm against the `state` field returned by the `gh api … /reviews` call). Keep the local rendered report intact — posting is additive, not a replacement for the report.
