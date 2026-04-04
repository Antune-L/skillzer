# TypeScript Conventions

## Strict Rules

- Strict mode always
- Explicit return types for public functions
- **No type casting** (`as`, angle-bracket) — use type guards, `satisfies`, or Zod `parse`/`safeParse` instead. Only exception: when the compiler truly cannot infer a provably-correct type AND the alternative would be an unsafe workaround

## Types

- Prefer `interface` for object shapes
- Use `satisfies` for config objects
- Prefer `array.at(index)` over `array[index]` for type safety

## Validation

- Zod at boundaries — prefer `safeParse`/`parse` over ad-hoc runtime checks (`instanceof`/`typeof`/manual narrowing)
- Use generated Zod schemas (e.g. from Prisma) when available

## Naming

- PascalCase: components, types, interfaces
- camelCase: functions, hooks, files
- UPPER_SNAKE_CASE: constants

## Imports

- Order: external -> workspace -> local
- Prefer `import type` for type-only imports
- No magic numbers/strings — extract to constants
- Avoid nested ternaries — use if/else or early returns
