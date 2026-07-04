# Library best-practice checklists — per detected lib

Static, version-aware checklists for the **quality** reviewer's folded library check. The
orchestrator detects the stack from `package.json` (see `mechanical-checks.md` §Stack manifest)
and passes this file's absolute path in the quality envelope; the reviewer reads it and applies
**only the detected libs' sections**. A lib that is not in the manifest must never be checked —
its idioms don't apply.

**Static first, context7 on doubt.** These checklists are the deterministic baseline. When the
reviewer is unsure whether an API form is current for the *detected major version*, it queries the
context7 MCP for that lib instead of flagging from memory. A finding based on a remembered older
version is a false positive.

Severity default: `warning` when the misuse can fail silently or throw at a boundary; `nit` for
stylistic lib idioms.

---

## zod (detect version — v3 vs v4 APIs differ)

- **Boundary parsing**: external input (HTTP body/query/params, webhook payloads, env, file
  contents) goes through `safeParse` (or a framework-validated contract) — a bare `.parse()` on
  external input throws unhandled. `.parse()` is fine on internal/trusted data.
- **v4 forms** (only when manifest says zod@4): `z.email()` / `z.url()` / `z.uuid()` not
  `z.string().email()` (deprecated); `z.strictObject(...)` not `.strict()`; error customization
  via `error:` not `message:`/`errorMap`.
- **Query/route params are strings**: numeric/boolean params need `z.coerce.number()` /
  explicit transform — `z.number()` on a query param always fails at runtime.
- **`discriminatedUnion` over `union`** when a discriminant field exists — better errors, O(1)
  dispatch, exhaustive narrowing.
- **Don't duplicate schemas across layers**: deriving with `.pick()`/`.omit()`/`.extend()` from a
  shared schema beats re-declaring the shape front + back (drift risk — pairs with the logic
  reviewer's cross-layer rule check; flag the duplication here, the drift there).
- **Don't re-validate what types guarantee**: schema for external data, plain types for internal
  function args.
- **Transform placement**: prefer `.pipe()` / `.transform()` on the schema over post-parse manual
  massaging that can drift from the schema.

## tanstack-query (react-query)

- **Query key completeness**: every variable the `queryFn` closes over (id, filters, page,
  **locale**) appears in the key — a missing key segment serves stale cross-parameter cache.
  (Recurring real bug: locale-enriched responses without `locale` in the key.)
- **Invalidation after mutation**: a mutation that changes server state invalidates (or updates)
  the affected queries in `onSuccess`/`onSettled` — flag a mutation with no cache handling.
- **`enabled` for conditional fetches** — not an `if` around the hook (rules-of-hooks) and not a
  sentinel id like `id ?? 0`.
- **No `useEffect` + `refetch()` choreography** for what a key change already does — changing the
  key refetches; effects around queries are an anti-pattern.
- **Derived state from `data`**, computed in render or `select` — not copied into local state via
  effect.

## drizzle / prisma (ORM)

- **Transactions for multi-statement mutations**: a loop of inserts/updates/deletes that must
  succeed together runs inside `db.transaction` / `$transaction` — partial commit on mid-loop
  throw is a data bug (quality owns the lib usage; the non-atomicity itself may already be seeded
  by quality item 5 — don't double-flag, pick one finding).
- **N+1**: a query inside a loop over a previous query's rows → use a join / `inArray` / `include`.
- **Select only what's used** when the row is wide and hot (list endpoints): flag `select()`-less
  full-row fetches feeding a 3-field DTO. `nit` unless on a hot path.
- **Drizzle**: prefer the relational `db.query.*.findMany({ with })` API over hand-assembled
  joins when relations are defined; **Prisma**: beware implicit `findUnique` null — handle the
  null path.
- **Migration hygiene — never hand-write what the generator owns** (real incident: sofrapa
  #155/#166/#176/#190 hand-written SQL-only migrations desynced Drizzle snapshots and broke
  replay from an empty DB; repaired in #196/#198). The mechanical pre-pass seeds the structural
  signals (see `mechanical-checks.md` §ORM migration hygiene); this reviewer judges them:
  - **Drizzle**: every new migration comes from `drizzle-kit generate` — `migration.sql` and its
    snapshot state (per-dir `snapshot.json` or `meta/_journal.json` entry) commit together. An
    SQL-only migration is a `warning`; a schema change with no regenerated migration is drift.
  - **Prisma**: new migrations come from `prisma migrate dev` — the `schema.prisma` change and
    `prisma/migrations/<ts>_*/migration.sql` land in the same PR; one without the other is drift.
  - **Editing an already-merged migration is `critical`** — it may be applied to shared/prod
    databases; the fix is a new forward migration, never a rewrite of history.
  - Manual DDL executed directly against a database is invisible in a diff — when snapshot drift
    appears with no migration explaining it, flag the gap and recommend a CI replay/drift check
    (`drizzle-kit check` / regenerate-and-fail-on-diff) rather than guessing.

## eden treaty / trpc (type-safe API clients)

- **Don't rewrap typed errors**: catching the client's `{status, value}` error and rethrowing a
  bare `Error` drops the status the caller needs (recurring real bug — auth handling loses the
  401).
- **No hand-written fetch** to a route the typed client already exposes — bypasses the contract.

## react-hook-form

- **Validation through the resolver** (zodResolver with the shared schema) — not manual `validate`
  callbacks duplicating schema rules.
- **`Controller`/`*Field` wrappers for controlled inputs** — not `watch()` + `setValue()`
  choreography for a single field.

---

## Extending this file

When a review hits a recurring misuse of a lib not listed here (or a new rule for a listed lib),
add it — one bullet, concrete, version-tagged if the API differs across majors. Keep each lib
section under ~10 bullets: this is a checklist of *high-frequency, mechanically recognizable*
misuses, not the lib's documentation.
