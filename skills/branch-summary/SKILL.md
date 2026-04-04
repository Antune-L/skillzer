---
name: branch-summary
description: Summarizes commits and changes made on the current branch compared to its parent branch. Outputs a concise bullet-point list in English. This skill should be used when the user wants a quick overview of what was done on a branch (e.g. "what did I do on this branch?", "summarize this branch", "what changed since main?").
---

## Workflow

### 1. Detect base branch and gather data

Run these commands in parallel to collect branch information:

```bash
# Find base branch (try common names)
git rev-parse --verify main 2>/dev/null && echo "main" || \
  git rev-parse --verify master 2>/dev/null && echo "master" || \
  git rev-parse --verify develop 2>/dev/null && echo "develop" || \
  echo "HEAD~1"

# List commits on current branch vs base
git log --oneline <base>..HEAD

# Get changed files summary
git diff --stat <base>...HEAD
```

### 2. Build the summary

Produce a bullet-point list in English. Keep it short and concise — one bullet per logical change or commit group. Focus on **what** changed and **why**, not implementation details.

Rules:
- English only
- Bullet points (`-`)
- Max ~10 bullets, merge related commits into one point
- No file-level details unless they are the key change
- No code snippets

### Example output

```
- Added user authentication with JWT tokens
- Refactored database connection pooling for better performance
- Fixed crash on empty search results
- Updated API endpoints to v2 format
- Added unit tests for the payment module
```
