---
name: prd
description: "Create a Product Requirements Document as structured JSON and render a self-contained HTML deliverable. The JSON is the sole PRD source and ends with macro-level implementation tasks."
---

# Product requirements documents

Author the PRD once as JSON and present the generated HTML to the user. Never create a parallel
`.prd.md` or hand-write the HTML.

Use [prd-template.json](prd-template.json) as a concrete, valid starting document. The field
contract is documented by [schemas/prd.schema.json](schemas/prd.schema.json), while the renderer
performs dedicated validation of the same contract without claiming general JSON Schema support.

## Before drafting

Inspect the repository before asking for facts. Use `ts-search-first` to find components, hooks,
utilities, contracts and feature codes that can be reused. Record concrete hits in `preDraft.reuse`.

Identify shared surfaces and their consumers. Prefer a local extension such as a prop, variant or
wrapper. When an in-place change is unavoidable, list its consumers, require backward compatibility
and include a `regression-check` pass in `preDraft.sharedSurfaces`.

Record every link or document the user pasted — Notion page, Figma file, business document, ticket,
repository path — in `sources` with a short title, and keep them even when the prose never cites
them.

Resolve source disagreements with the user before drafting. Record the source order exactly as
`user instruction`, `Figma mockup`, `business document`, `existing code`, unless the user explicitly
changes it. Put unresolved contradictions in `openQuestions`.

Ask one to three questions only when a material product decision remains unresolved. Preserve the
guided, user-centred check-in before a significant change of focus or key interpretation. Draft only
after the user confirms there is enough information.

## Authoring contract

Create `plans/<timestamp>-<slug>.prd.json`. Use plain text in values; do not encode HTML, Markdown
layout or generated counters. Keep requirements observable and implementation-agnostic.
Write all authored prose in the JSON and resulting HTML in French. Keep JSON keys, IDs, file paths,
commands and code identifiers unchanged.

The final `tasks` array is a macro checklist of independently verifiable outcomes. Each task uses a
stable `T1`, `T2`, etc. identifier and states `expectedOutcome`, `startCondition`, observable
`acceptance` criteria and `boundaries` from `preDraft`. Use
`None — can start independently` when a task has no prerequisite.

Do not assign agents, files, execution order or a fixed agent count. Those choices belong to a
separate implementation plan based on the current code.

## Pyramid structure

The document states the need once, then the axes that answer it, then the detail under each axis.

- Level 1, the need: `summary` says what we need and `goals` says what success looks like. No
  detail, no solution.
- Level 2, the axes: `axes` holds 3 to 5 workstreams that together solve the problem. Each has an
  `A1`, `A2`, etc. identifier, a `title` and a `summary` of one sentence within 20 words. This is
  the slide where a hurried reader stops, so each axis must be understandable without the detail.
- Level 3, the detail: every requirement and every task carries an `axis` field referencing exactly
  one axis. An axis without a requirement fails the render; an axis without a task only warns.
- Decisions stay first: `openQuestions` is rendered before the need, because a reader who must
  arbitrate sees the arbitration before the argument.

## Writing for a three-minute review

The reviewer already reads too many documents. Reduce volume at the source; the renderer only
packages what the JSON contains.

- Decisions first: `openQuestions` is rendered at the top as the decisions expected from the reader.
  Phrase each entry as a question followed by a proposed default.
- Word budgets: `summary` 60 words; each axis `summary` 20; each `goals`, `successMetrics` and
  `outOfScope` item 25; requirement `description` 40; each `acceptance` item 30; task
  `expectedOutcome` 30.
- At most 7 requirements at `must`; use `should` or `could` for the rest so priority stays
  informative. At most 5 `acceptance` items per requirement; a test matrix belongs in a task.
- No restatement: a sentence present in `userStories` does not reappear in a requirement or a task.
  `designConsiderations` holds only constraints absent elsewhere. Leave `userStories` empty when
  every story would map one-to-one to a requirement.
- Start every `title` with its information-bearing word, never with "Overview of" or
  "Considerations for".
- Keep tooling instructions (lint, typecheck, test commands) out of requirement acceptance criteria.
- Write acceptance criteria in the EARS pattern: « Quand <événement>, le système doit… », « Tant
  que <état>, … », « Si <cas d'erreur ou limite>, alors… ». Every `must` requirement carries at least
  one « Si…, alors… » criterion, because error and edge cases are what implementing agents omit.
  Replace vague adjectives (rapide, intuitif, robuste, fluide, simple…) by an observable threshold or
  behaviour; the renderer warns on both.
- Record implementation pitfalls in the `boundaries` of the task they threaten, as an entry starting
  with `Piège :` followed by the risk and the instruction (« ne pas… », « réutiliser… »). Keep them to
  the traps an agent would plausibly fall into without product judgement.
- `sources` is a reference shelf, not prose: it carries no word budget and does not count towards the
  reading estimate, so a `title` of a few words plus its `ref` is enough.
- `preDraft.reuse` and task `boundaries` are agent context: hidden from the human view by default,
  so write them for the implementing agent. `preDraft.sharedSurfaces` stays visible as the impact
  and compatibility block: lead each entry with the consumers and the obligation, because the
  reviewer must approve them.

## Render and validate

Resolve this skill directory as `<prd-skill>`, then run:

```bash
<prd-skill>/scripts/render-prd-html.sh plans/<timestamp>-<slug>.prd.json [output.html] [--previous <old.prd.json>]
```

