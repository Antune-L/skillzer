# UX and visual foundations

Use the task guidance for new and existing screens. When choosing the look, build on the
product's tokens, fonts and palette.

## From task to layout

| Decision | Starting point | When the task needs more |
|---|---|---|
| Entry point | Name the object and action in the user's terms. | Test navigation labels in a plain outline. Ask where to change a billing address and observe the first choice and backtracking. |
| Hierarchy | Use contrast, scale and proximity to establish reading order. | Prioritize by state. An overdue invoice can foreground its balance and due date. Keep comparable values aligned. |
| Available actions | Show what an action affects and put frequent actions within reach. | Reveal rare options at the point of need. Show active filter values near the affected list, even when the filter panel is closed. |
| Feedback | Distinguish pending, confirmed, empty and failed states. | Keep filtered-empty recovery tied to the filters. Keep pending saves visible until the outcome is known. |
| Recovery | Keep entered values and say how to fix an error. | Restore search, sort, selection and reading position after detail. If the original item disappeared, move focus to a nearby row or list heading. |

For meaningful commitments, show the consequence before the action and offer an editable
review where it helps catch mistakes. Test first-time use, repeated use or resumption based
on which matters for this screen. [Nielsen's usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) · [Tree testing](https://www.nngroup.com/articles/tree-testing/) · [Applied filters](https://baymard.com/research-articles/how-to-design-applied-filters) · [GOV.UK check answers](https://design-system.service.gov.uk/patterns/check-answers/) · [Moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)

## Hierarchy

- One focal point per screen and per zone: a single primary button per zone, secondary actions
  as outline, ghost or link.
- Build emphasis with at most two levers per element among size, weight, contrast, position,
  spacing, colour and shape. Reach for contrast and spacing before colour.
- Blur test: on a blurred screenshot the intended focal point is still the first thing seen.
- Reading order: title and summary top left, then detail. DOM order equals visual order.
- Only the single element the user must notice differs from its siblings. Highlighting several
  cancels the effect.

## Spacing and sizes

- Every spacing and text size comes from the project scale. No one-off values (`13px`,
  `p-[13px]`). Four or five text sizes per screen.
- Between body text and the page title at least one step is 1.25 times or more.
- Body line height 1.5 to 1.7, body at least 14 px (16 ideal), labels never under 12 px,
  inputs 16 px on mobile to avoid the zoom on focus.
- Running text capped near 65 characters per line.
- One page container (same maximum width and side padding) on every screen.
- One radius scale with a stated rule (for example controls 8, cards 16, pills full) applied
  everywhere. No card inside a card.
- Targets at least 24 by 24 CSS px, 44 on touch; make the whole row or card clickable when it
  is the action.

## Colour

- Components use theme tokens, never raw values.
- Neutrals slightly tinted toward the primary hue carry backgrounds, surfaces, borders and
  text: about 60 % background, 30 % surfaces and text, 10 % accent.
- One primary colour marks actions. Success, warning and error are semantic and separate from
  the accent.
- Text contrast at least 4.5:1 (3:1 for large text); borders and icons that carry meaning at
  least 3:1.
- Never information by colour alone: pair it with a label or an icon.
- Design light and dark together when the product has both; check each change in both.
- When the user can choose a palette or accent, a new element derives every colour from those
  tokens, including a hero, illustration or gauge. Check it under each palette: an element
  that looks identical under all of them is hard-coded.

## Screen states

Design the states that apply. For a slow initial load, reserve space for the content.
During a refresh, keep cached data readable when it still helps the task. For first-use empty
states, show the next action. For filtered-empty states, offer a way to adjust or clear filters.
On failure, preserve context and offer recovery. If a refresh fails, indicate that the visible
data is stale when recency matters. Check the long case with many items, long labels and large values.

## Forms

- One column. Label above the field, never placeholder as label. Error under the field,
  saying how to fix it, linked with `aria-describedby`, with the input preserved. The submit
  button names the action. Clicking a checkbox or radio label selects it.
- Accept pasted and loosely formatted input (spaces, separators), normalise it, display one
  canonical format.
- Prefer a constrained control (select, date picker, bounded number) to free text.
- Do not ask what the system can deduce; preselect the most likely, least risky value.
- Acknowledge actions promptly and distinguish a pending result from a confirmed one. Announce
  important status changes without moving focus away from the user's task.
- Consider optimistic feedback for frequent reversible edits when rollback and recovery are
  clear. Offer Undo for deletions the product can actually restore.

## Density and frequency

- A tool used daily favours density and stability over spectacle: compact rows, stable
  positions, no celebration on routine actions.
- One or two visible actions per zone, rare actions in an overflow menu, destructive last.
- A component of the same kind sits at the same place on every screen.

## Signatures of generated UI to avoid

Unless the brief or the existing brand asks for them:

- Purple-to-blue gradients, gradient text, coloured glows, radial halos behind sections.
- Everything centred; the same radius and shadow on every block; three identical cards in a row.
- A thick coloured border on one side of a card; an icon in a rounded tile above every heading.
- Tiny uppercase letter-spaced labels above headings; numbered section labels.
- Emoji as icons; decorative status dots; hand-drawn SVG icons instead of the project's icon set.
- Buzzword copy (seamless, empower, supercharge, next-generation) and "Not X. Just Y." lines.
- Copy that repeats what a control already communicates. Keep requirements, consequences and
  actionable recovery instructions visible.
