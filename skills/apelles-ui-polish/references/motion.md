# Motion

## Compose the change

Sketch the start and end states. Identify the object the user is tracking and what should
stay still. Choose movement to match the relation between the states.

| Relationship | Motion to try | What stays clear |
|---|---|---|
| Same object | Carry a recognizable part of the selected card into its detail. | Keep global navigation still and the title readable. |
| Ordered sequence | Slide a calendar grid in the next or previous direction. | Keep month controls in place. |
| Change in state | Move a selected row to its new rank or slide a selection indicator. | Keep headers still and show the final order immediately after the effect. |
| Direct gesture | Move a sheet with the finger and settle it at release. | Keep scrolling usable and offer a visible close button. |
| Independent views | Switch directly or use a short fade. | Place focus where the user can continue. |

Use the same cue for equivalent interactions. A quiet dashboard may need only selection and
feedback. An important, infrequent outcome can carry a more expressive accent.
[Google Design examples](https://design.google/library/making-motion-meaningful) · [Material motion patterns](https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md)

Check entry and exit across each family of layers. Anchor a popover's expansion at its
trigger. Bring a side panel in from its edge. A chart plays its entrance once and keeps
its place when a sibling updates. Pair an error or success cue with a specific message.

## Set the rhythm

Start around 100–150 ms for local feedback, 150–200 ms for a small layer and 200–300 ms
for a larger change. Tune for frequency, distance and control. Repeated keyboard actions
can be instant. Separate how long a visual effect runs from how soon users can continue.
A larger transformation can take longer when users can interrupt it and act promptly.
Reuse the project's tokens for equivalent interactions.

Ease into the landing position for arrivals. A permanent exit can accelerate. During a
drag, follow the pointer directly. On release, a damped spring can carry the release speed
into the target with little overshoot. [Carbon durations and easing](https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview) · [Apple on gestures and interruptions](https://developer.apple.com/videos/play/wwdc2018/803/) · [Apple on springs and velocity](https://developer.apple.com/videos/play/wwdc2023/10158/)

## Put expression where it helps

- **Card to detail.** Save the list context. Keep the cover recognizable as it grows into
  the detail and reveal the supporting text when its column is ready. If data is slow,
  show the identity already available and reserve room for the detail. Offer retry on
  failure and keep Back available throughout. Restore the card and reading position on
  return. If the card disappeared, focus a useful point in the list and use a direct return.
- **Move a board card.** Move the selected card as nearby cards make room. Offer a Move
  control that works by click or keyboard. If the target is outside the viewport, show its
  name in the confirmation. Keep the result recognizable with reduced motion.
- **Explain a chart aggregate.** Let marks collect into their groups, then show the totals
  if the task is to understand the calculation. For quick comparison, leave values
  simultaneously visible and keep the scale stable where possible.
- **Reveal a confirmed result with a product motif.** Use the edge of an existing ticket as a
  mask for a reservation confirmation, with the surrounding screen still. Trigger it after
  confirmation. The final ticket carries the same wording and actions after the effect and
  with reduced motion. Replay the task ten times and check that the next action stays available.

Watch [object constancy during sorting](https://bost.ocks.org/mike/constancy/),
[dragging a mobile sheet](https://emilkowal.ski/ui/building-a-drawer-component) and
[animated grouping](https://idl.uw.edu/papers/animated-aggregate-operations). Some chart
transitions help people follow a transformation. Keep a static view available when the task
is comparing trends or values. [Heer and Robertson on transitions](https://idl.uw.edu/papers/animated-transitions) · [Robertson and colleagues on trend comparison](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tvcg2008-trendvis.pdf)

## Handle interruption and reduced motion

- Start a reversal or new transition from the visible position. Take the latest navigation
  choice as the destination. Bind data and pending feedback to their corresponding item or
  request so a late response cannot overwrite the newer view. Keep save confirmation tied
  to the actual save outcome.
- Tie focus and control availability to the state change, including when animations are
  skipped or cancelled. Restore focus to the opener when useful, or to a logical successor
  if it no longer exists. A layer underneath an editor keeps its position when the editor
  closes. [W3C modal dialog focus guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- Honor `prefers-reduced-motion: reduce` in CSS and in any motion driven by JavaScript.
  Remove non-essential spatial motion and stagger. Use the final state immediately or a
  subtle opacity change where useful. Keep names, selected state, progress or outcome text,
  available actions, focus and return location. For a gesture, retain direct control where
  needed and skip decorative travel or bounce on release. [WCAG animation from interactions, AAA](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions)
- In the browser, reverse halfway, select another item during loading and make the first
  response arrive last. Return to the list, check focus and repeat by keyboard and with
  reduced motion enabled. Verify a failed load or save has a route back to the task.

## Choose the technique

- Use an existing CSS transition for local changes. Update a pointer-following tooltip's
  position without replaying its entry. If using a CSS transition from `display: none`, use
  `@starting-style` for the starting values and `transition-behavior: allow-discrete` if
  transitioning `display` itself.
- For list reordering, measure positions before and after the change, visually offset each
  item to its previous position and animate it to its new one (FLIP). Match items by stable
  identity and check size changes. [Paul Lewis's FLIP demonstration](https://aerotwist.com/blog/flip-your-animations/)
- For a shared element between views, consider browser view transitions. Verify that the
  associations are unique, proportions remain readable and the underlying task works when
  the feature is unavailable. [Chrome view transition examples](https://developer.chrome.com/docs/web-platform/view-transitions/same-document)
- Prefer transforms for position and opacity for fades. Size changes can trigger layout
  (recalculating geometry), and large blurs and shadows can cost time to draw. Record a
  performance trace with realistic data and reduce the most expensive effect if frames
  are missed. Measure base geometry before applying transforms.
  [Web animation performance guide](https://web.dev/articles/animations-guide)

Use the project's existing tools. Propose a new dependency only when a chosen effect needs
capabilities the stack lacks. Avoid decorative loops, parallax and effects that take over
scrolling or repeatedly move content people are reading.
