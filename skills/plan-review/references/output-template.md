# Output Template

Produce the review following the language of the original plan markdown (French plan = French review, English plan = English review).

```
## Plan Review

**Problem Statement**: [one-sentence restatement of the core problem]

### Verdict: [APPROVE | REVISE | REJECT]

### Completeness
- [requirement 1]: [COVERED | MISSING] — [brief note]
- [requirement 2]: [COVERED | MISSING] — [brief note]

### Issues Found
> Skip this section entirely if no issues found.

1. **[INCORRECT|RISKY|MISSING]** — [step reference]: [description of the issue and why it matters]

### Quality Assessment
- Problem Resolution: [brief assessment]
- Minimal Diff: [brief assessment]
- Simplicity: [brief assessment]
- Regression Safety: [brief assessment]

### Suggested Changes
> Skip this section entirely if verdict is APPROVE.

- [actionable change 1]
- [actionable change 2]

### Alternative Approach
> Skip this section entirely if the current approach is sound.

[Brief description of alternative and why it's better]
```

## Verdict Criteria

- **APPROVE**: All requirements covered, no correctness issues, solution quality is acceptable
- **REVISE**: Requirements covered but approach has issues that should be fixed before implementation
- **REJECT**: Missing requirements, fundamental correctness issues, or a clearly superior alternative exists
