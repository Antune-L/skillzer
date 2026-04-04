# Regression Check Checklist

Categorized verification steps by change type. For each category, use the grep patterns to
find consumers, then apply the verification steps.

---

## 1. Type / Interface Change

**Find consumers:**
```
grep -r "import type.*{.*TypeName" --include="*.ts" --include="*.tsx"
grep -r ": TypeName" --include="*.ts" --include="*.tsx"
grep -r "as TypeName" --include="*.ts" --include="*.tsx"
grep -r "satisfies TypeName" --include="*.ts" --include="*.tsx"
```

**Verify:**
- [ ] All destructured properties still exist on the new type
- [ ] No removed/renamed fields referenced in consumer code
- [ ] Generic type parameters still match (count and constraints)
- [ ] Discriminated unions — check exhaustive switches/if-chains cover new variants
- [ ] Zod schemas derived from the type still match

---

## 2. Function Signature Change

**Find consumers:**
```
grep -r "functionName(" --include="*.ts" --include="*.tsx"
grep -r "functionName," --include="*.ts" --include="*.tsx"   # passed as callback
```

**Verify:**
- [ ] Argument count matches new signature
- [ ] Argument types match (especially if param was narrowed/widened)
- [ ] Return type consumers handle the new shape
- [ ] Default parameter removal — callers that relied on the default now pass explicitly
- [ ] Overloads — all overload signatures updated consistently

---

## 3. Symbol Rename

**Find stale references:**
```
grep -r "oldSymbolName" --include="*.ts" --include="*.tsx" --include="*.json"
```

**Verify:**
- [ ] Zero remaining references to old name across entire monorepo
- [ ] Re-exports in barrel files (`index.ts`) updated
- [ ] String references (API paths, error messages, logging) updated
- [ ] Test files reference new name
- [ ] Config files (`.env`, JSON configs) reference new name if applicable

---

## 4. Symbol Deletion

**Find orphaned imports:**
```
grep -r "import.*{.*deletedSymbol" --include="*.ts" --include="*.tsx"
grep -r "from ['\"].*moduleWithDeletion['\"]" --include="*.ts" --include="*.tsx"
```

**Verify:**
- [ ] Zero remaining imports of deleted symbol
- [ ] No re-exports of deleted symbol in barrel files
- [ ] Consumers have replacement or have been updated to not need it

---

## 5. Database Schema / Prisma Change

**Trace the full stack:**
```
# 1. Service layer
grep -r "prisma\.modelName" --include="*.ts"
grep -r "changedFieldName" --include="*.service.ts" --include="*.repository.ts"

# 2. DTOs / validation
grep -r "changedFieldName" --include="*.dto.ts" --include="*.schema.ts"

# 3. Controllers / resolvers
grep -r "changedFieldName" --include="*.controller.ts" --include="*.resolver.ts"

# 4. Frontend hooks
grep -r "changedFieldName" --include="*.ts" --include="*.tsx" path/to/frontend/

# 5. Frontend components
grep -r "changedFieldName" --include="*.tsx" path/to/frontend/
```

**Verify:**
- [ ] Migration file exists and is correct
- [ ] Service layer uses new field name
- [ ] DTOs reflect new field (request AND response)
- [ ] Frontend API hooks send/receive correct field names
- [ ] UI components display/bind correct field names
- [ ] Seed data / fixtures updated

---

## 6. API Endpoint Change

**Find frontend consumers:**
```
grep -r "endpoint/path" --include="*.ts" --include="*.tsx"
grep -r "useQuery.*queryKey" --include="*.ts" --include="*.tsx"
grep -r "useMutation.*mutationKey" --include="*.ts" --include="*.tsx"
```

**Verify:**
- [ ] Request payload shape matches new DTO
- [ ] Response handling matches new response shape
- [ ] Query key invalidation still correct
- [ ] Error handling accounts for new error cases
- [ ] URL params / path segments match new route

---

## 7. Zod Schema Change

**Find consumers:**
```
grep -r "schemaName\.parse" --include="*.ts" --include="*.tsx"
grep -r "schemaName\.safeParse" --include="*.ts" --include="*.tsx"
grep -r "z\.infer.*schemaName" --include="*.ts" --include="*.tsx"
grep -r "schemaName\.shape" --include="*.ts" --include="*.tsx"
```

**Verify:**
- [ ] All `parse`/`safeParse` call sites pass data matching new shape
- [ ] `z.infer<typeof schema>` consumers handle new fields
- [ ] Composed schemas (`.merge`, `.extend`, `.pick`, `.omit`) still valid
- [ ] Default values still appropriate
- [ ] Transform/refine/preprocess pipelines compatible with new shape

---

## 8. Shared Component / Hook Change

**Find consumers:**
```
grep -r "import.*ComponentName" --include="*.tsx"
grep -r "import.*useHookName" --include="*.ts" --include="*.tsx"
grep -r "<ComponentName" --include="*.tsx"
```

**Verify:**
- [ ] Props match new interface (added required props provided, removed props not passed)
- [ ] Hook return value destructuring matches new shape
- [ ] Callback signatures match new types
- [ ] Ref forwarding still works if component uses `forwardRef`
- [ ] Context value shape matches if context provider changed
