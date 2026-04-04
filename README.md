# Skillzer

Collection of reusable skills, agents, and scheduled tasks for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Structure

```
skillzer/
├── skills/             # Reusable skill definitions (.claude/skills)
├── agents/             # Custom agent definitions (.claude/agents)
├── scheduled-tasks/    # Scheduled task definitions (.claude/scheduled-tasks)
├── example/            # Ready-to-copy CLAUDE.md template + docs/ structure
└── CLAUDE.md           # Guide: how to write an effective CLAUDE.md
```

## Writing a good CLAUDE.md

The [`CLAUDE.md`](./CLAUDE.md) at the root of this repo is a guide on how to write an effective CLAUDE.md for your projects — philosophy, principles, anti-patterns. The [`example/`](./example/) directory contains a ready-to-copy template with a pre-filled CLAUDE.md and `docs/` structure for a typical TypeScript/React/Node.js project.

## Usage

Copy or symlink the desired items into your `~/.claude/` directory:

```bash
# Skills
cp -R skillzer/skills/my-skill ~/.claude/skills/

# Agents
cp skillzer/agents/my-agent.md ~/.claude/agents/

# Scheduled tasks
cp -R skillzer/scheduled-tasks/my-task ~/.claude/scheduled-tasks/
```

## Creating your own skills

The skills in this repo are meant to be forked and adapted. The more a skill is specific to your project's stack and patterns, the more powerful it becomes. For example, a generic "pagination" skill is useful — but one that describes exactly how your TanStack Table talks to your backend (query params, API response shape, filters, Prisma query) turns a 30-minute task into a 2-minute prompt.

**Always audit new or modified skills** with the `audit-agents-skills` skill before committing.

See [`CLAUDE.md`](./CLAUDE.md) for more on writing effective skills and project configuration.

## References

- **audit-agents-skills** is built on top of [claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) combined with best practices shared by [an Anthropic engineer](https://x.com/trq212/status/2033949937936085378).
- **architecture-reviewer** and **smart-explore** are adapted from [claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) templates (`examples/agents/` and `examples/skills/`).

## Other recommended skills

Skills we use but that aren't included in this repo — install them separately:

- **[simplifier](https://github.com/anthropics/claude-code/tree/main/plugins/official/code-simplifier)** (Claude official) — simplifies and refines code for clarity and maintainability while preserving functionality. Run it after every coding session.
- **[systematic-debugging](https://github.com/anthropics/claude-code/tree/main/plugins/official/systematic-debugging)** (Claude official) — structured root cause analysis with defense-in-depth strategies. Use when a bug resists the first fix attempt.
- **[vercel-react-best-practices](https://github.com/nichochar/vercel-react-best-practices)** — 47 performance rules for React/Next.js (rendering, caching, bundle size, async patterns).

## Tips to Supercharge Your Claude Code Workflow

- **Save tokens with RTK** — a Rust-based CLI proxy that cuts 60-90% of token usage on dev operations: [rtk-ai/rtk](https://github.com/rtk-ai/rtk)
- **Use git worktrees for parallel work** — built-in to Claude Code (`isolation: "worktree"` on agents), or use [Worktrunk](https://worktrunk.dev/config/) for a managed setup
- **Multitask with CMUX** — a multiplexer designed for Claude Code, run multiple agents side by side: [cmux.com](https://cmux.com/fr)
- **Get notified when Claude finishes** — set up a [hook](https://docs.anthropic.com/en/docs/claude-code/hooks) on task completion, or use CMUX which has notifications built-in
- **Leverage MCP servers** — extend Claude Code with Model Context Protocol servers:
  - [Context7](https://context7.com/) — fetch up-to-date library/framework documentation on the fly
  - [Playwright MCP](https://playwright.dev/docs/getting-started-mcp) — browser automation for testing and debugging
  - [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) — interact with Chrome DevTools directly from Claude