The command validates the complete supported contract before writing
`plans/<timestamp>-<slug>.prd.html`. It has no package installation step or network dependency. The
optional positional argument sets another HTML output path. `--previous` compares the document with
an earlier JSON by identifier: new and modified axes, requirements, tasks and questions carry a
badge, removed ones are listed in a banner, and a « Seulement les changements » button appears. An
earlier schema version is accepted and compared on the fields both versions share. Re-run the
command after every JSON edit and fix every reported validation error.

After a successful render the command prints warnings on stderr: word budgets, vague words and
`must` requirements without a « Si… » / « If… » criterion. They never fail the render. Fix the named
fields and re-render until the warnings are gone, or tell the user which ones remain and why.

The HTML opens as a brief: decisions expected, the need (title, summary, goals, then the sources
when there are any), out of scope, the axes list, then one section per axis holding its summary,
its requirements and its tasks, collapsed one per line, followed by the additional context and the
impact block. Every axis, requirement and task has an anchor (`axis-A1`, `req-FR1`, `task-T3`), and
task dependencies are links, marked when they cross axes. A "Mode présentation" button (key `d`)
shows one block per screen: decisions, the need, the axes overview, then for each axis its title
slide followed by its requirement and task slides, then out of scope and the rest. Key `g` opens the
slide grid; keys with a modifier are ignored. Presentation is opt-in and never the default. Agent
context appears only through its own button.

## Review before presenting

The render checks form only; omissions of substance are found by reviewers. Run this review after
the first successful render, before presenting the PRD, unless the user asks to skip it.

1. Pyramid check, in a fresh context. Give one read-only subagent only `summary`, `goals`, `axes`
   and `outOfScope`, nothing else, and ask it to answer:
   - Restate the plan in three sentences.
   - Which pairs of axes overlap?
   - Which part of the need is covered neither by an axis nor by `outOfScope`?
   - Are the axes the same kind of idea (can one plural noun name them all)?
   - Does every axis title state an outcome rather than a label (« Débloquer l'envoi » rather than
     « Prérequis inter-services »)?
   Rewrite the axes when its restatement diverges from the intent.
2. Substance review. Launch two to four read-only subagents in parallel, each on one angle that
   fits the PRD, for example: contracts and consumers of the shared surfaces, data semantics and
   mappings, operations and documentation (runbooks, migrations, rollout), compliance with this
   skill. Each receives the JSON path and the repository, and reports only gaps that would change a
   requirement, an acceptance criterion or a task, each with evidence (file and line, command
   output). Style remarks are out of scope.
3. Apply the accepted findings, increment `revision`, re-render with `--previous` pointing at a copy
   of the reviewed JSON so the reviewer sees what changed, and list the rejected findings with one
   reason each in the final message.

When the host cannot spawn subagents, run the same two passes yourself, reading only the listed
fields for the pyramid check.

Present the HTML path, the JSON source path, the review outcome and the unresolved questions,
copied verbatim rather than referred to. Generated HTML is a build artifact; agents and
implementation tools consume the JSON.

## Gotchas

- JSON has no comments and rejects trailing commas. Keep rationale in document fields.
- Empty optional arrays are valid, but every supported top-level field is required to prevent silent
  content loss between authoring and rendering.
- Task dependencies must reference another task ID and cannot reference the same task.
- In `renderPrd.py`, keep the global `[hidden]{display:none!important}` rule: any `display:flex` rule
  otherwise overrides the `hidden` attribute and leaks presentation controls into the brief.
- Chrome wraps the non-summary children of `<details>` in one anonymous box, so `display:grid` on a
  `details` puts them all in the first column. Use CSS multicol with `column-span:all` on the
  summary instead.
- CSS cannot open `<details>` for printing; the `beforeprint` handler does it.
- Long identifiers and paths need `overflow-wrap:anywhere`, otherwise the page scrolls sideways on
  mobile.
- Text is escaped during rendering. Put literal product wording in JSON; never pre-escape HTML.
- The brief order is the DOM order, so the slide order can only differ from it through the explicit
  `slideOrder` list in `PRD_CONFIG`: every slide carries a `data-slide-key` and the script sorts the
  slides by that list. A new slide without a key sorts to the front; add its key to `slide_order()`.
- The sources live inside the need block rather than in a block of their own: a section that is
  neither a `slide` nor a `pres-group` would stay on screen during the whole presentation. The brief
  list and the slide footer line are two elements of that block, swapped by `body.presenting`.
- The `h1` precedes the decisions, so it lives in `#page-head`, which is not a slide; the script shows
  it in presentation only on the `#brief` slide. Any new top-level element that is neither a slide
  nor a `pres-group` must be hidden in presentation, otherwise it stays on screen for every slide.
- Axis sections and their « Exigences » / « Tâches » parts are nested `pres-group`s; hiding with
  `group.hidden = !group.contains(current)` works at every level.
- In presentation, the click handler must handle `data-slide-target` links before the
  `preventDefault` that stops a `summary` click from collapsing the slide.
- The `@media print` token block must also target `:root:not([data-theme="light"])`, otherwise the
  dark system theme wins on specificity and prints light text on white paper.
- The `--previous` filter hides only compared items (axes, requirements, tasks, questions); an axis
  whose only change is a removed task looks unchanged, and the removal shows in the banner alone.
- The « Si… » edge-case warning fires on PRDs written before the EARS rule, which phrase edge cases
  as « Sans… » or « Un échec… ». Rewrite the criterion rather than widening the pattern.
