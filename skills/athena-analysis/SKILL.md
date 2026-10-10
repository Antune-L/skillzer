---
name: athena-analysis
description: 'When the user sends source material (Notion link, kanban card, mockups, specs) about a problem or feature and wants it understood and a solution recommended before building — "analyse ce ticket", "analyse ce problème", "regarde ce Notion et propose une solution", "athena: lien".'
---

# Athena — Multi-source problem analysis with adversarial review

Athena, goddess of wisdom and strategy: gather every source, let independent analysts study the
problem, then let adversaries attack the result until only the best solution survives.

**Read-only.** Athena never edits source code, never moves kanban cards, never writes Notion
comments. The deliverable is an analysis report. Implementation starts only on explicit request
(hand off to `prd`, `asclepios-bugfix`, or inline work).

**Not for:** raw client feedback to reproduce in a browser (`chiron-client-feedback`), a feature
idea with no source material that should end in a PRD (`plan-feature`), a known bug to fix and
ship (`asclepios-bugfix`), or a two-way technical question (`paris-research`).

## Pipeline

### 0. Resolve models by role

Use **Luna for Codex exploration** and **Sonnet for Claude exploration**, choosing the newest
available version in that family. Prefer a fast execution/service setting when supported; keep
reasoning at the model's default or high level, since speed and reasoning depth are different
options. Keep Sol (Codex) or Opus (Claude) for solution analysts and adversarial reviewers. Escalate
a difficult ownership or contract question to a stronger available model; each escalation counts
as a budgeted call. Use a general-purpose agent capable of reading complete non-sensitive source files.

When the `t3-code` MCP is present, call `orchestrator_capabilities` once and select actual model
IDs from its live catalog, including custom models. Prefer native subagent tools for same-provider
work when they support the selected model; otherwise use `delegate_task`, including cross-provider
work. Without T3, inspect the native tool's supported models. Never invent model IDs or options.
If the preferred model is unavailable, choose an available equivalent and report the substitution.
If delegation is unavailable, report the missing independent validation rather than inventing it.

### Budget — depth follows evidence

Size the initial run after intake and announce it. Code exploration is a separate phase before
solution design; a request without repository claims can omit explorers.

| Size | When | Explorers | Analysts | Reviewers | Initial total |
| --- | --- | --- | --- | --- | --- |
| Light | one source, low ambiguity | 2 if code is involved, otherwise 0 | 2 | 1 | 5 or 3 |
| Standard | default | 2 | 3 | 3 | 8 |
| Deep code | several repos, uncertain ownership, conflicting evidence | 3 | 3 | 3 | 9 |
| Deep UX/data | mockups or data migration need a separate analyst | 2 | 4 | 3 | 9 |

Use **at least 2 independent analysts and 1 fresh adversarial reviewer**, and **at most 10
subagents per run**, explorers and re-review included. Respect the platform's concurrent limit.
The final spare slot is reserved for re-review; other spare slots can fund targeted exploration.
These are initial allocations: reduce or combine noncritical lenses when more discovery is needed,
while retaining the minimum analysts/reviewer. At nine allocated calls, no new exploration task can
consume the reserved tenth call. A deep run may therefore report a gap without attempting it twice.
When code and UX/data both need depth, combine a lens to retain the reserved review call.
At the limit, report the unresolved claim and its consequence instead of declaring coverage complete.

### 1. Intake — build the dossier

The orchestrator gathers sources itself, so every subagent reads the same material and no
subagent depends on MCP access it may not have.

1. Create a scratch dir: `ATHENA_TMP=$(mktemp -d "${TMPDIR:-/tmp}/athena.XXXXXX")`. Echo the path
   and carry it literally into later commands (env does not persist across Bash calls).
2. Inventory every input the user sent (links, files, images, pasted text). For each type, follow
   [`references/sources.md`](references/sources.md): Notion pages **and their relevant comments**,
   Notion databases used as kanban (related cards), the Atelier kanban MCP, mockups and
   screenshots, Figma, Slack threads, GitHub issues/PRs.
3. Follow links **one hop** from each primary source (linked pages, relations, parent epic, sibling
   cards). Go a second hop only when the first hop is clearly central to the problem.
