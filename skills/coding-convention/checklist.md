1. Detect duplication:
   - Similar logic across multiple files
   - Same data transformations
   - Same API calls with minor variations
2. Prefer:
   - Extracting a pure utility
   - Generic React hook if used repeatedly
   - Composition over complex configuration
3. Avoid:
   - Premature generics
   - Abstractions with a single caller
   - Homegrown "framework" patterns
   - Unnecessary comments, especially on self-explanatory code
4. Optimize readability:
   - Explicit names
   - Early returns
   - Short functions
   - Useful types (no "cosmetic" types)
   - **No nested ternaries**: if more than one level of `? :`, extract to intermediate variable, early return, or `if/else`

## Output

- Minimal refactor proposal (concrete diff).
- Justification in 3–5 lines max (DRY, readability, reduced surface).
