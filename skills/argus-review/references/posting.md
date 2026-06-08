# Posting findings inline on the PR (`--post`)

Optional last-mile step. Argus is read-only by default; `--post` (or "poste les findings sur la PR") publishes them as **inline review comments** via `gh`. This is the step the user otherwise does by hand on nearly every review.

**Posting publishes to GitHub — outward-facing. Confirm the target PR# with the user before posting.** Default to `event: "COMMENT"` (never auto-`REQUEST_CHANGES`/`APPROVE` — the human curates the verdict).

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

`gh pr comment` is allowed in **exactly one** case: a `pass` verdict with **zero** findings → post a one-line summary comment (nothing to anchor). It is also the documented last resort only if *not a single finding* could be anchored inline (rare — say so explicitly in the report).

## Defaults (match the user's standing preference)

- **Severity: post all of `critical`, `warning`, and `nit`.** The user wants nits in the comments too. Anchor every nit inline like any other finding; prefix its comment body with `[nit]` so it reads as low-priority. Only drop nits if the user explicitly asks for critical+warning only on a given run.
- **Inline at `file:line`** for every finding whose line is commentable on the PR diff (see line-validation below). Findings with no line (file-level) or whose line is off-diff → fold into the review **summary body** as a bulleted list, individually — never collapse the whole set into the body because a few don't anchor.
- One review per run carrying all inline comments + the concise summary body.

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
# commentable RIGHT-side lines per file, from the saved patch at /tmp/argus_diff.patch
awk '
  /^\+\+\+ b\// { f=substr($0,7); next }
  /^@@/ { split($3,a,","); ln=substr(a[1],2)+0; inhunk=1; next }
  inhunk && /^[+ ]/ { print f":"ln; ln++ }
  inhunk && /^-/ { next }
  /^diff |^index |^--- / { inhunk=0 }
' /tmp/argus_diff.patch | sort -u > /tmp/argus_commentable.txt
```

For each kept finding:
1. If `path:line` ∈ commentable set → inline comment.
2. Else if another changed line of the same hunk is close (±3) → snap `line` to it and keep inline (note the snap in the body).
3. Else → off-diff: move **that one finding** into the summary body bullet list. Do not move the others.

## Build the review payload

Map each anchored finding to a comment object: `path`, `line`, `side: "RIGHT"`, `body`. For a multi-line finding add `start_line` + `start_side: "RIGHT"` (start) alongside `line` (end). Compose one review, `event: "COMMENT"`:

```json
{
  "commit_id": "<HEAD_SHA>",
  "event": "COMMENT",
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

- **Comment body convention:** `**[severity] section** — <evidence>. <recommendation>`. Evidence + fix only; no preamble.
- **Body when every finding anchored inline:** verdict line + counts table only — omit the "Off-diff" section entirely. Keep it short.

## Avoid duplicate comments on re-runs

The user re-runs Argus on updated branches. Before posting, pull existing review comments and skip findings already commented at the same `path:line`:

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --paginate \
  --jq '.[] | "\(.path):\(.line)"' | sort -u
```

## Post

```bash
gh api "repos/$OWNER_REPO/pulls/$PR/reviews" --method POST --input /tmp/argus_review.json \
  --jq '{id, state, html_url, inline: (.comments|length)}'
```

Confirm `inline` > 0 (unless the only findings were genuinely off-diff). If it is 0 while findings exist, the lines did not anchor — re-check line-validation before falling back to the body.

## Failure handling

- **422 "line must be part of the diff"** on the whole request — one or more `comments[]` lines are off-diff. Identify the offending comment(s), move **only those** into the summary `body` bullet list, keep the rest inline, and re-post. Never drop a finding silently; never collapse all findings into the body because one failed.
- **403 / not a collaborator** — surface to the user; they may need to post under their own auth.
- **Wrong PR / branch mismatch** — re-resolve `PR` and `HEAD_SHA`; never post to a PR the user did not confirm.

## After posting

Report back: PR#, number of **inline** comments posted (broken down by severity, nits included), number folded into the summary body (with why), and the verdict. Keep the local rendered report intact — posting is additive, not a replacement for the report.
