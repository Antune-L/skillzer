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
- **Always also run the GraphQL review-thread query** — the REST inline endpoint does NOT expose
  thread resolution, so skipping this step silently disables the "skip resolved threads" filter.
  The thread `id` and comment `databaseId` fetched here are also what §7 needs to resolve threads —
  keep the mapping REST comment id → thread id:

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$pr:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$pr){
        reviewThreads(first:100){ nodes {
          id isResolved isOutdated
          comments(first:20){ nodes { databaseId author{login} path line body } }
        }}}}}' \
  -F owner="${OWNER_REPO%/*}" -F repo="${OWNER_REPO#*/}" -F pr="$PR"
```

Skip threads where `isResolved == true`. More than 100 threads → paginate with `reviewThreads(first:100, after:$cursor)`.

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
| **ask** | Would change runtime behavior (who sees what, permissions, returned data) but cannot be validated against stated intent — hedged phrasing, speculative edge case, or no PR description to anchor intent. | Never touch code; surface as a question in the triage table for the user to decide. |
| **skip-nit** | Style/preference/bikeshed with no correctness impact (naming taste, optional refactor, "consider…"). | Skip unless the user asked for nits. |
| **skip-wrong** | Incorrect, based on a misread, out-of-scope for this PR, or already handled elsewhere. | Skip; note the reason (useful if the user wants to reply). |

Standing defaults (the user's repeated instructions):
- **"ce qui est pertinent"** → apply the `apply` set only.
- **"pas les nit"** → `skip-nit` is the default; never apply nits unless told.
- **Bots (`gemini-code-assist`, `coderabbitai`) are nitty** — they pad a few real findings with many style nits and speculative suggestions. Judge each on merits; a bot's confident tone is not evidence. Expect most bot comments to land in `skip-nit`.
- **Hedged behavioral findings are never auto-applied.** "Consider gating…", "flagging for confirmation", a speculative edge-case scenario: when the proposed fix changes runtime behavior and the PR description states no intent to validate it against (`gh pr view "$PR" --json body` — empty body = no anchor), the verdict is `ask`, never `apply` (fftir #327: hedged banner-visibility warning auto-applied, then rolled back as slop).
- **Verify claimed regressions against pre-PR behavior.** Before applying a comment claiming "X will now happen", check the base version of the exact call site (`git show origin/<base>:<file>` or the PR diff context). If the behavior already existed pre-PR, or the cited invariant comes from a sibling code path (a hook/helper not used at the changed call site), it's `skip-wrong` (fftir #327: "admins will now see the banner" — they already did; the invariant lived in a hook the banner never used).

**Consult the rejected-patterns memory** ([`rejected-patterns.md`](rejected-patterns.md)) before
triaging: a comment matching a listed pattern defaults to its recorded verdict (still overridable
on strong evidence). After the run, if a *class* of comment was skipped for the same reason on
this PR and at least one earlier PR, append it to the file — one line: pattern → verdict → reason.
Never log one-off skips; only recurring classes.

## 5. Present, then apply

1. **Print the triage table first** — `author · path:line · verdict · one-line reason` — so the user sees the call on each comment. For each `ask` item, state the question and the option you would take; the user decides — nothing is applied for it this run.
2. **Apply the `apply` set** as real code changes:
   - group related fixes, smallest diff,
   - reuse existing project components/patterns (don't reinvent),
   - respect conventions (no `as` casts, naming, import order),
   - **check regressions** on any changed symbol and run typecheck/lint on touched files.
3. **Thread resolution happens in §7, after the push** — the replies cite the commit sha, so
   resolving before pushing would reference a sha that doesn't exist yet.

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

## 7. Resolve every triaged thread (default)

Close the loop on GitHub so the user keeps a global view of what remains open. **Every triaged
inline thread gets a one-line reply** — the invariant is: open thread WITH a minos reply = awaiting
the user's decision; open thread WITHOUT a reply = not triaged (e.g. posted after the run). Threads
with a final verdict (`apply` / `skip-nit` / `skip-wrong`) are then resolved; `ask` threads stay
open. Opt out if the user said `--no-resolve` / "ne résous pas les threads", **or** if the caller
(e.g. an orchestrator ticket) explicitly forbids posting comments — then close threads with the
caller's mechanism instead (typically GraphQL `minimizeComment`) and report per-thread verdicts in
the run report.

- Reply body per verdict — one line, factual, no debate:
  - **apply** → `Fixed in <sha>.` — then resolve.
  - **skip-nit** → `Skipped: nit — <one-line reason from the triage table>.` — then resolve.
  - **skip-wrong** → `Not applied: <one-line reason from the triage table>.` — then resolve.
  - **ask** → `Awaiting decision from the author: <one-line question>. Left open on purpose.` —
    reply but do **NOT** resolve. Without this reply the user cannot tell an ask thread from an
    untriaged one when scanning the PR.

  ```bash
  gh api "repos/$OWNER_REPO/pulls/$PR/comments/<comment_id>/replies" -f body="Fixed in <sha>."
  ```

- Then resolve, using the thread `id` from the §2 GraphQL query (map via the comment's `databaseId`):

  ```bash
  gh api graphql -f query='
    mutation($thread:ID!){
      resolveReviewThread(input:{threadId:$thread}){ thread { isResolved } }
    }' -F thread="<thread_id>"
  ```

- Scope limits:
  - **Only inline review threads are resolvable.** Review summaries (§2b) and issue comments (§2c)
    have no resolve concept — never reply to them, they are triaged but left as-is.
  - Threads dropped in §3 as already resolved get nothing. Threads skipped as outdated/superseded
    ARE resolved, with `Obsolete: <reason>.` as the reply.
  - If the run stopped before pushing (check failed, all skipped with nothing to commit), still
    resolve the skip threads — only the `apply` replies depend on a pushed sha.

## 8. Report back

- Applied: each fix at `file:line` with the comment it answers.
- Ask: open questions awaiting the user's call, each with the option you would take.
- Skipped: grouped by `skip-nit` / `skip-wrong` with the one-line reason.
- Counts: N applied, Q asked, M nits skipped, K out-of-scope/wrong, R threads resolved, A ask
  threads replied-but-left-open (+ any thread that failed to reply/resolve, with the error).
- **Zero-silent-threads check**: confirm every triaged inline thread got a reply. Any thread left
  open without one is a bug in the run — list it explicitly.
- **Commit + push**: the pushed commit sha and branch (or why nothing was pushed — all skipped / check failed / branch mismatch).
- If any `apply` fix is non-trivial or risky, flag it prominently so the user reviews the pushed commit.
