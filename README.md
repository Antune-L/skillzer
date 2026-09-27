# Skillzer

Collection of reusable Markdown instructions for Codex, [Claude Code](https://code.claude.com/docs/en/skills), and other assistants that support `SKILL.md` skills. Individual skills may depend on tools or commands that differ between assistants.

## Structure

```
skillzer/
├── skills/             # Reusable SKILL.md instructions for compatible assistants
├── agents/             # Claude Code agent definitions (.claude/agents)
├── scheduled-tasks/    # Claude Code scheduled task definitions
├── example/            # Ready-to-copy CLAUDE.md template + docs/ structure
└── CLAUDE.md           # Claude Code guide: writing an effective CLAUDE.md
```

## Writing a good CLAUDE.md

The [`CLAUDE.md`](./CLAUDE.md) at the root of this repo is a guide on how to write an effective CLAUDE.md for your projects — philosophy, principles, anti-patterns. The [`example/`](./example/) directory contains a ready-to-copy template with a pre-filled CLAUDE.md and `docs/` structure for a typical TypeScript/React/Node.js project.

## Installation

### Via the `skills` CLI

Install a skill using [skills](https://github.com/vercel-labs/skills). Choose your assistant when the CLI prompts for a target:

```bash
npx skills add Antune-L/skillzer/skills/<skill-name>
```

Available skills:

```bash
npx skills add Antune-L/skillzer/skills/argus-review
npx skills add Antune-L/skillzer/skills/audit-agents-skills
npx skills add Antune-L/skillzer/skills/code-review
npx skills add Antune-L/skillzer/skills/coding-convention
npx skills add Antune-L/skillzer/skills/minos-pr-feedback
npx skills add Antune-L/skillzer/skills/prd
npx skills add Antune-L/skillzer/skills/regression-check
npx skills add Antune-L/skillzer/skills/ts-search-first
```

### Manual

Copy a skill directory, including its `SKILL.md` and supporting files, to the location your assistant reads. [Codex](https://learn.chatgpt.com/docs/build-skills) reads personal skills from `~/.agents/skills/` and repository skills from `.agents/skills/`. [Claude Code](https://code.claude.com/docs/en/skills) reads personal skills from `~/.claude/skills/` and repository skills from `.claude/skills/`. Check the documentation for other assistants before choosing a destination.

The `agents/`, `scheduled-tasks/`, and `CLAUDE.md` examples use Claude Code conventions; they are not portable skill definitions.

## Creating your own skills

The skills in this repo are meant to be forked and adapted. The more a skill is specific to your project's stack and patterns, the more powerful it becomes. For example, a generic "pagination" skill is useful — but one that describes exactly how your TanStack Table talks to your backend (query params, API response shape, filters, Prisma query) turns a 30-minute task into a 2-minute prompt.

**Always audit new or modified skills** with the `audit-agents-skills` skill before committing.

See [`CLAUDE.md`](./CLAUDE.md) for more on writing effective skills and project configuration.

## References

- **prd** was enhanced by [Westerbay](https://github.com/Westerbay). Thank you for the contribution!
- **audit-agents-skills** is built on top of [claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) combined with best practices shared by [an Anthropic engineer](https://x.com/trq212/status/2033949937936085378).
- **architecture-reviewer** is adapted from a [claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) template (`examples/agents/`).

## Other recommended skills

Skills we use but that aren't included in this repo — install them separately:

- **simplifier** (Claude official) — simplifies and refines code for clarity and maintainability while preserving functionality. Run it after every coding session.
- **autofix-pr** (Claude official) — automatically fixes common issues in pull requests. Run it before merging.
- **systematic-debugging** (Claude official) — structured root cause analysis with defense-in-depth strategies. Use when a bug resists the first fix attempt.
- **[vercel-react-best-practices](https://github.com/nichochar/vercel-react-best-practices)** — 47 performance rules for React/Next.js (rendering, caching, bundle size, async patterns).
- **[grill-me](https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me)** (Matt Pocock) — grills you with questions to test your understanding of a topic. Great for learning and interview prep.
- **[remotion](https://www.remotion.dev/docs/ai/skills)** (Remotion official) — best practices for creating videos programmatically with React, so a coding agent can build and render videos.

## Tips to Supercharge Your Claude Code Workflow

- **Save tokens with RTK** — a Rust-based CLI proxy that cuts 60-90% of token usage on dev operations: [rtk-ai/rtk](https://github.com/rtk-ai/rtk)
- **Use git worktrees for parallel work** — built-in to Claude Code (`isolation: "worktree"` on agents), or use [Worktrunk](https://worktrunk.dev/config/) for a managed setup
- **Multitask with CMUX** — a multiplexer designed for Claude Code, run multiple agents side by side: [cmux.com](https://cmux.com/fr)
- **Get notified when Claude finishes** — set up a [hook](https://docs.anthropic.com/en/docs/claude-code/hooks) on task completion, or use CMUX which has notifications built-in
- **Leverage MCP servers** — extend Claude Code with Model Context Protocol servers:
  - [Context7](https://context7.com/) — fetch up-to-date library/framework documentation on the fly
  - [Playwright MCP](https://github.com/microsoft/playwright-mcp) — browser automation for live testing and debugging (see [setup below](#playwright-mcp-setup))
  - [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) — interact with Chrome DevTools directly from Claude
