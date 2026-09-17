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

## Writing for a three-minute review

The reviewer already reads too many documents. Reduce volume at the source; the renderer only
packages what the JSON contains.

- Decisions first: `openQuestions` is rendered at the top as the decisions expected from the reader.
  Phrase each entry as a question followed by a proposed default.
- Word budgets: `summary` 60 words; each `goals`, `successMetrics` and `outOfScope` item 25;
  requirement `description` 40; each `acceptance` item 30; task `expectedOutcome` 30.
- At most 7 requirements at `must`; use `should` or `could` for the rest so priority stays
  informative. At most 5 `acceptance` items per requirement; a test matrix belongs in a task.
- No restatement: a sentence present in `userStories` does not reappear in a requirement or a task.
  `designConsiderations` holds only constraints absent elsewhere. Leave `userStories` empty when
  every story would map one-to-one to a requirement.
- Start every `title` with its information-bearing word, never with "Overview of" or
  "Considerations for".
- Keep tooling instructions (lint, typecheck, test commands) out of requirement acceptance criteria.
- `preDraft.reuse` and task `boundaries` are agent context: hidden from the human view by default,
  so write them for the implementing agent. `preDraft.sharedSurfaces` stays visible as the impact
  and compatibility block: lead each entry with the consumers and the obligation, because the
  reviewer must approve them.

## Render and validate

Resolve this skill directory as `<prd-skill>`, then run:

```bash
<prd-skill>/scripts/render-prd-html.sh plans/<timestamp>-<slug>.prd.json
```

The command validates the complete supported contract before writing
`plans/<timestamp>-<slug>.prd.html`. It has no package installation step or network dependency. An
optional second argument sets another HTML output path. Re-run it after every JSON edit and fix every
reported validation error.

After a successful render the command prints word-budget warnings on stderr. They never fail the
render. Shorten the named fields and re-render until the warnings are gone, or tell the user which
ones remain and why.

The HTML opens as a brief: decisions expected, goals, out of scope, then requirements and tasks
collapsed one per line. A "Mode présentation" button (key `d`) shows one block per screen; it is
opt-in and never the default. Agent context appears only through its own button.

Present the HTML path, the JSON source path and unresolved questions. Generated HTML is a build
artifact; agents and implementation tools consume the JSON.

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
