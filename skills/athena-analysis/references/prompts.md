# Templates and subagent prompts

Replace `<...>` placeholders with literal values before sending; subagents do not see the
conversation.

## Dossier template

```markdown
# Dossier — <short title>

Repo roots: <each absolute root, branch, short sha, relevant local changes>
Graph: <graphify-out path or "none">

## User request
<verbatim message from the user>

## Sources
### <source 1 title> — <url> — <reachable | unreachable: reason>
Summary: <faithful summary>
Requirements (verbatim):
- "<quote>"
Relevant comments:
- <author>, <date>, <resolved?>, on "<anchored text>": "<comment>"

### Related items
- <card/page title> — <url> — relation: <duplicate | dependency | previous attempt | conflict | follow-up> — <why it matters>

## Images
- <absolute path> — <what it shows>

## Conflicts between sources
- <source A says X, source B says Y; latest dated is ...>
```

## Explorer prompt

```text
Work read-only to establish current repository facts before any solution is chosen. Do not edit
the repository, switch branches, fetch, or trigger application/provider operations.

Inputs:
- Dossier: <ATHENA_TMP>/dossier.md
- Exact assigned roots and revisions: <literal paths, branches, SHAs, relevant local changes>
- Whole product root for artifacts inventory: <literal path, not just the ticket module>
- Instructions: <applicable instruction paths>
- Scope: <artifacts and discovery | behavior and ownership | distinct uncovered area>
- Bounded question: <specific question to settle, without a proposed solution>
- Search exclusions: <literal exclusions and why>
- Exploration procedure: <literal path to references/exploration.md; read it>

Apply the exploration procedure and decision gates, including safe content discovery. Never print
secret values. Read complete relevant non-sensitive source files; classify configuration and
credential files using the reference's metadata-only procedure first. Treat module ownership as a hypothesis.

Return:
1. Assigned scope and inspected revisions
2. Search ledger: queries/patterns, roots, exclusions, results inspected and coverage gaps
3. Artifacts found: exact path, category, purpose, file:line and consumers
4. Existing behavior and ownership: verified call/contract links and alternative paths
5. Candidates ruled out with evidence
6. Unresolved questions, impact, and next targeted search
7. Confidence based on evidence; label unverified claims explicitly
```

## Analyst prompt

```text
You are a senior engineer analyzing a problem before any implementation. Work read-only: do not
edit, create, or delete any file in the repo.

Inputs:
- Dossier: <ATHENA_TMP>/dossier.md (read it fully, open every image listed)
- Repo roots and revisions: <literal paths, branches, SHAs, relevant local changes>
- Exploration evidence: <ATHENA_TMP>/exploration-ledger.md or <not applicable: reason>
- Decision gates: <literal path to references/exploration.md, when code is involved>

Your angle: <spec-first | code-first | risk-first | product-UX or data>
<one paragraph describing the angle, copied from SKILL.md step 2>

Ground every claim in a source: dossier section, image path, or file:line in the repo. Read the
code; never infer it from file names. Mark anything you could not verify as "unverified". Apply the
exploration decision gates for absence and change claims. Never print secret values; follow the
reference's safe search procedure. Do not equate missing evidence with impossibility.

Return exactly these sections:
1. Problem statement (3-5 sentences, plain language)
2. Requirements: each with its source, marked explicit or inferred
3. Current state in the code: findings with file:line
4. Proposed solution: approach, justified required/conditional/optional changes, what is reused
5. Alternatives considered and why rejected
6. Risks: regressions, consumers, data, permissions, performance
7. Feasibility per requirement: feasible (with condition if any) | not feasible (with reason)
8. Open questions that block or change the solution
9. Confidence: high | medium | low, with why
```

## Adversarial reviewer prompt

```text
You are an adversarial reviewer. A draft analysis and solution were produced for the problem below.
Your job is to find what is wrong, missing, or weaker than it could be. Do not rubber-stamp: an
empty objection list requires a justification of what you checked. Work read-only.

Before-search inputs:
- Dossier: <ATHENA_TMP>/dossier.md
- Repo roots and revisions: <literal paths, branches, SHAs, relevant local changes>
- Decision gates: <literal path to references/exploration.md, when code is involved>

Your lens: <spec fidelity | code reality | challenger>
<one paragraph describing the lens, copied from SKILL.md step 4>

For code reality (and the light-run challenger), search independently from the request and raw
sources for artifacts, existing paths, and owners before reading the after-search block. Then
apply the decision gates. Report search scope and evidence even without objections. Never print
secret values; follow the reference's safe search procedure.

After-search inputs (do not read until your independent search is recorded):
- Draft: <ATHENA_TMP>/draft.md
- Exploration ledger: <ATHENA_TMP>/exploration-ledger.md
- Re-review only: <previous objections, decisions, changes>

For each objection return:
- Severity: critical (the solution fails or misses the problem) | major (significant gap or risk) | minor
- Claim: what is wrong, in one sentence
- Evidence: dossier quote, image path, or file:line you verified yourself
- Suggested fix

Challenger lens only: also return your best alternative solution and the strongest argument that it
beats the draft.
```

## Report template

```markdown
# Analyse — <title>

**Problème compris** — <3-5 sentences> (sources: <links>)

**Éléments liés** — <card/page: why it matters>

**État actuel du code** — <file:line findings and artifacts; roots/revisions, coverage limits>

**Solution recommandée** — <approach; required/conditional/optional changes with reasons; reuse>

**Alternatives rejetées** — <one line each + reason>

**Revue adversariale** — <accepted objections and how they changed the solution; rejected ones in one line>

**Risques** — <list>

**Questions ouvertes** — <max 2, each with a recommended default>

**Faisabilité**

✅ Faisable
- <point> — <condition if any>

❌ Pas faisable
- <point> — <blocking reason>
```

Write the report in the user's language.
