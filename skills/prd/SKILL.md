---
name: prd
description: "Generate a Product Requirements Document from user instructions using the PRD template. Outputs a human-readable self-contained HTML file plus a markdown source for implementation tooling. Includes a macro-level task checklist at the end."
---

Use the template at [prd-template.md](./prd-template.md). Follow its directives and replace placeholders with the user's instructions.

## Pre-draft (mandatory — before writing the PRD)

Run these gates first and record their output in the PRD's **Pre-draft findings** block. Skipping
them under-specifies the work; the implementer (often a weaker model that follows the PRD literally)
then reinvents existing code or breaks shared components.

1. **Reuse scout** — run the `ts-search-first` skill to find existing components, hooks, utils,
   contracts, and feature codes to reuse. List each as "reuse `X` (`path`)". Don't let the
   implementer recreate what exists. If the project defines its own reuse rule (CLAUDE.md,
   `.cursor/rules/*`), cite it in the findings.
2. **Shared-surface scout** — decide whether the feature must touch a shared file (any file
   imported by many features: `components/ui|form|table|layout`, `hooks/`, `lib/`, `utils/`,
   shared packages in a monorepo — detect per project, don't assume this layout). If yes, state
   per file: **extend locally** (preferred — new prop/variant/wrapper) OR, if an in-place edit is
   unavoidable, **list the consumers + require backward-compat and a `regression-check` pass**.
3. **Source priority** — declare the order the implementer follows when sources disagree:
   **user instruction > Figma mockup > business doc > existing code**. Flag any contradiction you
   spotted between sources for the user to resolve before drafting.

After the PRD content, add a "Tasks" section with a checklist (`- [ ] ...`). Tasks must be MACRO-level (epics), not granular case-by-case items.

## Output format (mandatory)

The human-facing deliverable is an **HTML file**, not raw markdown.

1. Write the PRD as markdown (`<name>.prd.md`) — the single source of truth, consumed by
   implementation skills (`composer-implement`, `oppenheimer`, plan runners). Use GFM: tables for requirements with
   attributes (priority, status), `- [ ]` task checklist, a `## Pre-draft findings` section at
   the top.
2. Render the HTML **from the markdown via the script** — never write the HTML by hand:

   ```bash
   ~/.claude/skills/prd/scripts/render-prd-html.sh <name>.prd.md
   ```

   It produces a self-contained `<name>.prd.html` (inline CSS, light/dark, table of contents,
   real checkboxes) next to the source. After any edit to the `.prd.md`, re-run the script —
   the HTML is a build artifact, not a second document to maintain.
3. Tell the user the HTML path and suggest `open <name>.prd.html` to view it.
