# Frontend Conventions

<!-- Adapt to your actual stack -->

Stack: React + [Vite / Next.js] + TanStack Query + [shadcn/ui / your UI lib]

## React

- Function components only, explicit props types (no `React.FC`)
- Avoid `useEffect` — use as last resort
- Prefer separate components over `render*()` functions — they can use hooks, appear in DevTools, and can be memoized
- Use `cn()` for class merging
- Use the `vercel-react-best-practices` skill
- Before creating a new component, check if it already exists

## Forms

- react-hook-form with `zodResolver` for validation
- Wrap fields in `Controller` using typed field components (`InputField`, `DatePickerField`...)

## Data Fetching

- TanStack Query for all server state
- Invalidate broadly after mutations (router-level keys, not method-level)

## Styling

- `cn()` for class merging
- Avoid pixel values in Tailwind — prefer scale tokens (`max-h-100` over `max-h-[400px]`)

## State Management

- TanStack Query for server state
- [Zustand / URL params] for client state
- Avoid prop drilling beyond 2 levels — extract context or compose
