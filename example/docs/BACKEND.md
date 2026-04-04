# Backend Conventions

<!-- This is an example of a deeper doc referenced from CLAUDE.md's Documentation Index.
     Adapt to your actual stack. -->

Stack: [NestJS / Express / Hono] + Prisma + PostgreSQL

## Structure

- Extract pure helpers (mapping, sorting, formatting) to `<feature>.utils.ts`
- Functions that throw or depend on service context stay as service methods
- Group by business logic in subfolders when a feature grows

## Validation

- Zod at boundaries — prefer `safeParse`/`parse` over ad-hoc runtime checks
- Use generated Zod schemas from Prisma when available

## Errors & Logs

- Structured logging (pino or equivalent)
- Include context in error messages
- Don't silently swallow errors — log before re-throwing

## Database

- Prisma for ORM
- Always use migrations for schema changes
- Cascade direction: from referenced table toward FK holder — double-check before applying
