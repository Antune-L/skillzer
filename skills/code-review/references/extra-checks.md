# Dead Code & Complexity Checks

Apply these to all changed files, in addition to the principles checklist.

| Signal | What to look for | Severity |
|---|---|---|
| Unreachable branches | Conditions that can never match (`if (true && false)`, switch case after `return`, code after `throw`) | critical |
| Unused variables | Locals declared but never read | warning |
| Unused imports | Imports not referenced in the file | nit |
| Unused exports | Exported symbols with zero importers — confirm via grep before flagging | warning |
| Nested ternaries | Ternaries inside ternaries — convert to `if`/`else` or early returns | warning |
| Deeply nested callbacks | More than 3 levels of nested callbacks/closures — extract or flatten | warning |
| Functions > 50 lines | Without a clear, justified reason (large switch / state machine / generated code) | warning |
| Magic numbers/strings | Literal values used in logic without a named constant | nit |
| Leftover debug calls | `console.log`, `debugger`, `print()` left in source | nit |
| Commented-out code | Dead commented blocks instead of deleted code | nit |
| TODO without owner | `TODO:` without an owner tag (project convention often `TODO(name):`) | nit |

## Notes

- A 60-line function with a single big switch on a discriminated union is **fine** — don't flag it.
- An unused export in a public package entry point may be intentional API surface — check for `package.json` `exports` and `index.ts` re-exports before flagging.
- Magic strings used as keys in a typed map (with `as const`) are not magic — they're the schema.
