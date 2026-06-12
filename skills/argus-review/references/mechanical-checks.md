# Mechanical pre-pass — deterministic seeding

The highest-frequency findings in this codebase are **mechanically detectable** (banned `as` cast, hardcoded text/locale, `cn` misuse, native dialogs). Greping for them is deterministic and free of LLM variance. Argus runs this pass **before** dispatch and seeds the **conventions** reviewer with the hits, so recall on the top category does not depend on a model noticing.

This pass produces **candidates**, not verdicts. The conventions reviewer verifies each against rule source + diff context and drops false positives. False positives here are cheap; misses are not.

## Ignore list — strip from the diff before dispatch

These are generated/lock/snapshot noise. Strip the matching files from the patch you pass to reviewers, and state what was dropped:

```
*.lock  bun.lock  pnpm-lock.yaml  package-lock.json  yarn.lock
**/snapshot.json   **/*.snap
**/*.gen.ts        **/routeTree.gen.ts
**/paraglide/**    **/generated/**
**/dist/**         **/.turbo/**   **/node_modules/**
```

Do **not** strip (review normally, but conventions reviewer skips their import-order/naming):
- `**/components/ui/**` (shadcn autogen — may be hand-edited; keep for security/regression)
- `**/migrations/**` (hand-written SQL is reviewable; pure generated DDL is noise)
- locale message files `**/messages/*.json` (needed for i18n parity check)

## Build the changed-file set

```bash
BASE=<base>; BRANCH=<branch>          # or use --cached for staged
git diff --name-only "$BASE...$BRANCH" \
  | grep -vE '\.(lock|snap)$|snapshot\.json$|\.gen\.ts$|/paraglide/|/generated/|/dist/|/\.turbo/' \
  > /tmp/argus_files.txt
```

## Capability detection (run once, gate the folded checks)

Folded sub-checks must only fire when the project has the capability. Resolve these flags deterministically in the parent and pass them into every dispatch. **Off → the reviewer skips that sub-check.** Detect from the repo root, not just the diff (a project either has i18n or it does not).

```bash
ROOT=$(git rev-parse --show-toplevel)

# i18n: an i18n library OR a locales/messages dir with translation files
i18n=off
if rg -lq -e 'paraglide' -e '"i18next"' -e 'react-intl' -e 'next-intl' -e 'vue-i18n' -e '@formatjs' -e 'use-intl' \
     "$ROOT"/package.json "$ROOT"/apps/*/package.json "$ROOT"/packages/*/package.json 2>/dev/null \
   || find "$ROOT" -type d \( -name messages -o -name locales \) -not -path '*/node_modules/*' 2>/dev/null | grep -q . ; then
  i18n=on
fi

# frontend / a11y: JSX/markup present
frontend=off
if find "$ROOT" -name '*.tsx' -o -name '*.jsx' -o -name '*.vue' -o -name '*.svelte' 2>/dev/null | grep -vq node_modules; then frontend=on; fi

# react
react=off; rg -lq '"react"' "$ROOT"/package.json "$ROOT"/apps/*/package.json "$ROOT"/packages/*/package.json 2>/dev/null && react=on

# payments
payments=off; rg -lq -e '"stripe"' -e '@stripe/' -e 'paypal' -e 'checkout\.session' "$ROOT"/package.json "$ROOT"/apps/*/package.json 2>/dev/null && payments=on

# monorepo
monorepo=off; [ -f "$ROOT/turbo.json" ] || [ -f "$ROOT/turbo.jsonc" ] || [ -f "$ROOT/pnpm-workspace.yaml" ] || rg -lq '"workspaces"' "$ROOT/package.json" 2>/dev/null && monorepo=on

echo "i18n=$i18n frontend=$frontend react=$react payments=$payments monorepo=$monorepo"
```

## Stack manifest (libs for the quality reviewer's library check)

Detect which libraries from `library-practices.md` the repo actually uses, with the **major
version** when the checklist is version-sensitive (zod v3 vs v4). One pass over the manifests:

```bash
LIBS=""
for lib in zod @tanstack/react-query drizzle-orm prisma @elysiajs/eden @trpc/client react-hook-form; do
  spec=$(rg --no-filename -o "\"$lib\"\s*:\s*\"[^\"]+\"" \
        "$ROOT"/package.json "$ROOT"/apps/*/package.json "$ROOT"/packages/*/package.json 2>/dev/null | head -1)
  [ -z "$spec" ] && continue
  # "catalog:" / "workspace:*" specs have no digit — keep the lib, versionless
  v=$(echo "$spec" | rg -o ':\s*"[^"]*?([0-9]+)' -r '$1' | head -1)
  case $lib in
    @tanstack/react-query) name=tanstack-query ;;
    @elysiajs/eden)        name=eden ;;
    @trpc/client)          name=trpc ;;
    drizzle-orm)           name=drizzle ;;
    *)                     name=$lib ;;
  esac
  LIBS="$LIBS $name${v:+@$v}"
done
echo "libs=$(echo $LIBS | tr ' ' ',')"
```

The emitted names match the section titles in `library-practices.md` — that mapping is what the
orchestrator uses to pick which sections to paste. A versionless entry (pnpm `catalog:` /
`workspace:*` spec) still gets its checklist; resolve the real version from
`pnpm-workspace.yaml`'s catalog when present, otherwise the reviewer leans on context7 for
version-sensitive items.

Pass the result into the envelope's **Stack manifest** slot, and paste the matching
`library-practices.md` sections (detected libs only) into the **quality** dispatch. A lib absent
from the manifest gets no checklist — its idioms must not be checked.

