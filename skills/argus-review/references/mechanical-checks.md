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
**/graphify-out/**
```

Do **not** strip (review normally, but conventions reviewer skips their import-order/naming):
- `**/components/ui/**` (shadcn autogen — may be hand-edited; keep for security/regression)
- `**/migrations/**` (hand-written SQL is reviewable; pure generated DDL is noise)
- locale message files `**/messages/*.json` (needed for i18n parity check)

## Build the changed-file set

```bash
BASE=<base>; BRANCH=<branch>          # or use --cached for staged
git diff --name-only "$BASE...$BRANCH" \
  | grep -vE '\.(lock|snap)$|snapshot\.json$|\.gen\.ts$|/paraglide/|/generated/|/dist/|/\.turbo/|/graphify-out/' \
  > "$ARGUS_TMP/files.txt"   # $ARGUS_TMP = the run's mktemp -d dir from SKILL.md step 2
```

## Capability detection (run once, gate the folded checks)

Folded sub-checks must only fire when the project has the capability. Resolve these flags deterministically in the parent and pass them into every dispatch. **Off → the reviewer skips that sub-check.** Detect from the repo root, not just the diff (a project either has i18n or it does not).

**Cache first — capabilities are a property of the repo, not of the PR.** Re-detecting on every run costs minutes for an answer that only changes when the package manifests change. The cache lives in the common git dir (shared across worktrees, never committed), keyed by a hash of the manifests:

```bash
ROOT=$(git rev-parse --show-toplevel)
CACHE="$(git rev-parse --git-common-dir)/argus-capabilities"
KEY=$(cat "$ROOT"/package.json "$ROOT"/apps/*/package.json "$ROOT"/packages/*/package.json 2>/dev/null | shasum | cut -d' ' -f1)
if [ -f "$CACHE" ] && [ "$(head -1 "$CACHE")" = "$KEY" ]; then tail -n +2 "$CACHE"; fi
```

On a hit (the flags + LIBS lines print), **skip both detection blocks below entirely**. On a miss, run them, then write the cache:

```bash
{ echo "$KEY"; echo "i18n=$i18n frontend=$frontend react=$react payments=$payments monorepo=$monorepo"; echo "LIBS=$LIBS"; } > "$CACHE"
```

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
FILES=$(cat "$ARGUS_TMP/files.txt")

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

## ORM migration hygiene — ONLY IF `drizzle` or `prisma` in the stack manifest

Hand-written migrations bypass the ORM's generator and desync its snapshot/journal state (real
incident: sofrapa #155/#166/#176/#190 shipped SQL-only Drizzle migrations without snapshots →
history no longer replayable from an empty DB, repaired in #196/#198).

**Run this on the RAW `git diff --name-status` output, never on `files.txt` or the stripped
patch** — the ignore list above strips `**/snapshot.json`, so a missing/present snapshot is
invisible to reviewers; only this pre-pass can see it.

```bash
git diff --name-status "$BASE...$BRANCH" > "$ARGUS_TMP/name-status.txt"

# --- Drizzle (skip unless drizzle in LIBS) ---
# 1. Migration added without its generated sibling snapshot (hand-written migration)
#    Layouts vary: per-dir snapshot.json (this repo) OR a meta/_journal.json entry — accept either.
for sql in $(rg '^A\s' "$ARGUS_TMP/name-status.txt" | rg -o '\S*migrations/.*/migration\.sql$'); do
  dir=$(dirname "$sql")
  rg -q "^A\s+$dir/snapshot\.json" "$ARGUS_TMP/name-status.txt" \
    || rg -q 'migrations/meta/_journal\.json' "$ARGUS_TMP/name-status.txt" \
    || echo "$sql — added without generated snapshot/journal → hand-written migration candidate (warning)"
done

# 2. Already-committed migration MODIFIED (not added) — may be applied elsewhere (critical candidate)
rg '^M\s+\S*migrations/.*\.(sql|json)$' "$ARGUS_TMP/name-status.txt"

# 3. Drizzle schema changed but no migration in the diff — missing generation candidate
#    Low-confidence: type-only / relations-only edits legitimately need no migration.
if rg -q '^[AM]\s+\S*(schema|schemas)/.*\.ts$' "$ARGUS_TMP/name-status.txt" \
   && ! rg -q 'migrations/' "$ARGUS_TMP/name-status.txt"; then
  echo "schema changed with no migration in diff — verify a migration was generated (low-confidence)"
fi

# --- Prisma (skip unless prisma in LIBS) ---
# schema.prisma and prisma/migrations/<ts>_*/migration.sql must land together; one without the
# other is drift. A MODIFIED migration.sql is the critical case, same as Drizzle #2.
rg '^M\s+\S*prisma/migrations/.*migration\.sql$' "$ARGUS_TMP/name-status.txt"
if rg -q '^M\s+\S*schema\.prisma$' "$ARGUS_TMP/name-status.txt" \
   && ! rg -q '^A\s+\S*prisma/migrations/' "$ARGUS_TMP/name-status.txt"; then
  echo "schema.prisma changed with no new migration — verify prisma migrate dev was run (low-confidence)"
