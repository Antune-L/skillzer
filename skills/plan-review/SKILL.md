---
name: plan-review
description: >
  Review a markdown plan (from EnterPlanMode or /plan) before implementation.
  Triggers on "review this plan", "check my plan", "is this plan good".
---

# Plan Review

Critical review of implementation plans produced by Claude's planning mode.

## Input

The plan is a markdown document where:
- The **first lines** contain the original user prompt / problem context
- The rest describes the proposed implementation steps

Provided as a file path or inline markdown.

## Review Process

### 1. Extract the Problem

Read the plan, isolate the original context, restate the core problem in one sentence.

### 2. Completeness Check

For each requirement or bug in the context, verify a plan step directly addresses it.
Flag unaddressed requirements as **MISSING**.
For bug fixes: verify the root cause is identified — not just symptoms.

### 3. Correctness & Risk Analysis

For each step, flag as **INCORRECT** or **RISKY** if:
- It could introduce regressions on existing consumers of modified code
- It relies on implicit assumptions that might not hold
- For bug fixes: it patches a symptom instead of the root cause

### 4. Solution Quality Assessment

Evaluate by priority:

1. **Problem Resolution** — Does this actually fix the problem?
2. **Minimal Diff** — Only necessary changes? Flag scope creep.
3. **Simplicity** — Simplest approach that works? Flag over-engineering.
4. **Regression Safety** — Accounts for existing consumers?
5. **Maintainability** / **Performance** / **Convention Compliance** — only flag if material.

### 5. Alternative Solutions

Propose a better approach only when clearly superior — do not nitpick.

## Output

Follow the template in `references/output-template.md`. Match the language of the original plan.

## Important Guidelines

- Read all files referenced in the plan before judging — do not review in the abstract
- Be specific: reference exact plan steps, file paths, and line numbers
- Review scope = plan scope — do not add suggestions beyond the original context
- Bias toward APPROVE when the plan is reasonable, even if not perfect
- Bias toward REJECT when a bug fix doesn't address root cause
- For bug-fix plans, apply `systematic-debugging` reasoning to validate root cause analysis
- For convention concerns, defer to `coding-convention` skill criteria

## Gotchas

- **Plans that look complete but miss context edges**: The original prompt may contain implicit requirements buried in examples or parentheticals. Read the full context twice — the second pass catches what the first skims over.
- **Symptom-patching disguised as root cause fix**: A plan that says "add a null check" or "add a try/catch" is likely treating symptoms. Push back unless the plan explains *why* the value is null or *why* the exception occurs.
- **Scope creep via "while we're here" refactors**: Plans often sneak in cleanup steps unrelated to the stated problem. These increase regression surface for zero problem-resolution value. Flag them.
- **Missing regression check on consumers**: Plans that modify a shared function/type rarely list the callers that need updating. If the plan touches exports or public APIs, verify it accounts for downstream impact.
- **Over-confident "simple" plans for complex bugs**: When a bug involves async timing, caching, or state management, a plan with fewer than 3 steps is suspicious. These bugs usually need investigation steps before fix steps.