Pass the capability flags (§Capability detection above) into the dispatch envelope's **Project capabilities** slot. Reviewers read it and skip off-capability checks. When detection is ambiguous, default the flag **off** and note it — a missed i18n flag is recoverable; a wave of false "hardcoded text" findings on a non-i18n repo destroys trust in the report.

## Banned-pattern grep (ripgrep over changed files)

Run each over the changed-file set. Keep only hits on **added/modified** lines — cross-check against the patch; a hit on an unchanged context line is pre-existing, skip it. Record `file:line:matched-pattern` for the seed list.

```bash
FILES=$(cat /tmp/argus_files.txt)

# Type casts (exclude import-alias `import { x as y }` and JSX) — most-cited ban
rg -n --no-heading -e '\)\s+as\s+\w' -e '\]\s+as\s+\w' -e '\b\w+\s+as\s+(const\b|unknown\b|any\b|[A-Z]\w*)' $FILES \
  | rg -v '^\s*import|from\s+["'\'']'

# lint-disable used to silence a cast / any — RED FLAG, the project ban still applies
rg -n --no-heading -e '(oxlint|eslint|biome)-disable.*(no-unsafe-type-assertion|no-explicit-any|consistent-type-assertions)' $FILES

# Native browser dialogs
rg -n --no-heading -e '\b(window\.)?(confirm|alert|prompt)\s*\(' $FILES

# dangerouslySetInnerHTML (verify sanitization in the security reviewer)
rg -n --no-heading -e 'dangerouslySetInnerHTML' $FILES

# Hardcoded locale in Intl / toLocale*  — ONLY IF i18n=on (single-locale app: a hardcoded locale is fine)
[ "$i18n" = on ] && rg -n --no-heading -e '["'\''](fr|es|pt|en)-[A-Z]{2}["'\'']' -e 'toLocale(String|DateString|TimeString|LowerCase|UpperCase)?\s*\(' $FILES

# className built without cn()  →  [...].join(' ') or template ternary
# Exclude shadcn components/ui/** — style/import/naming there is a hard no-emit (see dimensions.md conventions)
STYLE_FILES=$(echo "$FILES" | tr ' ' '\n' | rg -v '/components/ui/' | tr '\n' ' ')
rg -n --no-heading -e 'className=\{[^}]*\.join\(' -e 'className=\{`[^`]*\$\{[^}]*\?[^}]*\}' $STYLE_FILES

# Leftover debug
rg -n --no-heading -e 'console\.(log|debug)\s*\(' $FILES

# Deprecated Zod email
rg -n --no-heading -e 'z\.string\(\)\.email\(' $FILES

# useEffect (require justification comment)
rg -n --no-heading -e '\buseEffect\s*\(' $FILES

# Manual date parsing instead of the mandated date lib
rg -n --no-heading -e 'new Date\([^)]*\.split\(' $FILES

# Tracked-task comments missing the (ali) owner prefix
rg -n --no-heading -e '\b(TODO|FIXME|NOTE)\b' $FILES | rg -v 'TODO\(ali\)|FIXME\(ali\)|NOTE\(ali\)'
```

Adapt patterns to the repo's actual rules (read `CLAUDE.md`/`AGENTS.md`/`docs` first). If the repo bans different things, grep those instead — the pass is a template, not a fixed law.

## i18n hardcoded-text candidates (heuristic) — ONLY IF `i18n=on`

**Skip this entire section when `i18n=off`.** On a project with no translation system, hardcoded user-facing strings are not a violation — running it produces only noise.

Literal user-facing strings are harder to grep without false positives. A cheap heuristic over changed frontend files (`apps/web`, `apps/backoffice`, shared UI):

```bash
# JSX text nodes and string props that look like prose (2+ words, letters/accents) and are NOT m.* calls
rg -n --no-heading -e '>[^<>{}]*[A-Za-zÀ-ÿ]{2,}[^<>{}]*<' -e '(title|label|placeholder|aria-label)=["'\''][^"'\'']*[A-Za-zÀ-ÿ ]{4,}' \
   $(echo "$FILES" | rg 'apps/(web|backoffice)|shared-ui') \
  | rg -v 'm\.[a-zA-Z]'
```

Treat these as **low-confidence** candidates — the conventions reviewer must confirm each is genuinely user-facing copy (not a key, className, or test id) before flagging.

## Seed list format → conventions reviewer

Pass the verified-candidate hits into the conventions dispatch prompt under the envelope's "Mechanical pre-pass candidates" slot:

```
Mechanical pre-pass candidates to verify first, then extend:
- apps/web/src/features/article/article-details-formatters.ts:42 — `as` cast (no-unsafe-type-assertion disabled at L40 — red flag)
- apps/web/src/features/basket/basket-recap.tsx:26 — hardcoded 'fr-FR' in Intl.NumberFormat
- apps/web/src/features/basket/payment-selector.tsx:18 — className via [...].join(' ') instead of cn()
- ...
```

The conventions reviewer treats these as a starting set: confirm each (drop pre-existing/false-positive), assign severity per the project rule source, and add anything the grep missed (naming, magic numbers, import order, i18n parity).

## Why seed instead of letting the agent re-grep

- **Determinism:** the same diff yields the same seed list every run — no model-to-model variance on the highest-frequency category.
- **Efficiency:** the agent spends tokens verifying + extending, not rediscovering. No wasted re-greping the parent already did.
- **Recall:** a banned `as` buried in line 380 of a 500-line file is found by grep regardless of attention budget.
