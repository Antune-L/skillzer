---
name: apelles-ui-polish
description: Use when visually designing, redesigning, polishing or animating a product screen or component (app, dashboard, form), or making an HTML mockup of it - "refonte visuelle", "améliore le visuel / les animations", "rends ça moins générique / moins slop", "maquette html", "apelles". Not for landing pages (design-taste-frontend), mockup comparisons (mockup-fidelity-review) or purely functional fixes.
---

# Apelles UI Polish

Design for the task and the product's existing identity. Apply these defaults where they fit the
screen and respect the user's explicit choices.

- Read [foundations](references/foundations.md) for task design, hierarchy, spacing, states and forms.
- Read [patterns](references/patterns.md) to choose a component for a task.
- Read [details](references/details.md) for rendering defects and their likely causes.
- Read [motion](references/motion.md) when designing or changing transitions.

## Start with the task

Name the task in the user's terms, how often it occurs, what counts as success and where the
user resumes after leaving or being interrupted. For example, a billing clerk finds the March
invoice, corrects its reference, sees the save confirmed and resumes from the same row and
filters. Use this to decide what to keep visible and which selection, input, scroll position
and keyboard focus should survive the task.

## A restyle keeps everything the screen did

- A redesign changes how things look, not what the user can do. Every section, value, hover
  readout, edit action, selector and shortcut of the current screen exists in the new one.
- Removing or merging something is a product decision: propose it, never do it silently.
- An existing product keeps its tokens, fonts, icons, wording and themed elements (a tape mask
  stays a tape mask, it does not become a blur), unless that element is itself under review.
- When the user can pick a theme, palette or accent, every new element follows it, hero and
  decorative ones included. A signature element with its own fixed colours is a defect.
- Restyle the existing component instead of writing a simpler sibling. A new picker next to an
  existing picker is a regression in consistency and usually in capability.

## The component follows the user's task

- Choosing a value for a field with a custom picker (date, month, colour): a popover anchored
  to that field. It opens next to it, moves nothing, closes on select. Never a block inserted
  in the page flow. Plain option lists stay a select or combobox.
- Detail of an item while the list or calendar stays in view: side panel on desktop, bottom
  sheet on mobile. Never content below the fold that forces a scroll.
- Short edit: modal. Long task: page. Short explanation of one mark: tooltip.
- An editor opened from a panel stacks above it; the panel stays open underneath and does not
  replay its entrance when the editor closes.
- A control appears once, in the scope it affects.
- A calendar can change month and year directly, preselects the date implied by the context,
  and looks like the product's other pickers.

## Space is designed at every size

- Decide per screen which region scrolls and which element absorbs extra space. One scroll
  container per axis per zone. Keep any necessary two-dimensional scrolling local to the
  content that requires it, such as a wide data table.
- Blocks take the height of their content. Stretching a block and centring its content creates
  a hole on a large screen; give extra room to what benefits from it (a chart, a list).
- No magic heights tuned at one viewport. Check a short phone (375 × 667) and a
  wide desktop (2560 px or more) where those sizes fit the product.
- Related things are close, unrelated things are apart: the gap between groups is at least
  twice the gap inside a group.
- Separate adjacent controls are at least 8 px apart, unless deliberately joined into one
  group with a shared border. A label keeps at least 8 px from the edge of its button, tab or
  segment; segments are sized from their longest label, not as equal fractions.
- Siblings share edges: the values of a list or legend sit in common columns, icon buttons in
  a row share one box size and one centre line.
- Everything in one bar shares one centre line, across groups: logo, navigation icons, labels
  and action buttons, within 1 px.

## Text and numbers never fight their container

- Size containers from the longest realistic value (largest amount, negative amount, longest
  label), never from the sample on screen.
- Text either wraps or is truncated on purpose with an ellipsis and access to the full value.
  Amounts and dates are never truncated.
- Every amount, counter and table number uses tabular figures; numeric columns align right.
- One formatter per kind of value across the product.
- Text is never thinner or smaller than the product's body token; key figures are heavier
  than their labels; no letter spacing on numbers.
- Remove captions that repeat an obvious action, such as “Select a day to see its detail.”
  Keep labels, formats, units, legends, consequences
  and corrections visible where they are needed. Put optional explanations in help that users
  can open by pointer or keyboard.

## Everything interactive answers

- Every clickable element has hover, focus-visible and pressed states, including custom ones:
  tabs, segmented options, calendar cells, legend rows, chart marks, cards.
- Hover never moves the element or its neighbours: change colour, background, border colour or
  shadow, not position or size.
- A tooltip sits beside the pointer, never under it, flips at the edges, and only appears when
  it adds information.
- What hover reveals is also reachable by tap and keyboard.
- A chart readout matches the point under the pointer at every width, and a restyled chart
  keeps its hover and comparison behaviour.

## Motion explains the relationship

- Design the start and end states first. Decide whether the change follows the same object,
  moves through an ordered sequence, changes state, follows a gesture or switches between
  independent views. Name the visual anchor, where attention lands and what stays still.
