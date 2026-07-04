---
name: regression-check
description: >
  After modifying code, map all consumers of changed symbols and flag unhandled mismatches.
  Not for debugging (use systematic-debugging).
---

# Regression Check

Proactive analysis to catch regressions BEFORE they happen. Run AFTER modifying code,
BEFORE committing. Maps the blast radius of changes and flags unhandled consumers.

## When to Trigger

- After modifying any exported function, type, interface, or API endpoint
- After renaming/moving files or symbols
- After changing database schema or migrations
- After modifying shared utilities, hooks, or components

**Mandatory (not optional) when a shared-surface file changes.** A shared surface is any file
imported by many features. Detect it per project rather than assuming a layout:

- Typical candidates: `components/ui|form|table|layout`, `hooks/`, `lib/`, `utils/`, shared
  packages (`packages/*` in a monorepo).
- When in doubt, count importers: `grep -rl "from ['\"].*<module>" --include="*.ts*" | wc -l` —
  more than ~3 importers ⇒ treat as shared surface.
- If the project defines its own shared-surface rule (e.g. a `.cursor/rules/*.mdc` or CLAUDE.md
  section), honor it — but never require it to exist.

A one-feature edit to a shared surface is the most common regression source.

## Process

### Phase 1 — Identify What Changed

Collect the list of changed symbols from one of:

- `git diff --name-only` + `git diff` for modified lines
- Session context (files just edited in this conversation)

For each changed file, extract:

- Modified/deleted/renamed **exports** (functions, types, interfaces, constants, classes)
- Changed **function signatures** (params added/removed/retyped, return type changed)
- Changed **field names** in types, DTOs, Zod schemas, Prisma models
- Changed **API contracts** (route paths, request/response shapes)

### Phase 2 — Map the Blast Radius

For each changed symbol, find ALL consumers. Use the most precise source available, in order:

1. **Knowledge graph** — if `graphify-out/graph.json` exists, the dependency edges are already
   computed: `graphify query "who imports/uses <symbol or module>?"` (or `graphify path` between
   the changed module and a suspected consumer). Start here; it catches re-exports and barrel
   files that regex misses.
2. **Compiler / LSP** — exact reference resolution beats text matching:
   - LSP "find references" on the changed symbol when available.
   - Or run the project's typecheck (`tsc --noEmit` / the `typecheck` script from `package.json`)
     after the change — every consumer broken by a signature/shape change surfaces as an error
     with file:line. This is the ground truth for TS projects.
3. **Grep fallback** — only when neither is available, or to catch non-TS references
   (route strings, config, docs):

   ```
   grep -r "import.*{.*symbolName.*}" --include="*.ts" --include="*.tsx"
   grep -r "from ['\"].*changedModule['\"]" --include="*.ts" --include="*.tsx"
   ```

   Regex misses default imports, re-exports, and barrel files (`index.ts` chains) — when using
   this fallback, explicitly check barrels that re-export the changed module.

Trace transitively — if A imports B which imports changed module C, check both A and B.

Be **monorepo-aware**: scan all `apps/`, `packages/`, `libs/` directories, not just the
directory containing the change.

### Phase 3 — Verify Compatibility

For each consumer found, read the relevant lines and verify:

- Field names match the new shape
- Function call arguments match the new signature
- Destructured properties still exist
- Type assertions still hold against the new type
- API request/response handling matches the new contract

Consult `references/checklist.md` for change-type-specific verification steps.

### Phase 4 — Report

Output a structured report:

```
## Regression Check Report

### Changed symbols
- `symbolName` in `path/to/file.ts:42` — description of change

### Verified consumers
- ✓ `path/to/consumer.ts:15` — uses `symbolName` correctly
- ✓ `path/to/other.tsx:88` — destructures updated fields

### Flagged mismatches
- ✗ `path/to/broken.ts:23` — still references old field `oldName`, should be `newName`
- ✗ `path/to/stale.tsx:55` — passes 2 args, new signature expects 3

### Needs manual review
- ? `path/to/dynamic.ts:10` — dynamic import, cannot statically verify
```

## Key Principles

- **Exhaustive**: trace transitive consumers, not just direct importers
- **Monorepo-aware**: changes in one app can break another app or shared package
- **Zero false confidence**: if a consumer can't be statically verified (dynamic imports,
  `require()`, string interpolation), flag as "needs manual review" — never silently skip
- **Actionable**: every finding includes file path, line number, and what needs attention
- **Concise**: no lengthy explanations — the report is a checklist, not a narrative

## Integration

- Reference `coding-convention` skill for naming consistency when renames are involved
- After this skill flags issues, run typecheck/lint/tests on flagged files
- This skill is proactive (pre-commit); `systematic-debugging` is reactive (post-bug)
