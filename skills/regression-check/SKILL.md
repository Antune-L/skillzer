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

For each changed symbol, find ALL consumers:

```
grep -r "import.*{.*symbolName.*}" --include="*.ts" --include="*.tsx"
grep -r "from ['\"].*changedModule['\"]" --include="*.ts" --include="*.tsx"
```

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
