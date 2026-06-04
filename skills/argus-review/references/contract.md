# Reviewer output contract

Single source of truth for the JSON every reviewer returns. **Self-contained** — does not reference any other skill. The orchestrator pastes the §Compact schema into each dispatch prompt and validates replies against the §Full schema here.

Every reviewer returns **one JSON object and nothing else** — no prose, no surrounding fences. The object is mandatory even on failure; prose-only output is a failure.

## Compact schema (paste into dispatch prompts)

```
Return exactly this JSON shape (no prose, no fences):
{
  "agent": "<your-section>-reviewer",
  "version": "1.0.0",
  "scope": { "mode": "branch|staged|remote-branch", "base": "<base>", "branch": "<branch>", "files": ["<changed file reviewed>"] },
  "status": "ok|partial|error",
  "coverage": "complete|partial|not-run",
  "summary": { "critical": 0, "warning": 0, "nit": 0 },
  "findings": [
    {
      "id": "<section>.<category>.<slug>",
      "section": "<your-section>",
      "severity": "critical|warning|nit",
      "category": "<short category>",
      "title": "<short normalized title>",
      "file": "<repo-relative path>",
      "line": 0,
      "end_line": 0,
      "related_files": [],
      "evidence": "<one concrete sentence tied to file:line>",
      "confidence": "high|medium|low",
      "recommendation": "<one concrete next action>"
    }
  ],
  "notes": [],
  "errors": []
}
Rules: summary counts == findings split by severity, exactly. Omit line/end_line for file-level findings. Never use severity "nit" for the security section. No findings → status "ok", coverage "complete", zeros, empty arrays.
```

## Full schema (orchestrator validation reference)

### Top-level fields

| Field | Type | Required | Rule |
|---|---|---|---|
| `agent` | string | yes | e.g. `quality-reviewer` |
| `version` | string | yes | Semver, start `"1.0.0"`; bump on schema change |
| `scope.mode` | enum | yes | `branch` \| `staged` \| `remote-branch` |
| `scope.base` | string | yes | Base branch (empty allowed for `staged`) |
| `scope.branch` | string | yes | Reviewed branch (empty string for `staged`) |
| `scope.files` | string[] | yes | Changed files actually reviewed (subset on partial) |
| `status` | enum | yes | `ok` \| `partial` \| `error` |
| `coverage` | enum | yes | `complete` \| `partial` \| `not-run` |
| `summary` | object | yes | `{critical, warning, nit}` — must match `findings` |
| `findings` | array | yes | May be empty |
| `notes` | string[] | yes | Short context; may be empty |
| `errors` | string[] | yes | Non-empty iff `status` is `partial`/`error` |

### Finding fields

| Field | Type | Required | Rule |
|---|---|---|---|
| `id` | string | yes | Stable, unique. `<section>.<category>.<slug>` |
| `section` | enum | yes | `quality` \| `architecture` \| `regression` \| `security` \| `conventions` |
| `severity` | enum | yes | `critical` \| `warning` \| `nit` |
| `category` | string | yes | Agent-defined (e.g. `duplication`, `i18n`, `injection`, `signature-change`) |
| `title` | string | yes | Short normalized title (used for dedupe) |
| `file` | string | yes | Repo-relative path |
| `line` | integer | no | Start line — omit for file-level findings |
| `end_line` | integer | no | End line — omit if `line` omitted |
| `related_files` | string[] | yes | Other cited files; empty for single-file |
| `evidence` | string | yes | One concrete sentence tied to `file:line` |
| `confidence` | enum | yes | `high` \| `medium` \| `low` |
| `recommendation` | string | yes | One concrete next action |

## Output rules

- Always emit the JSON, even on failure.
- Never omit required fields — use empty string / empty array.
- `summary` counts equal the findings array split by severity, exactly.
- No findings → `status: "ok"`, `coverage: "complete"`, zeros, empty arrays.
- Partial review → `status: "partial"` + `coverage: "partial"` + `errors[]` explaining why.
- Hard failure → `status: "error"` + `coverage: "not-run"` + `errors[]` with cause.
- Security section never uses `severity: "nit"`.

## Token budget

Hard cap **3000 tokens** (JSON only). If exceeded: keep every `critical`/`warning` verbatim, collapse `nit` findings into a single `notes[]` entry, set `status: "partial"` and note the collapse in `errors[]`.

## Orchestrator validation steps

1. Parse the reply as JSON. If wrapped in fences/prose, strip the outer wrapper before parsing; if unparseable → reviewer failure.
2. Verify all top-level fields present + enum values valid.
3. Recount `findings` by severity, compare to `summary`. Mismatch → reviewer failure.
4. Verify `section` on every finding equals the reviewer's assigned section.
5. Verify `version` major matches this contract's major (`1`). Incompatible → surface as failure.

On any validation failure: coerce `status` to `error`, populate `errors[]` with the reason, record under "Subagent failures" in the report.