4. Write `$ATHENA_TMP/dossier.md` using the template in
   [`references/prompts.md`](references/prompts.md#dossier-template): one section per source with its
   URL, a faithful summary, verbatim quotes for requirements and decisions, and the relevant
   comments with author and date. Copy images to `$ATHENA_TMP/images/` and list their paths with a
   one-line description of what each shows.
5. Identify the target repo or collection of repos, following the Code section in
   [`references/sources.md`](references/sources.md#code). Record absolute roots, revisions, and
   relevant local changes in the dossier. Treat a module suggested by a ticket as a hypothesis,
   not the search boundary. Never analyze code from memory.

**Clarification gate:** if the dossier is missing something that would change the analysis
(which repo, which persona, contradictory specs with no tie-breaker, inaccessible link), ask at
most 2 questions, each with a recommended default, before fanning out. Unreachable sources
(MCP not authenticated, 403) are reported, not silently skipped.

### 1.5. Repository exploration — establish facts before proposing changes

For repository-dependent requests, read [`references/exploration.md`](references/exploration.md)
and run at least two independent explorers with complementary scopes:

- **Artifacts and discovery**: start the filename/extension inventory at the whole product root,
  including nested services, with explicit exclusions. Then inspect relevant resources, fixtures,
  configuration, schemas, and domain/provider matches; do not inherit the ticket's module boundary.
- **Behavior and ownership**: trace the existing behavior, contracts, callers and consumers across
  modules; look for configuration, reuse, or an existing path that already satisfies the request.
- **Additional explorer when needed**: a distinct repo, data model, or uncovered dependency.

Give each a bounded question, exact roots/revisions, dossier, exclusions, and the explorer prompt
in [`references/prompts.md`](references/prompts.md#explorer-prompt), without another explorer's
conclusions or a proposed solution. Store factual results in `$ATHENA_TMP/exploration-ledger.md`: search
coverage, inspected candidates, behavior traces, conflicting evidence, and remaining gaps.

Before solution design, resolve critical gaps with a targeted task using a changed search strategy.
Apply the reference's decision gates and escalation limits; finish this evidence phase before
spawning solution analysts.

### 2. Wave 1 — independent analysts (parallel)

Spawn the analysts chosen in the budget **in a single message** so they run concurrently. Each gets
the dossier, exploration evidence when applicable, repo roots/revisions, and a distinct angle
(prompts in [`references/prompts.md`](references/prompts.md#analyst-prompt)):

- **Spec-first**: what exactly is asked, according to docs, comments, and mockups; contradictions
  between sources; acceptance criteria; edge cases the sources imply but do not state.
- **Code-first**: establish the actual owner and behavior (`file:line`), existing mechanisms to
  reuse, constraints (data model, permissions, API contracts), and minimal changes justified by
  the exploration decision gates.
- **Risk-first**: what could go wrong (regressions, consumers, migrations, permissions, performance,
  pre-existing data), and which solution shape minimizes that risk.
- **Product/UX or data** (when relevant): user flows and states from the mockups, or the data
  model, migration, and backfill implications, whichever dominates the problem.

Each analyst must return the structured analysis defined in the prompt (problem statement,
requirements with source, current-state findings with `file:line`, proposed solution, risks,
open questions, confidence). Analysts never see each other's output.

### 3. Synthesis — the orchestrator drafts

The orchestrator (not a subagent) merges the analyses into `$ATHENA_TMP/draft.md`:

1. Reconcile the problem statement; flag where analysts disagree and which source settles it.
2. Verify every claim the solution rests on, including absence claims, search completeness, and
   proposed module ownership, against current files and exploration coverage. Apply the decision
   gates in [`references/exploration.md`](references/exploration.md#decision-gates). Keep unverified
   assumptions visible; an agent's confidence or agreement does not replace evidence.
3. Pick one candidate solution; graft the best points from the others and say which.
4. List the assumptions the candidate depends on.

### 4. Wave 2 — adversarial review (parallel)

Spawn the fresh reviewers chosen in the budget in a single message (a light run uses only the
challenger). Give them the raw-source dossier, repo roots/revisions, and decision-gate reference,
then a marked after-search block containing the draft and exploration ledger. Do not give analysts'
raw outputs. Code reviewers search before reading that block; this independence relies on prompt
order, not technical access isolation. Lenses (prompts in [`references/prompts.md`](references/prompts.md#adversarial-reviewer-prompt)):

- **Spec fidelity**: does the draft cover every requirement, comment decision, and mockup detail?
  Did it misread or invent anything?
- **Code reality**: independently search for existing artifacts and alternative implementation
  paths, then apply the exploration decision gates and re-verify decisive `file:line` claims,
  hidden consumers and side effects. In a light run, the challenger also performs this code check.
- **Challenger**: argue the draft is the wrong solution; propose a simpler or more robust
  alternative and make the strongest case for it.

Each reviewer returns objections with severity (`critical` / `major` / `minor`), evidence, and a
suggested fix.

### 5. Verdict

For each objection, the orchestrator decides **accepted** or **rejected**, with a one-line reason
backed by evidence. Judge on evidence, not eloquence.

- If an accepted `critical` objection changes the solution, or an accepted `major` objection
  invalidates an absence claim or a required module change, revise the draft and run **one**
  re-review round with fresh reviewers left in the budget (at most 2, total stays at or below 10),
  prioritizing code reality for exploration objections. Include the original brief before search;
  put previous objections, decisions, and the revised draft in the after-search block of the new
  prompt (with T3 `delegate_task`, use a new call
  and a distinct `clientRequestId`, never `t3_thread_send` on the child thread).
- Never run more than one re-review round. Remaining disagreements go to open questions.

### 6. Report

Write `$ATHENA_TMP/report.md`, then give the user a concise version in chat using the structure
in [`references/prompts.md`](references/prompts.md#report-template):

- **Problem understood**: plain language, 3 to 5 sentences, with the sources that define it.
- **Related items**: linked cards, tickets, and pages found during intake, and why they matter.
- **Current state in the code**: key `file:line` findings and existing artifacts, with the roots,
  revision, coverage limits, and distinction between static evidence and runtime validation.
- **Recommended solution**: the approach, touched areas, and key steps, not a full implementation.
- **Rejected alternatives**: one line each with the reason.
- **Adversarial review outcome**: accepted objections and how they changed the solution.
- **Risks and open questions**: max 2 questions for the user, each with a recommended default.

**Always close the chat answer with the feasibility verdict**, as two bullet lists, one line per
point, no prose around them:

- **✅ Feasible**: each requirement or point that can be done, with its condition when there is one
  ("feasible if the API exposes X").
- **❌ Not feasible**: each point that cannot be done as asked, with the blocking reason in a few
  words (technical limit, missing data, contradicts another requirement, needs a decision).

Every requirement from the dossier appears in exactly one list. Base the classification on the
post-review solution, not on the analysts' first opinion. Missing evidence is not a technical
impossibility: state it as a validation condition or an unresolved decision, with the observed
blocker, rather than claiming an artifact or behavior does not exist.

After the verdict, offer the next step (PRD with `prd`, fix with `asclepios-bugfix`, or
implementation) and give the report path.

## Gotchas

- **Comments can override the page body.** In Notion, a later comment often changes the scope
  ("finalement on ne fait pas l'export"). Sort comments by date and treat the latest decision as
  authoritative; flag the conflict in the dossier instead of silently picking one.
- **Resolved comments still matter.** `notion-get-comments` hides resolved discussions by default;
  resolved threads often hold the final decision. Fetch them with `include_resolved: true` and mark
  them as resolved in the dossier.
- **Block-level comments are hidden by default.** Page-level only is the default; pass
  `include_all_blocks: true` or most of the discussion is missed.
- **Convergent analysts are a weak signal.** If all analysts propose the same solution, the
  angles were too close; the challenger reviewer becomes the most important one, so brief it harder.
- **Subagents do not inherit the conversation.** Everything they need must be in the dossier or the
  prompt (paths, repo, branch). A missing piece of context produces a confident wrong analysis.
- **A negative search is scoped evidence.** Files may have generic names, domain acronyms, provider
  payload fields, or misspelled directories. Inventory requested extensions and inspect relevant
  fixtures/resources; do not conclude absence from a provider-name search or ignored-file defaults.
- **Mockups are not specs.** Visual details in a mockup that contradict the written ticket go to
  open questions; do not let either silently win.
