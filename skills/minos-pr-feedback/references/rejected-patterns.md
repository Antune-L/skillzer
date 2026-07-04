# Rejected-comment patterns — triage memory

Recurring comment classes and their default verdict. Consulted before triage; appended to after a
run only when the same class was skipped for the same reason on this PR **and** at least one
earlier PR. One line per pattern. Never log one-off skips.

Format: `pattern → default verdict → reason (source PRs)`

- Bot "consider extracting a helper" on ≲30-line duplication, 2 occurrences → skip-nit → user
  repeatedly judges it not worth it (fftir #311, #312)
- Bot "add null/undefined check" on a field the schema/ORM marks required → skip-wrong → misread
  of the data model (fftir #317)
- "Confirm this is intentional" / "verify with design" phrasing with no concrete failure →
  skip-nit → confirmation-seeking, not a finding (sofrapa #186, fftir #328)
- Style-preference renames with no misleading name involved → skip-nit → taste, not correctness
