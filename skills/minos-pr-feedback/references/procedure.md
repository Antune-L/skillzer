# Inbound — fetch, triage and apply reviewer comments

The user has feedback on a PR (from a human reviewer or a bot like `gemini-code-assist`) and wants the **pertinent** items fixed — nits dropped. This is the step they otherwise do by hand on nearly every PR.

## 1. Resolve the PR

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
PR=$(gh pr view --json number -q .number)   # current branch; or pass the explicit number
```

Any `gh` call below can fail auth on a private repo: **401/403 → tell the user to `gh auth login` / check repo access; never fabricate an empty result** (an empty fetch reads as "no comments" and silently drops real feedback).

## 2. Fetch all three comment sources

GitHub stores PR feedback in **three separate APIs**. Fetching only one silently drops feedback.

```bash
# (a) inline review comments — anchored at file:line, this is where most real findings live
gh api "repos/$OWNER_REPO/pulls/$PR/comments" --paginate --jq '
  .[] | {id, user: .user.login, path, line, original_line,
         in_reply_to: .in_reply_to_id, outdated: (.position == null), body}'

# (b) review summaries + verdict state (bots post their overview here: APPROVED / COMMENTED / CHANGES_REQUESTED)
gh api "repos/$OWNER_REPO/pulls/$PR/reviews" --paginate --jq '
  .[] | select(.body != "") | {id, user: .user.login, state, body}'

# (c) top-level conversation comments (issue comments — humans often drop high-level notes here)
gh api "repos/$OWNER_REPO/issues/$PR/comments" --paginate --jq '
  .[] | {id, user: .user.login, body}'
```

Notes:
- `position == null` on an inline comment ⇒ the line is **outdated** (the diff moved past it) — usually already addressed; down-weight or skip.
- `in_reply_to_id` set ⇒ part of a thread; read the whole thread before judging (a later reply may resolve it).
- To detect **resolved** threads (not exposed by the REST inline endpoint), use the GraphQL review-thread query when resolution matters:

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$pr:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$pr){
        reviewThreads(first:100){ nodes {
          isResolved isOutdated
          comments(first:20){ nodes { author{login} path line body } }
        }}}}}' \
  -F owner="${OWNER_REPO%/*}" -F repo="${OWNER_REPO#*/}" -F pr="$PR"
```

Skip threads where `isResolved == true`.

## 3. Filter noise before triage

Drop, without counting them as findings:
- comments authored by the user themselves,
- resolved threads (`isResolved`) and outdated lines (`position: null` / `isOutdated`),
- pure acknowledgements ("LGTM", 👍, "thanks").

## 4. Triage rubric

Classify every surviving comment into exactly one bucket, each with a one-line reason:

| Verdict | Meaning | Action |
| --- | --- | --- |
| **apply** | Correct + relevant: real bug, regression, security/perf issue, convention violation, or a clearly-better approach. | Fix it. |
| **skip-nit** | Style/preference/bikeshed with no correctness impact (naming taste, optional refactor, "consider…"). | Skip unless the user asked for nits. |
| **skip-wrong** | Incorrect, based on a misread, out-of-scope for this PR, or already handled elsewhere. | Skip; note the reason (useful if the user wants to reply). |

Standing defaults (the user's repeated instructions):
- **"ce qui est pertinent"** → apply the `apply` set only.
- **"pas les nit"** → `skip-nit` is the default; never apply nits unless told.
- **Bots (`gemini-code-assist`, `coderabbitai`) are nitty** — they pad a few real findings with many style nits and speculative suggestions. Judge each on merits; a bot's confident tone is not evidence. Expect most bot comments to land in `skip-nit`.

## 5. Present, then apply

1. **Print the triage table first** — `author · path:line · verdict · one-line reason` — so the user sees the call on each comment.
2. **Apply the `apply` set** as real code changes:
   - group related fixes, smallest diff,
   - reuse existing project components/patterns (don't reinvent),
   - respect conventions (no `as` casts, naming, import order),
   - **check regressions** on any changed symbol and run typecheck/lint on touched files.
3. **Do not auto-reply or resolve threads** — standing instruction: "pas besoin de répondre, applique ce qui te semble pertinent". Only post replies if explicitly asked; then reply per-thread via `gh api repos/$OWNER_REPO/pulls/$PR/comments/<id>/replies`.

## 6. Commit and push the applied fixes

The user opted into committing for this workflow — updating the PR is the point. Run this **only after** regressions + typecheck/lint pass, and **only if at least one fix was applied** (an all-skipped run has nothing to commit).

- **Stage only what minos touched.** Never `git add -A` / `git add .` — the working tree may hold unrelated changes. Stage the exact files from the `apply` set:

  ```bash
  git add <file1> <file2> ...        # only the files minos modified
  ```

- **Commit** with a conventional message summarizing the addressed feedback:

  ```bash
  git commit -m "fix: address PR review feedback"
  # more specific is better when the fixes share a theme:
  # git commit -m "fix: handle null user in reviews-section per review"
  ```

- **Push to the PR's head branch** so the PR updates automatically:

  ```bash
  git push
  ```

  Push **only when the checked-out branch IS the PR's head**. If they differ (detached HEAD, or minos ran against a named branch that isn't checked out), do **not** push blind — flag it and let the user push.

- **Checks gate the commit.** If typecheck / lint / regression surfaced a failure, stop before committing and report it — never push a broken tree.
- **Committing is not a substitute for review.** Still flag any non-trivial or risky fix prominently in the report so the user can inspect — and amend or revert — the pushed commit.

## 7. Report back

- Applied: each fix at `file:line` with the comment it answers.
- Skipped: grouped by `skip-nit` / `skip-wrong` with the one-line reason.
- Counts: N applied, M nits skipped, K out-of-scope/wrong.
- **Commit + push**: the pushed commit sha and branch (or why nothing was pushed — all skipped / check failed / branch mismatch).
- If any `apply` fix is non-trivial or risky, flag it prominently so the user reviews the pushed commit.