- Use roughly 100–300 ms as a starting range for short transitions. Keep frequent actions
  responsive, including instant changes where suitable. Move directly with the pointer during
  a drag. Choose similar behavior for interactions that have the same meaning.
- When the brief calls for expression, choose a meaningful moment and a visual motif the
  product already uses. Describe the recognizable result after the effect and how the motion
  feels after ten repetitions.
- Verify that reversing mid-flight starts from the current visible state. The latest navigation
  choice determines the destination even if an earlier request returns later. Reduced motion
  preserves information, available actions and the destination.

## Checking the result

Check rendered loading, empty, error and populated states. Use representative phone and
desktop sizes, each supported theme, keyboard-only interaction and 200% zoom. For vertically
scrolling content, also check reflow at 320 CSS px (layout pixels), with no loss of information
or functionality and no horizontal scrolling except where the content requires two dimensions.
Offer a click or tap alternative to dragging unless an exception applies,
such as when dragging is essential. Use a screen reader to check that meaningful status changes
are announced.
[WCAG reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow) · [Dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements) · [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages)

Try a realistic task that includes leaving and resuming. During a transition, reverse halfway,
select another item and return. Where requests can overlap, make the first response arrive
last. Verify the destination, selection, input, scroll position and keyboard focus. Repeat with
reduced motion and keyboard alone. When evaluating usability with a participant, give the task
without naming the controls and record unassisted completion, hesitation, backtracking and errors.

One view checked is not a screen checked. The same checks apply to every page, every tab set,
every open layer (dialog, panel, picker) and every selectable palette, at phone and desktop
width: defects hide in the views that are not the landing one. Gaps and centre lines are
measured on the render (bounding boxes), not judged by eye: a 2 px offset is invisible on a
full-page screenshot and obvious to the user.

`scripts/layoutAudit.js` is a single arrow function to evaluate in the page through the
browser tool. It returns `viewport`, `pageScroll`, `counts` (full totals) and one list per
category capped at 25 examples: `clippedText`, `spilledText`, `offscreen`, `nestedScroll`,
`smallTargets`, `noHoverState`, `hoverMovesLayout`, `nonTabularNumbers`,
`slowOrLinearMotion`, `crampedSiblings` (adjacent controls under 8 px apart), `offAxis`
(marks of one bar off its centre line). Use the output as leads for rendered checks. Judge
hierarchy, whitespace, visual continuity and task completion by observing the screen and
interacting with it. Inspect flagged examples and fix or explain any that remain.

A mockup or demo is only testable with enough varied, connected sample data to exercise each
interaction: several periods and years, comparisons, aggregates ("Other"), empty and
overloaded days, extreme amounts and labels. Fictional data, never the user's.

## Gotchas

- **`min-width: auto` on flex and grid children.** A `nowrap` child widens its parent past the
  screen. Use `min-width: 0` on the child and `minmax(0, 1fr)` on the track; `overflow-x:
  hidden` on the parent only hides it.
- **`justify-content: center` on a scrolling column cuts the top.** Use `safe center`.
- **Fit-to-viewport and fill-the-large-screen are one decision.** Constraining height to avoid
  page scroll, then stretching to fill, produces the hole reported on the next screen size.
- **Radius on each segment of a stacked bar** shows separate pills. Radius goes on the wrapper.
- **Pointer-to-data conversion that ignores SVG margins** shifts the readout by one point. Use
  the SVG's own screen matrix.
- **Measuring a popover while its scale animation runs** gives a wrong size and position.
- **A standalone HTML mockup has no component library**, so pickers and layers get reinvented
  in a weaker form that the app then inherits. Give them the behaviour of the real component.
- **Audit script limits.** It does not enter shadow roots or iframes, and cannot read
  external stylesheets on a `file://` page, cross-origin ones, or `adoptedStyleSheets` (false
  `noHoverState`). It flags re-declared properties in `hoverMovesLayout` and isolated years in
  `nonTabularNumbers`. `crampedSiblings` ignores tile grids and controls separated by another
  element; `offAxis` only looks at rows under 96 px tall and under-reports when a bar has two
  marks or when most marks are shifted. A resized headless Chrome window keeps a layout width near 500 px
  minimum; viewport emulation (Playwright `setViewportSize`, DevTools device mode) gives exact
  phone widths. Read the `viewport` field before concluding about phone widths. Inspect
  `slowOrLinearMotion` in context. A deliberate, interruptible transition can be valid.
- **A browser MCP may refuse `file://` pages.** Serve the mockup locally, or run the audit
  from a local Playwright script: read the file and evaluate `'(' + source + ')()'`.
- **A later rule of equal specificity silently resets a spacing** (a header `gap` back to
  2 px). Read the computed value on the render, not the first declaration found.
- **Inline SVG sits on the text baseline**, a few pixels off its neighbours' centre. Make the
  SVG `display: block` and centre it in its wrapper with grid.
- **Fullscreen mobile windows can mask invalid desktop geometry.** When mobile CSS overrides
  the window position and size, defer desktop geometry until entering desktop mode. Verify the
  same open window across the breakpoint, including keyboard focus on overlays.
- **Auditing a file another agent is still editing** gives stale results. Check after the
  last write.
