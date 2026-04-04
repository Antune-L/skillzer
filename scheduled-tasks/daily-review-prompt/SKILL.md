---
name: daily-review-prompt
description: Review the last 24h of conversations and suggest improvements to CLAUDE.md, skills, and gotchas sections.
---

# Daily Review

Analyze recent work sessions to identify friction points, missing context, and improvement opportunities for the developer experience.

## Data Sources

Gather context from these sources (in order of priority):

1. **Git history** — `git log --since="24 hours ago" --all --oneline` across active projects
2. **Memory files** — recent entries in `~/.claude/projects/*/memory/`
3. **CLAUDE.md files** — current state of global (`~/.claude/CLAUDE.md`) and per-project CLAUDE.md
4. **Existing skills** — scan `~/.claude/skills/` and `~/.claude/scheduled-tasks/` for what already exists

## Workflow

### Phase 1: Gather

- Read git history and memory files to understand what was worked on
- Identify patterns: repeated questions, back-and-forth loops, manual steps that could be automated

### Phase 2: Analyze

For each friction point, classify it:

| Type | Action |
|------|--------|
| Missing context Claude needed | → CLAUDE.md update |
| Repeated workflow pattern | → New skill candidate |
| Existing skill that failed or was awkward | → Gotcha addition to that skill |
| Project-specific convention | → Project CLAUDE.md update |

### Phase 3: Report

Output a structured report — **do not apply changes**, only propose them.

## Output Format

```markdown
## Summary
<!-- 2-3 sentence overview of what was worked on -->

## CLAUDE.md Changes
<!-- For each proposed change: what to add/modify and why -->
- **File**: `~/.claude/CLAUDE.md` or project-specific path
- **Change**: what to add or modify
- **Why**: what friction this would have prevented

## Skill Improvements
<!-- Gotchas to add to existing skills -->
- **Skill**: `<skill-name>`
- **Gotcha**: description of the failure/friction
- **Suggested addition**: text to add to ## Gotchas

## New Skills to Create
<!-- Only if a clear repeated pattern emerged -->
- **Name**: proposed skill name
- **Category**: one of Library/Verification/Data/Business/Scaffold/Quality/CI-CD/Runbook/Infra
- **Justification**: what repeated pattern this would address

## No Action Needed
<!-- Explicitly state if nothing worth changing was found — don't invent busywork -->
```

## Composable Skills

- Use `skill-creator` if a new skill is approved for creation
- Use `audit-agents-skills` to validate any skill changes meet quality bar
- Reference `coding-convention` for code-related CLAUDE.md suggestions

## Gotchas

- **Don't invent busywork** — if nothing meaningful emerged in 24h, say so. Not every day produces improvements
- **Check before suggesting new skills** — always scan `~/.claude/skills/` first to avoid duplicating existing ones
- **Git history may be sparse** — if the user worked in repos you can't access, the review will be incomplete. Acknowledge gaps
- **Don't modify files** — this skill is read-only. Propose changes, let the user decide what to apply
- **Memory ≠ current state** — memory files can be stale. Cross-check with actual file contents before recommending based on memory
