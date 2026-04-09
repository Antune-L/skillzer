# Principles & Reuse Checklist

Detailed checklist organized by principle. Each item names the signal and the fix.

---

## DRY — Don't Repeat Yourself

| Signal | What to look for |
|--------|-----------------|
| Copy-paste blocks | Two or more blocks with identical or near-identical logic (>3 lines). Diff them — if only names/values change, extract a shared helper or map over a config array. |
| Parallel conditional chains | Multiple `if`/`switch` blocks branching on the same discriminator across files. Consolidate into a lookup table, strategy map, or polymorphic dispatch. |
| Repeated fetch/transform patterns | Same API call + response mapping written in multiple places. Extract into a shared hook (`useXxx`) or service function. |
| Duplicated validation | Same Zod schema, regex, or guard logic defined in multiple locations. Single source of truth — export from one module. |
| Duplicated types/interfaces | Identical or near-identical type definitions across files. Consolidate into a shared types module. |

## SOLID

### S — Single Responsibility

| Signal | What to look for |
|--------|-----------------|
| God component/function | One unit handling fetching, transformation, rendering, AND side effects. Split into container/presenter or extract hooks. |
| Mixed abstraction levels | Business logic interleaved with UI or infrastructure code. Separate layers. |

### O — Open/Closed

| Signal | What to look for |
|--------|-----------------|
| Hardcoded variants | Growing `if`/`else` or `switch` whenever a new variant (status, type, role) is added. Prefer a registry/map pattern where new variants are added declaratively. |

### L — Liskov Substitution

| Signal | What to look for |
|--------|-----------------|
| Type narrowing after abstraction | Code receives a base type then immediately narrows with `instanceof` or discriminated-union checks to alter behavior. Re-examine the abstraction boundary. |

### I — Interface Segregation

| Signal | What to look for |
|--------|-----------------|
| Fat prop interfaces | A component accepts 10+ props but most callers use a small subset. Split into focused, composable components. |
| Unused dependencies | A module imports a heavy package but only uses one function. Import only what's needed or find a lighter alternative. |

### D — Dependency Inversion

| Signal | What to look for |
|--------|-----------------|
| Direct infrastructure coupling | Component directly calls `fetch`, `localStorage`, or a specific ORM method. Abstract behind an interface, hook, or service layer to allow testing and swapping. |

## KISS — Keep It Simple

| Signal | What to look for |
|--------|-----------------|
| Premature abstraction | A generic wrapper/factory created for a single use case. Inline it until 2-3 real consumers exist. |
| Over-engineered patterns | Visitor, Strategy, or Observable patterns where a function call would do. Complexity must earn its place. |
| Unnecessary indirection | A file that re-exports from another without adding value, or a wrapper that just forwards all args. Remove the layer. |
| Overly generic types | Complex generics (`T extends Record<K, V extends ...>`) for a function with one or two concrete callers. Use concrete types until generics are truly needed. |

---

## Reinventing the Wheel — Library & Component Reuse

### Popular libraries to prefer over custom code

Scan for custom implementations that duplicate functionality available in already-installed or widely-adopted packages.

| Domain | Custom code doing... | Prefer |
|--------|---------------------|--------|
| Date manipulation | Manual date arithmetic, formatting with string ops | `date-fns`, `dayjs`, or project's existing date lib |
| Form handling | Manual state + onChange + validation wiring | `react-hook-form`, `formik`, or project's existing form lib |
| Validation | Hand-rolled regex/guard chains | `zod`, `yup`, or project's existing validation lib |
| HTTP client | Raw `fetch` wrappers with retry/interceptor logic | `ky`, `axios`, or project's existing HTTP client |
| State management | Custom pub/sub or context-heavy global state | `zustand`, `jotai`, Redux/RTK, TanStack Query, or project's existing store |
| Tables | Custom `<table>` with sorting/filtering/pagination | `@tanstack/react-table` or project's existing table component |
| Animation | Manual CSS keyframe strings or JS timers | `framer-motion`, `motion`, or CSS transitions |
| Utility functions | Custom `debounce`, `throttle`, `cloneDeep`, `groupBy`, `uniq` | `lodash-es` (tree-shakeable), `remeda`, or native JS equivalents |
| Class merging | Custom className concatenation logic | `clsx`, `cn` (from shadcn utils), `tailwind-merge` |
| ID generation | `Math.random().toString(36)` | `nanoid`, `uuid`, `crypto.randomUUID()` |
| Keyboard shortcuts | Manual `keydown` listeners | `react-hotkeys-hook`, `tinykeys` |
| Clipboard | Manual `document.execCommand('copy')` | `navigator.clipboard` API or project's existing utility |

### UI Component Reuse

Before reviewing, identify the project's component library (shadcn, Radix, MUI, Ant Design, Mantine, etc.) by checking `package.json` and `components/ui/`.

| Signal | What to look for |
|--------|-----------------|
| Custom modal/dialog | `<div>` with `position: fixed` + backdrop + escape handling. Use the project's Dialog/Modal. |
| Custom dropdown/select | `<div>` with toggle state + click-outside + keyboard nav. Use the project's Select/DropdownMenu. |
| Custom tooltip | Hover state + positioned popup. Use the project's Tooltip. |
| Custom toast/notification | Manual state + timeout + animation for messages. Use the project's Toast/Sonner. |
| Custom tabs | Manual active-state toggling between panels. Use the project's Tabs. |
| Custom accordion | Toggle visibility with chevron rotation. Use the project's Accordion/Collapsible. |
| Custom date picker | Calendar grid with date selection. Use the project's DatePicker. |
| Custom data table | `<table>` with manual sorting/filtering headers. Use the project's DataTable. |
| Custom form inputs | Radio groups, checkboxes, switches built from scratch. Use the project's form primitives. |
| Custom command palette | Search input + filtered list + keyboard navigation. Use the project's Command (cmdk). |
| Custom popover | Click-triggered floating content with positioning. Use the project's Popover. |
| Custom sheet/drawer | Sliding panel from edge. Use the project's Sheet/Drawer. |
