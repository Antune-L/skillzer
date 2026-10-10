# Repository exploration and decision gates

Read this reference whenever the analysis depends on repository files or behavior. Exploration
establishes what exists and who owns it before analysts recommend a change. Keep code and external
systems read-only; write findings only to the Athena scratch directory.

## Discovery scope

1. Give the artifacts explorer the whole product root for filename/extension inventory, regardless
   of the ticket's suggested module. Establish nested repositories, read their instructions, and
   record revisions/local changes. Bound subsequent content inspection by discovered relevance;
   other explorers can start in suspected areas and expand along references.
2. Turn the request into search families: exact names/extensions; business vocabulary and acronyms;
   provider/protocol terms; payload fields; current and legacy identifiers discovered in code.
   Follow new terms and references when they reveal another likely owner. Do not assume a provider
   name appears in filenames or that one module owns both composition and delivery.
3. Start with a file inventory using `rg --files --hidden --no-ignore`, explicitly excluding VCS
   internals, dependencies, and unrelated build output; then search contents across relevant roots.
   For requested JSON files, inventory the extension without first filtering for provider names.
   Examine likely matches in source, tests, fixtures, resources, schemas, configuration, examples,
   migrations, and documentation when present. Return literal paths and inspect their meaning.
4. Use filename-only or count output for all content discovery;
   never print matching lines that could contain secrets. Classify possible credentials by key
   names or safe structure only, without returning their values. Do not rely on secret-looking
   filenames to decide which files need this handling. For JSON, when `jq` is available,
   `jq 'if type == "object" then keys else type end' <file>` returns object key names or the root
   type, without values. Otherwise use an available parser with equivalent metadata-only output.
   Inspect verified non-sensitive content after classification. Inspect excluded areas only for a concrete
   lead; a skipped or unreadable file is a coverage gap, never evidence of absence.
5. Trace artifacts to their loaders, tests, transformation, or runtime consumers. Classify matches
   as fixtures, schemas, configuration, templates, generated output, or executable implementation.
   A fixture proves an example exists, not that the current product can execute that payload.
   For credential files, report presence and the loading path without extracting or displaying values;
   distinguish existence, use by current code, and validity/authorization, which may remain unknown.
6. Trace the relevant behavior through entry point, validation/mapping, contract, handler or
   consumer, persistence/provider boundary, and callers as applicable. Read actual data shapes and
   branches; interfaces, filenames, dead code, and mocks alone do not prove reachable behavior.
   Inspect documented launch modes when they affect the diagnosis: source execution, packaged
   builds, and container images can have different prerequisites. Do not generalize a failure in
   one mode to all modes. Run containers or provider operations only within authorized runtime
   validation; otherwise mark runtime untested. A documented
   command is not proof of successful startup: trace scripts, imports, and installation requirements,
   and leave unavailable dependencies or image availability explicitly unverified.

Stop expanding a branch when its relevance is disproved with evidence. Continue when a new root,
identifier, consumer, or inconsistent result could change the answer. Do not scan unrelated repos
or run application/provider operations merely to complete static exploration.

## Evidence returned by each explorer

Use the return contract in [`prompts.md`](prompts.md#explorer-prompt). The search ledger must account
for truncation, access errors, filters, and relevant uninspected candidates. Store factual results
in `$ATHENA_TMP/exploration-ledger.md`; the report needs only decisive findings and material coverage limits.
Recheck cited paths and identifiers in current files when writing it.

## Decision gates

### Before saying an artifact or implementation is absent

Require all three:

- Filename/extension inventory and content searches across all relevant discovered roots, using
  domain/provider synonyms and identifiers from nearby code.
- Inspection of relevant candidates and explicit accounting for hidden/ignored areas, skipped
  results, truncation, and inaccessible roots that could affect the conclusion.
- A fresh independent search trying to find a counterexample, not merely repeating the first
  search terms or reviewing its citations. The code-reality reviewer may perform this check.

If any condition is missing, say **"not found in <searched scope>"** or **"unverified"**, and name
the gap. Even a completed search supports absence only in the inspected revision and scope.

### Before saying a module must be changed

For every required change, identify:

- The unmet requirement and the observed current behavior or incompatible data contract.
- The owning entry point, transformation, contract, and relevant callers/consumers, with verified
  `file:line` evidence. State where the trace is incomplete.
- Existing mechanisms that could satisfy the requirement through configuration, a caller change,
  mapping, reuse, or an existing supported launch mode, and why they do or do not suffice.
- Whether the change is **required**, **conditional on an unresolved fact**, or **optional**.

A suggested module from the source is a hypothesis. A simpler existing path found by another
agent invalidates an unsupported change recommendation; inspect it before retaining the proposal.
Separate existing legacy behavior from the requested new behavior and payload shape.

### Before drafting the solution (step 3)

Resolve decisive disagreements, uninspected relevant hits, and uncertain ownership with a targeted
task using the explorer-role model from step 0. Give it the specific question and raw evidence,
not a conclusion to confirm. Gaps found in Wave 2 are addressed in the reserved re-review or reported.
For independent counter-searches, omit previous search results until the agent has searched.

Follow the budget in `SKILL.md`: follow-ups use spare calls before the reserved final re-review
call. Stop after two unsuccessful attempts on the same question or earlier when those calls run
out; retain the gap and available alternatives. A budget limit is not proof of completeness.
Static code evidence is not runtime or deployed validation.
