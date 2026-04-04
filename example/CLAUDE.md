## Communication

- Sacrifice grammar to stay concise
- If you don't know, say it — do not hallucinate
- List all unresolved questions (if any) at the end

## Project Overview

<!-- Replace with your project description -->
[Project name] — [one-line description]. [Monorepo / single-app] with [pnpm / npm].

## Essential Commands

```bash
pnpm dev                      # Start dev server
pnpm lint && pnpm typecheck   # Pre-commit (mandatory)
pnpm build                    # Production build
pnpm test                     # Run tests
```

## Conventions

- Follow the `coding-convention` skill
- Comments in English only, no obvious comments
- Use `TODO(ME)` prefix for tasks to track (FIXME, NOTE, etc.)
- **Reuse before creating** — search the codebase before writing new code

## Workflow

- Before coding, analyze the problem to confirm the approach
- After coding, check for regressions, run the `simplifier` skill
- After coding, run typecheck + lint + tests. Fix with minimal diff
- Root cause analysis first when debugging — no band-aid fixes
- When encountering pitfalls, update the Gotchas section of the relevant skill
- Don't implement tests unless explicitly asked

## Git

- **Format**: `[type]: [message]` (feat, fix, docs, refactor, test, chore)
- **Branches**: `feature/`, `fix/`, `hotfix/`

## Do Not

- Disable TypeScript strict checks
- Skip lint + typecheck before commits
- Commit secrets, API keys, or sensitive data

## Documentation Index

| Topic | File | Load when... |
|-------|------|-------------|
| TypeScript & coding rules | `docs/TYPESCRIPT.md` | Writing any TS code |
| Frontend conventions | `docs/FRONTEND.md` | Working on React/UI |
| Backend conventions | `docs/BACKEND.md` | Working on API/server |
| Regression zones | `docs/regression-zones.md` | Touching risky areas |

## Skills

<!-- List your project-specific skills -->
| Skill | Use when... |
|-------|-------------|
| `coding-convention` | Writing any code |
| `vercel-react-best-practices` | Writing React components |

## Tools

- Use the context7 MCP to look up documentation

## Golden Rule

**When unsure about implementation details, database schema changes, business logic, or architectural decisions, ALWAYS ask the developer before making assumptions.**
