---
name: audit-agents-skills
description: "Audit Claude Code agents, skills, and commands for quality and production readiness. Use when evaluating skill quality, checking production readiness scores, or comparing agents against best-practice templates."
---

# Audit Agents/Skills/Commands

Quality audit for Claude Code agents, skills, and commands. Scores each file against best practices from [SKILLS-BEST-PRACTICES.md](./SKILLS-BEST-PRACTICES.md) and the detailed criteria in [scoring/criteria.yaml](./scoring/criteria.yaml).

## Workflow

### Phase 1: Discovery

Scan these directories for agents/skills/commands:

```
.claude/agents/
.claude/skills/
.claude/commands/
```

Classify each file by type (agent/skill/command).

### Phase 2: Audit

Read [SKILLS-BEST-PRACTICES.md](./SKILLS-BEST-PRACTICES.md) first — it defines the qualitative standard. Then for each file, check every criterion from [scoring/criteria.yaml](./scoring/criteria.yaml) plus the Anthropic best practices checklist below.

#### Anthropic Best Practices Checklist

These checks come directly from Anthropic's internal learnings and MUST be applied on top of the scoring criteria:

| Check | What to look for | Why it matters |
|-------|-----------------|----------------|
| **Description = trigger, short** | Description is concise (1-2 sentences), tells the model WHEN to activate — not a summary of what the skill does. Optimized for token budget: always loaded in context for every session | Verbose descriptions waste context tokens and dilute trigger signal. If the model can't trigger it or drowns in noise, the skill is dead |
| **Gotchas section** | Has a `## Gotchas` section with real failure cases | Highest-signal content per Anthropic — captures what Claude gets wrong |
| **Progressive disclosure** | Uses subfiles/folders instead of one massive SKILL.md | Keeps context lean; Claude reads subfiles on demand |
| **Don't state the obvious** | Focuses on non-default knowledge Claude wouldn't know | Wasted tokens if it just says "write clean code" |
| **Don't railroad** | Gives info + flexibility, not rigid step-by-step scripts | Claude needs room to adapt to the situation |
| **Single category** | Fits cleanly into one of the 9 types (Library, Verification, Data, Business, Scaffold, Quality, CI/CD, Runbook, Infra) | Confused skills that straddle categories are hard to trigger and maintain |
| **Name = directory** | Frontmatter `name` matches the directory name | Mismatch causes invocation confusion |
| **Composable** | References other skills it depends on or works with | Skills should compose, not duplicate |
| **No hardcoded paths** | No `/Users/`, `/home/`, `C:\` | Breaks portability |
| **Reasonable size** | SKILL.md alone < ~200 lines / < 5K tokens. Reference subfiles do NOT count against this — that is progressive disclosure working as intended (a 130-line SKILL.md + 600 lines of references is conform) | Context budget is finite; only SKILL.md is always loaded |

### Phase 2.5: Usage audit (when transcripts exist — highest-signal phase)

A skill can score A statically and still generate friction at every use. When session transcripts
exist (`~/.claude/projects/<project-dir>/*.jsonl`), mine them for how the skill behaves **in
practice** and weigh that into the grade.

Per audited skill (run in a subagent — transcripts are large, never read whole files):

```bash
# 1. sessions that actually INVOKED the skill — a plain name grep over-matches
#    (the available-skills list is embedded in every transcript)
grep -l -E '"skill": ?"<skill-name>"|<command-name>/<skill-name>' ~/.claude/projects/<dir>/*.jsonl
# spot-check one hit before counting it as a usage session

# 2. real user messages (the friction story: initial ask, then every correction/re-prompt)
jq -r 'select(.type=="user" and (.message.content|type)=="string") | .message.content' FILE.jsonl
jq -r 'select(.type=="user" and (.message.content|type)=="array") | .message.content[] | select(.type=="text") | .text' FILE.jsonl
```

Friction signals to count:
- **Corrections after skill output** ("non", "plutôt", "tu as raté", "attention", "refais") — the skill's defaults are wrong.
- **Repeated instructions across sessions** — anything the user must say every time belongs in the skill (gotcha or default).
- **Immediate re-invocations** (same skill, ≤2 messages apart) — the first run missed context (args, base, PR#).
- **Manual follow-up steps** after every run — a missing chaining/handoff.

Report per skill: sessions used · friction incidents (short verbatim quote each) · recurring
patterns (2+ sessions) → each pattern maps to a concrete fix recommendation in Phase 4. A
recurring unfixed friction caps the grade at **C** regardless of static score.

### Phase 3: Report

For each file, output:

```
### <file path>
- **Type**: agent / skill / command
- **Category**: (one of the 9 types, or "unclear")
- **Score**: X/32 (or X/20 for commands)
- **Grade**: A/B/C/D/F
- **Issues**: (list each failed criterion with 1-line fix suggestion)
- **Usage**: (Phase 2.5 — sessions used · friction incidents with verbatim quote · recurring patterns; "n/a" when no transcripts)
- **Best Practices**: (pass/fail for each Anthropic checklist item)
```

Then a summary table:

```
| File | Type | Score | Grade | Top Issue |
|------|------|-------|-------|-----------|
```

### Phase 4: Recommendations

Prioritize by impact:
1. **Critical** — skill is broken or untriggerable
2. **High** — missing gotchas, wrong description, massive size
3. **Low** — minor: missing examples, no composition references

## Grading

| Grade | Range | Meaning |
|-------|-------|---------|
| A | 90-100% | Production-ready |
| B | 80-89% | Good, meets threshold |
| C | 70-79% | Needs work |
| D | 60-69% | Significant gaps |
| F | <60% | Major rewrite needed |

Production threshold: **80% (Grade B)**.

**Usage cap (overrides the table):** a recurring unfixed friction from Phase 2.5 caps the final
grade at **C** — report it as `A→C (usage cap)` so the static score stays visible.

## Gotchas

- **`grep -l '<skill-name>'` over transcripts detects mentions, not usage.** The available-skills
  listing is embedded in every session file, so a plain name grep matches nearly every transcript
  (verified: identical hit counts for used and never-used skills). Grep an invocation-specific
  pattern and spot-check a hit before counting it.
- **The grade cap is easy to drop on aggregation.** Grade is `min(score grade, usage cap)` — an
  auditor reading only the Grading table will award A/B to a skill the usage data says is C.
