# Detail defects: symptom, cause, fix

Every row below was reported by a user on real agent-built UI. Each one was visible in a
screenshot the agent could have taken. Check them on the rendered page, never by reading code.

## Contents

- Text and numbers
- Alignment and spacing
- Height, scroll and empty space
- Hover and pointer
- Data visualisation
- Copy

## Text and numbers

| Symptom | Usual cause | Fix |
|---|---|---|
| A value sticks out of its container (amount outside a donut centre, label outside a card or cell) | Container has a fixed size; content was only tried with a short sample value | Size the container from the longest realistic value, or let the text shrink with `clamp()` and container query units. Test with the largest amount, a negative amount and the longest label of the dataset. |
| A flex or grid child pushes its parent wider than the screen | Flex and grid items default to `min-width: auto`, so a `nowrap` child cannot shrink | `min-width: 0` on the flex child, `minmax(0, 1fr)` instead of `1fr` on the grid track. |
| Text is cut with no ellipsis | `overflow: hidden` used to hide a layout problem | Either let it wrap, or truncate on purpose: `text-overflow: ellipsis` (one line) or `line-clamp` (several), and give the full value a reveal that works with touch and keyboard (tooltip on focus, detail view); a `title` attribute alone is not enough. Never truncate an amount or a date. |
| A lone word on the last line of a heading | Default wrapping | `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs. |
| Digits jump or columns of amounts look ragged | Proportional digits | `font-variant-numeric: tabular-nums` on every amount, counter, KPI and table number; right-align numeric columns. |
| Text reads too thin, or amounts too widely spaced | Light weight at small size, or letter spacing applied to numbers | Body at 400 to 500 minimum on small sizes, check on a non-retina rendering; no positive letter spacing on numbers. |
| In a dense cell the key figure does not stand out | Same weight for the value and its supporting labels | Judge the weight of primary values separately from body text: at actual size, the amount in a calendar cell or KPI is visibly heavier than what surrounds it. |
| Cents dropped, or separators differ between screens | Several ad hoc formatters | One formatting function per kind of value, reused everywhere; when a compact form is needed (calendar cell), make it a named variant of that function. |
| Straight quotes and apostrophes in visible copy | Typed from the keyboard | Typographic apostrophes and quotes in user-facing strings. |

## Alignment and spacing

| Symptom | Usual cause | Fix |
|---|---|---|
| Values of a list or legend do not share an edge | Each row is its own flex line | One grid for the whole list with shared columns (`grid-template-columns: auto minmax(0, 1fr) auto auto`, rows with `display: contents` or `subgrid`). |
| Icon buttons in a header sit at different heights | Mixed box sizes, line heights or icon sizes | Same box size for every icon button, `display: grid; place-items: center`, one icon size and weight. Verify by comparing the centre of each bounding box. |
| Navigation icons sit slightly above or below the logo | Inline SVG inside a span sits on the text baseline; only icon buttons were compared with each other | `display: block` on the SVG, `display: grid; place-items: center` on its wrapper. Compare the centre of every item of the bar with the logo's centre, within 1 px, at each breakpoint where the bar changes layout. |
| Two buttons look glued together | Gap of 2 to 4 px, often reset by a later rule | At least 8 px between separate controls (12 px on desktop), or join them on purpose into one group with a shared border. Read the computed `gap`. |
| A tab or segment label touches its edge or its neighbour | Equal-width segments (`flex: 1; min-width: 0`) with one longer label | Size segments from their content (`minmax(max-content, 1fr)`), keep 8 px or more of inner padding, let the control scroll or wrap when it no longer fits. Check every tab set of the product, not only the first view's. |
| Two blocks that belong together look unrelated, or the reverse | Equal gaps everywhere | Gap between groups at least twice the gap inside a group; container padding at least the gap between its children. |
| A stacked bar shows separate pills instead of one bar | Radius applied to each segment | Radius and `overflow: hidden` on the bar wrapper, none on the segments; segments touch. |
| List rows each have their own rounded card | Card reflex | One surface for the list, rows separated by spacing or one hairline, radius on the surface only. |

## Height, scroll and empty space

| Symptom | Usual cause | Fix |
|---|---|---|
| The user must scroll the page to reach the detail of what they just clicked | Detail rendered below the trigger in the page flow | Show it in a layer (see `patterns.md`), or in a region that is already visible. |
| An app screen scrolls as a whole although it is a workspace | No height budget | For workspace screens, lay out to `100dvh` with one scrolling region per column; long lists scroll inside their own region. Decide this once per screen and state it. |
| Two scrollbars, or horizontal plus vertical scroll in one zone | Nested `overflow: auto` containers, or a wide child in a vertical scroller | One scroll container per axis per zone. Remove the inner one or let the content reflow. `overflow-x: hidden` on a scroller is a patch: find the child that is too wide. |
| A big empty hole on a large screen, or content floating mid-height | A flex child stretched (`flex: 1`) with centred content | Let blocks take the height of their content and leave the free space at the end, or give the extra space to the element that benefits from being bigger (a chart, a list). Check at 1920 and 2560 px wide, and at 3840 px when the user works on 4K. |
| A hole next to a short list while a neighbour is cramped | Fixed heights (`height: 130px`, `max-height: 180px`) chosen at one viewport | Replace magic heights with content sizing plus `min-height` and `max-height` expressed against the container. |
| Centred content gets cut at the top when it overflows | `justify-content: center` on a scrolling flex column | `justify-content: safe center`. |
| A wide table breaks the page on a phone | Table forced into the page width, or the page scrolls sideways | Page content reflows down to 320 CSS px. A table or map that needs both axes scrolls inside its own container, with cell text allowed to wrap. |
| Layout shifts when a scrollbar appears | Scrollbar takes width | `scrollbar-gutter: stable` on the scroller. |

## Hover and pointer

| Symptom | Usual cause | Fix |
|---|---|---|
| A button moves when hovered and its neighbours or the pointer target shift | `transform: translateY()` or a size change on `:hover` | Hover changes colour, background, border colour or shadow only. Keep any press effect to a scale of 0.97 or more on `:active`, never a translation. |
| Clickable things with no reaction | Hover state forgotten on custom elements | Every clickable element has `:hover`, `:focus-visible` and `:active` states: tabs, segmented options, calendar cells, legend rows, chart marks, cards. Missing hover on one sibling out of several reads as a bug. |
| A tooltip hides what the pointer is on | Tooltip centred on the pointer | Offset it from the pointer (about 16 px) and flip at the viewport edges. A readout that follows the pointer over a chart takes `pointer-events: none`; a tooltip attached to an element stays open while the pointer moves onto it or focus stays on its trigger, and Escape dismisses it. |
| A tooltip flickers or re-animates while the pointer moves | Entry animation tied to position updates | Animate on appear only; update position without restarting the animation. |
| A tooltip that repeats what is already visible | Tooltip added everywhere | A tooltip adds information. If the mark already shows its single value, show nothing; open a detail only for aggregates ("Other", "+3"). |
| Hover is the only way to reach an action or a value | Desktop-only thinking | Same information on tap and on keyboard focus; row actions stay visible on touch. |

## Data visualisation

| Symptom | Usual cause | Fix |
|---|---|---|
| The readout shows the 9th when the pointer is on the 8th | Pointer mapped with the container width, ignoring SVG margins and scaling | Convert the pointer with the same transform used to draw: the SVG's `getScreenCTM().inverse()`, then the scale's inverse. Verify at two widths by pointing at a known data point. |
| A hovered slice or point is clipped | SVG clips its overflow | `overflow: visible` on the SVG, with padding in the layout for the enlarged mark. |
| A chart lost its hover readout or its comparison after a restyle | Rewritten instead of restyled | Restyle the existing chart component and keep every interaction it had. |
| Axis ticks waste space or show values far outside the data | Generic nice-step algorithm | Three to five ticks bounded to the data range, light horizontal grid, values written on the marks when there are few. |
| Bars exaggerate small differences | Quantitative axis not starting at zero | Bars start at zero; lines may use a bounded range. Pick ticks that mean something for the scale. |
| A missing day looks like a zero | Missing observations drawn as 0 | Draw gaps for missing data; distinguish zero, unavailable and loading. |
| Category colours change between themes or between two charts | Colours assigned by index per chart, or theme overrides | One category-to-colour map for the whole product, identical in light and dark unless contrast fails. |
| A legend is far from the chart or misaligned with it | Legend laid out independently | Legend adjacent to the chart, centred on it or directly below; legend rows follow the list grid rule above. |

## Copy

- Remove descriptions that backseat the user: sentences that explain the interface, say what
  to click or how to read a zone ("Days without data are greyed out. Select a day to see its
  detail."). If it is well built, it needs no explanation; if a sentence seems needed, fix the
  screen.
- This targets commentary, not content the user needs to act: field labels, required formats,
  units, chart legends, consequences of an action and error messages stay visible next to
  what they describe, never hidden in a tooltip.
- Rare last resort for a notion that cannot be made self-evident (a computed metric, a
  business rule): a small info icon (i) beside the label, with the explanation in a tooltip on
  hover and focus. One or two per screen at most.
- Labels survive longer text: try the longest translation the product supports in the
  narrowest buttons, tabs and dialogs.
- Keep the product's existing vocabulary. One word for one action across every screen.
- Button labels name the action. No filler, no invented metrics, no placeholder names.
