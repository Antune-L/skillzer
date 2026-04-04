# Writing an effective CLAUDE.md

Prank, it's not the CLAUDE.md you were thinking about..

CLAUDE.md is the first thing Claude reads when entering your project. It shapes every decision the agent makes. Getting it right is the highest-leverage investment you can make for AI-assisted development.

## Philosophy: table of contents, not encyclopedia

The key insight from [OpenAI's Harness Engineering](https://openai.com/index/harness-engineering/) team: they tried the "one big AGENTS.md" approach. It failed.

- **Context is a precious resource.** A huge instruction file crowds out the actual task, code, and relevant docs. The agent misses critical constraints or starts optimizing the wrong thing.
- **Too much guidance loses its utility.** When everything is "important", nothing is. The agent pattern-matches locally instead of navigating intentionally.
- **A monolithic manual rots immediately.** Agents can't tell what's still valid, humans stop updating it, and the file gradually becomes a liability.
- **It's hard to verify.** A single blob doesn't lend itself to mechanical checks (coverage, freshness, ownership, cross-links), so drift is inevitable.

Instead, treat CLAUDE.md as **the table of contents**. The actual knowledge base lives in `docs/`, skills, and references. CLAUDE.md is a short (~100 lines) map that tells the agent where to look next.

## Core principles

### 1. Be a map, not a manual

Point to deeper docs instead of inlining everything. This is **progressive disclosure**: Claude starts with a narrow, stable entry point and follows pointers when needed.

```markdown
## Documentation Index

| Topic                | File                       | Load when...             |
| -------------------- | -------------------------- | ------------------------ |
| Frontend conventions | `docs/FRONTEND.md`         | Working on frontend code |
| Backend conventions  | `docs/BACKEND.md`          | Working on backend code  |
| Regression zones     | `docs/regression-zones.md` | Touching risky areas     |
```

### 2. Enforce invariants, not implementations

State the constraint, not the micro-steps. Let Claude pick the approach.

```markdown
<!-- Good: constraint -->

- Validate data shapes at boundaries with Zod

<!-- Bad: micro-managing -->

- Import z from 'zod', create a schema with z.object(), call .parse() on the input,
  wrap it in a try/catch, return a 400 if it fails...
```

### 3. What Claude can't see doesn't exist

Knowledge in Slack threads, Google Docs, or people's heads is invisible to the agent. If it matters for implementation decisions, encode it in the repo — as markdown, code comments, or design docs.

### 4. Keep it alive

A stale CLAUDE.md is worse than none. If a rule no longer holds, remove it. If docs drift from code, the code wins. Review it periodically — or better, automate freshness checks.

## Recommended structure

```
CLAUDE.md                    # ~100 lines, the map
docs/
├── FRONTEND.md              # Frontend conventions (loaded on demand)
├── BACKEND.md               # Backend conventions (loaded on demand)
├── regression-zones.md      # High-risk areas to read before touching
└── ...
```

### What belongs in CLAUDE.md

- **Project overview** — what this is, tech stack, structure (2-3 lines)
- **Essential commands** — dev, lint, build, test (the 4 you always need)
- **Coding conventions** — the non-negotiable rules (naming, imports, no type casting...)
- **Workflow** — what to do before/after coding (analysis, regression check, lint)
- **Do Not** — hard lines (no strict disable, no secrets in commits)
- **Documentation Index** — pointers to deeper docs with "load when..." triggers
- **Skills & Commands** — available skills and when to invoke them
- **Golden Rule** — the one rule that trumps everything else

### What does NOT belong in CLAUDE.md

- Full API documentation — put in `docs/` or use context7 MCP
- Exhaustive code examples — put in skill `references/`
- Project-specific business logic — put in `docs/` or design docs
- Debugging recipes — the fix is in the code, the context is in the commit message
- Anything that changes weekly — it will go stale

## Writing your own skills

Skills are where the real leverage is. A generic skill is useful, but a **project-specific skill is powerful** — the more precise it is about your stack and patterns, the better Claude performs.

For example, instead of a generic "pagination" skill, write one that describes exactly how your TanStack Table connects to your backend: what query params the frontend sends, what shape the API response returns (`rows`, `rowCount`, `pageCount`), how filters are serialized, and what the Prisma query looks like. That level of specificity turns a 30-minute task into a 2-minute prompt.

Don't hesitate to fork and adapt the skills in this repo to your project's context. The closer a skill maps to your actual patterns, the less Claude has to guess.

**Always run the `audit-agents-skills` skill on any new or modified skill before committing.** It catches structural issues, missing sections, and quality gaps.

## Anti-patterns

| Anti-pattern                    | Why it fails                         | Fix                                               |
| ------------------------------- | ------------------------------------ | ------------------------------------------------- |
| 500-line CLAUDE.md              | Crowds out the actual task context   | Split into CLAUDE.md + `docs/`                    |
| Copy-paste from another project | Irrelevant rules confuse the agent   | Start minimal, add rules as needed                |
| Rules without "why"             | Agent can't judge edge cases         | Add brief rationale inline                        |
| Duplicating linter rules        | Double maintenance, inevitable drift | Let the linter enforce, don't repeat in CLAUDE.md |
| Never updating                  | Stale rules become actively harmful  | Review quarterly or after major refactors         |

## Example

See [`example/`](./example/) for a ready-to-copy template with a CLAUDE.md, docs structure, and filled-in conventions for a typical TypeScript/React/Node.js project.
Mind it's not perfect, it's an example !