fi
```

Corroboration heuristic (never a finding on its own): drizzle-kit names migration dirs with a
random codename (`20260701102242_unique_lila_cheney`); a descriptive slug on a round timestamp
(`20260701120000_add_order_item_status_history`) suggests hand-authoring — mention it as
supporting evidence when signal 1 fires.

Seed the hits to the **conventions** reviewer like the banned-pattern hits; the **quality**
reviewer owns the judgment side via `library-practices.md` §drizzle/prisma → Migration hygiene.
Severity: hand-written/missing-snapshot → `warning`; modified already-merged migration →
`critical` candidate (it may already be applied to shared databases); the two low-confidence
checks are questions for the reviewer to resolve, `nit` at most if unresolved.

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

## File-size count → quality reviewer

Line counts are deterministic — compute them in the parent so the oversized-file check (dimensions.md §quality item 9) never depends on a reviewer noticing:

```bash
# Total post-diff size of every changed file (skip deleted files); keep those ≥ ~400 lines
wc -l $FILES 2>/dev/null | sort -rn
# Diff-added lines per file, to tell "keeps growing" from "barely touched"
git diff --numstat <base>...<branch> # (or --cached --numstat)
```

Pass the survivors into the **quality** dispatch under the envelope's "File-size seed" slot:

```
File-size seed (total lines post-diff, pre-computed by the parent — apply §quality item 9):
- apps/api/src/services/order.service.ts — 1240 lines total (diff adds 85)
- apps/web/src/features/basket/basket-recap.tsx — 430 lines total (diff adds 120)
```

No file ≥400 lines → pass `none` (the reviewer then emits no oversized-file finding). The reviewer owns the judgment call (split axis, cohesion, severity); the parent only owns the counting. Test files (`*.spec.*`, `*.test.*`, `__tests__/`, `e2e/`) still appear in the seed for the ≥400 diff-grown tier, but the reviewer never flags them under the ≥~1000-lines tier (dimensions.md §quality item 9 exemption).

## New-symbol seed → quality reviewer (reuse detection)

Reuse misses are the largest measured recall gap (July 2026 retro: ~30 verified missed-reuse cases vs ~6 detected across 20 PRs — detection only fired on near-verbatim copies; structural duplicates of `useSeedOnDialogOpen`, `claimDue`, `assertSameSet`, `LoadingState`, `useAppForm` all shipped unflagged). The reviewer prose rule ("grep the wider repo") does not fire reliably — make it deterministic like the file-size seed:

```bash
# 1. Extract newly ADDED top-level symbols from the patch (functions, hooks, components, classes, exported consts/types)
rg -o '^\+\s*(export\s+)?(default\s+)?(async\s+)?(function|class|interface|type|const)\s+([A-Za-z_$][\w$]*)' \
   -r '$5' "$ARGUS_TMP/diff.patch" | sort -u > "$ARGUS_TMP/new-symbols.txt"

# 2. For each new symbol, grep the tree OUTSIDE the diff for same/similar names (strip use/get/format/is prefixes for the fuzzy pass)
while read -r sym; do
  stem=$(echo "$sym" | sed -E 's/^(use|get|format|is|assert|build|create|resolve)//' )
  hits=$(rg -l --max-count 3 -e "\b$sym\b" ${stem:+-e "$stem"} "$ROOT/apps" "$ROOT/packages" 2>/dev/null \
         | grep -vFf "$ARGUS_TMP/files.txt" | head -3)
  [ -n "$hits" ] && echo "$sym → possible existing equivalent(s): $hits"
done < "$ARGUS_TMP/new-symbols.txt"

# 3. Canonical homes: for every new file under a feature dir, list the repo's shared dirs so the reviewer checks them
#    (hooks/, components/ui/, components/shared/, lib/, utils/, packages/*/src) — one `ls` per dir, names only.
```

Pass survivors into the **quality** dispatch under the envelope's "New-symbol seed" slot:

```
New-symbol seed (added symbols with a possible pre-existing equivalent — apply §quality item 1/4; verify each, never assume):
- normalizeSearch → packages/utils/src/normalize-search-text.ts (normalizeSearchText)
- useMediaQuery → apps/web/src/hooks/shadcn/use-mobile.ts (useIsMobile)
- none
```

Name-match is a weak signal both ways: the seed catches same-name/similar-name cases; the reviewer still owns same-shape-different-name detection (grep the canonical shared dirs for every new hook/component/util the diff adds, per §quality item 1). An empty seed does NOT mean no reuse misses.

## Removed-line seed → regression reviewer

Reviewers systematically read added lines and miss removed invariants (July 2026 retro: removed `onFileReject` prop silently changed form semantics; a removed legacy `status: VALID` fallback flipped a whole licensee population; an upsert/stale-delete pair lost its `withTransaction`; a removed 422 guard exposed an unbounded fan-out). Extract the load-bearing `-` lines mechanically:

```bash
# Removed lines that carry behavior: props/params dropped, guards, transactions, early returns, error handling, exports
rg -n '^-' "$ARGUS_TMP/diff.patch" | rg -v '^\-\-\-' \
  | rg -e 'withTransaction|\$transaction|FOR UPDATE|throw |return null|return;|catch|disabled=|\?\.|onError|on[A-Z]\w+=\{|export |fallback|Omit<' \
  > "$ARGUS_TMP/removed-behavior.txt"
```

Pass hits (with their file context from the hunk headers) into the **regression** dispatch under the "Removed-behavior seed" slot. For each, the regression reviewer answers: *who depended on this behavior, and is that dependency handled?* — same consumer-grep discipline as renamed symbols. A removed guard/transaction/fallback with a surviving consumer is a finding even when every added line is correct.

## Why seed instead of letting the agent re-grep

- **Determinism:** the same diff yields the same seed list every run — no model-to-model variance on the highest-frequency category.
- **Efficiency:** the agent spends tokens verifying + extending, not rediscovering. No wasted re-greping the parent already did.
- **Recall:** a banned `as` buried in line 380 of a 500-line file is found by grep regardless of attention budget.
