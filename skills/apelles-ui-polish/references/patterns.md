# Choosing the component pattern

Most "why did it build a new block instead of a popup" corrections come from picking the
pattern by ease of implementation. Pick it from the user's task, then look for the existing
component that already implements it.

## Order of preference

1. A component that already exists in the product (search the codebase first; the
   `ts-search-first` skill applies). Restyle it, do not write a sibling.
2. A primitive from the component library the project already depends on (shadcn/ui, Radix,
   Base UI, React Aria...). Check `package.json` before assuming it is there.
3. A native platform element: `<dialog>` with `showModal()`, the Popover API
   (`popover` + `popovertarget`), `<details>`, `<input type="date">` when its look is acceptable.
4. A hand-written component, only when none of the above fits. It then owns keyboard support,
   focus management, dismissal and positioning. Say so in the report.

Adding a new library is a decision for the user: propose it, with the reason, before installing.

## Where does the content go

| The user needs to... | Pattern | Not |
|---|---|---|
| Pick a value for a field (date, month, colour, option among many) | Popover anchored to the field: opens next to it, does not move the form, closes on select, Escape and outside click | A block inserted under the form, or a separate section lower on the page |
| Read a short detail about one mark or word | Tooltip (hover and focus) | A click-to-open panel |
| See the detail of an item while keeping the list or calendar in view | Side panel on desktop, bottom sheet on mobile | An inline block below that forces a page scroll; a full page navigation for something glanceable |
| Edit an item or fill a short form | Modal dialog | A new page for three fields |
| Do a long or multi-step task | A page with its own URL | A modal that scrolls |
| Confirm a destructive, irreversible action | Confirmation dialog naming the object | A toast |
| Learn that a reversible action succeeded | Toast with "Undo" | A confirmation dialog before the action |
| Choose among 2 to 5 views of the same data | Tabs or segmented control | A select |
| Choose among many options | Select, or searchable combobox above about 10 options | A long native list for something the product already has a picker for |
| Reveal rarely used settings | Collapsed section in place | A modal |

## Layer rules

- At most three planes: page, surface, overlay.
- An editor opened from a panel stacks above it. The panel stays open and still underneath;
  closing the editor returns to the panel exactly as it was, with no exit and re-entry
  animation.
- Never two modals side by side or a modal that opens another modal for a different task.
- A toast must not be hidden by the open dialog or its footer: render it in the top layer or
  inside the dialog.
- Every layer closes with Escape, has a visible close or Cancel control, returns focus to its
  trigger, and asks before discarding unsaved input.
- A modal takes focus when it opens and keeps Tab inside it; the focused field stays visible
  above a sticky footer and the mobile keyboard.
- Layers follow one stacking order defined once for the product (sticky headers, floating
  buttons, panels, modals, toasts), not ad hoc `z-index` values.
- Mobile: the bottom sheet respects safe areas and never exceeds the viewport height; its
  content scrolls inside.

## Anchored popovers

- Position against the trigger: below by default, flip above when there is no room, clamp to
  the viewport with a margin, gap of 4 to 8 px.
- Measure the popover with its layout size, not `getBoundingClientRect()` while a transform
  animation is running: the animated scale gives a wrong size and a wrong position.
- Re-position on resize and on scroll of any scrolling ancestor, or close on scroll.
- The popover must not change the layout of what is behind it. Check that no field moves when
  it opens.

## Date and period pickers

- A calendar grid, not three selects, when the user thinks in days.
- It can change month and year without stepping twelve times: year navigation or a
  month-and-year header picker.
- Disabled dates look disabled and say why when it is not obvious (out of range, no data).
- Selectable dates and periods come from the product's data and creation rules (existing
  periods plus the next one that can be created), not from an open-ended calendar.
- Opened from a context that implies a date (a clicked day), that date is preselected.
- The week starts on the locale's first day; today is marked; the selected day is distinct from
  today.
- Typing a date still works when the field is a text input.
- If the product already has a month or period picker, the new one reuses its look, its
  options and its navigation.

## Controls and context

- A control appears once, in the scope it affects. A global comparison selector does not get a
  second copy inside a detail panel.
- Information stays at the level of detail where it was readable. A comparison shown in
  calendar cells remains visible there with the detail panel closed; it is not moved into the
  detail.
- If an item can be edited somewhere today, it stays editable there after the redesign.
- Navigation shortcuts that exist (a card that jumps to its month, a button that opens the
  source spreadsheet) are features, not decoration.
- Filters, tabs and pagination live in the URL so Back and reload restore them; active
  filters, the current navigation item and the save state (saving, saved, failed) are visible.
- A tab that only duplicates what another layout already shows at that breakpoint should not
  exist at that breakpoint.
