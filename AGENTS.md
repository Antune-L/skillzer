# Writing an effective AGENTS.md

Use AGENTS.md as a short, shared entry point for coding agents working in a repository. Include only guidance that applies across assistants; keep tool-specific instructions in their own files, such as [CLAUDE.md](./CLAUDE.md).

## What to include

- A brief project purpose and a map to the directories agents will need.
- Essential setup, build, lint, and test commands verified against the repository.
- Stable constraints that affect implementation decisions, with a short reason when it helps.
- Links to deeper documentation for topics that matter only to some tasks.

## Keep it useful

Prefer concrete, verifiable instructions over broad advice. Keep paths and commands current as the project changes. Move long procedures and examples to focused documentation or skills, so the entry point stays easy to scan.

When a project also has a CLAUDE.md, put shared guidance in AGENTS.md and import it with `@AGENTS.md` from CLAUDE.md. The [Claude Code guide](./CLAUDE.md) covers the Claude-specific file in more detail.
