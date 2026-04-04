---
name: ts-search-first
description: "Before writing any new function, hook, type, or component, search the codebase for existing implementations to reuse."
metadata:
  short-description: Codebase-first (reuse before creation)
---

## Why this exists

Claude defaults to generating fresh implementations even when existing code is a 90% match. This skill forces a search-first habit to catch reuse opportunities before writing anything.

## Procedure

1. Never start by coding. Start by locating what already exists.
2. Search the codebase by:
   - Probable names (camelCase, PascalCase, kebab-case)
   - Types/interfaces/export names
   - Patterns (useXxx, XxxProvider, getXxx, buildXxx, createXxx, updateXxx)
   - Routes/paths (backend) and query keys (frontend)
3. Use fast searches (e.g. ripgrep):
   - `rg "use[A-Z]" src`
   - `rg "function <name>|const <name> =" src`
   - `rg "<TypeName>" src`
   - `rg "<route-path>" src`
4. If found:
   - Propose direct reuse, or minimal extension
   - Respect local conventions (folders, naming, exports)
5. If not found:
   - Create the smallest possible solution, consistent with existing architecture

## Output

- Short report: "Found / not found" + files examined.
- Then the proposal: reuse (preferred) or minimal implementation.

## Composability

- Run `coding-convention` after extending found code to verify naming/file placement.
- Run `regression-check` after modifying existing code to catch broken consumers.

## Gotchas

- When creating a new oRPC contract/schema, also search for **reusable utility schemas** (pagination, search, sort, userId filters) — not just routes. Missing these leads to duplicated schemas discovered only at review time.
- Search for aliased re-exports — exact name matches miss code that re-exports under a different name.
- In monorepos, search all workspace packages, not just `src/`. Duplicate utilities across packages are common.
