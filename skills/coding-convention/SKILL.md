---
name: coding-convention
description: "Enforce project coding conventions: reduce duplication, keep naming/file placement consistent, and minimize regression risk. Includes React component and layout guidelines. Use when writing or reviewing code."
---

# Coding Conventions

## Summary

- Reduce duplication, complexity, API surface, and regression risk.
- Code must stay consistent with the rest of the project — file placement, naming (files, variables, functions).
- Use TODO(ali) prefix for TODOs in code.

## React components

When writing a React component, prioritize existing project libraries (shadcn, Phosphor icons,
Tailwind) over custom implementations if they speed up implementation and produce clean results.

### Layout: prefer flex over grid

Use **flexbox** (`flex`, `flex-col`, `flex-row`) by default for layouts.
Only use `grid` when the layout is truly tabular (columns and rows aligned across independent rows) or when CSS grid offers a concrete advantage that flex cannot easily reproduce.

```tsx
// ✅ DO — layout avec label fixe + contenu flexible
<div className="flex gap-5">
  <h2 className="w-55 shrink-0">Section</h2>
  <div className="flex-1">...</div>
</div>

// ✅ DO — paires label/valeur
<div className="flex gap-4">
  <dt className="w-40 shrink-0 text-sm font-medium text-gray-500">Label</dt>
  <dd className="flex-1 text-sm text-gray-900">Valeur</dd>
</div>

// ❌ AVOID — grid pour un layout simple à deux colonnes
<div className="grid grid-cols-2 gap-4">
  <dt>Label</dt>
  <dd>Valeur</dd>
</div>
```

## Details

**Checklist**: See [checklist.md](checklist.md) for a consistency reference.
