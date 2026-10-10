# Source intake — per type

Gather each source with the tools below, then summarize it into the dossier. When a tool is
unavailable (MCP not connected or not authenticated), record the source as **unreachable** in the
dossier and tell the user which connector to authorize; never guess its content.

## Notion page

1. `notion-fetch` with `id: <url>` and `include_discussions: true`. Check `truncated` and
   `unknown_block_ids`; fetch omitted subtrees if they look relevant.
2. `notion-get-comments` with `page_id`, `include_all_blocks: true`, `include_resolved: true`.
3. Keep only **relevant** comments: decisions, scope changes, client or PO feedback, technical
   constraints, unanswered questions, bug reproductions. Drop acknowledgements ("ok", "merci",
   emoji), scheduling chatter, and duplicates. For each kept comment record the author, the date,
   the anchored text (from the `discussion://` marker in the fetch output), resolved or not.
4. Linked content, one hop: page mentions, sub-pages, relation properties (parent epic, blocked
   by, related to), embedded files. Use `include_file_urls: true` or `notion-get-file-download-urls`
   for attachments such as mockups; download them into `$ATHENA_TMP/images/`.

## Notion database used as a kanban

When the page is a row of a database (the fetch shows a parent `collection://` data source):

1. `notion-fetch` the `collection://` URL to read the schema (status, relation, assignee, epic,
   tags columns) and its `<sqlite-table>` column names.
2. Query related cards with `notion-query-data-sources`:
   - cards linked through relation properties of the primary card,
   - cards sharing the same epic, parent, sprint, or tag,
   - cards whose title contains the key domain terms of the problem (`string_contains`).
   Use `mode: "rows"` with a structured filter when available; SQL mode is subject to plan limits.
3. For each related card, fetch it (and its comments only if it looks directly related). Record why
   it is related: duplicate, dependency, previous attempt, conflicting requirement, follow-up.

## Atelier kanban (kanban MCP)

1. `mcp__kanban__list_projects` to find the project, then `mcp__kanban__list_tickets` filtered by
   `project` (paginate with `offset`, check every column including `done`, `merged`, `failed`,
   `abandoned`: past attempts are valuable context).
2. Match related cards by title and domain terms. Record previous failed or abandoned attempts and
   why they failed when the card says so.
3. Do not call `start_ticket`, `update_ticket`, `create_todo_ticket`, or `analyze_tickets`: Athena is
   read-only and `analyze_tickets` launches background work on the board.

## Mockups, screenshots, images

- Read each image directly. Describe screens, states (empty, error, loading), copy text, and any
  annotation. Note what the mockup implies but the ticket does not say.
- Figma links: use the Figma MCP (load the `figma:figma-design-to-code` skill before
  `get_design_context`). If the Figma MCP needs authentication, ask the user for screenshots or
  to authorize the connector.

## Other sources

- **Slack** thread links: `slack_read_thread` (or `slack_read_channel` for channel links).
- **GitHub** issues or PRs: `gh issue view <n> --comments` and `gh pr view <n> --comments`.
- **PDF / docx**: read with the `Read` tool (`pages` for PDFs over 10 pages) or the matching skill.
- **Pasted text**: copy it verbatim into the dossier, it is a primary source.

## Code

- Resolve the product root before choosing the code area: current working directory if it matches,
  otherwise the location named in the sources, otherwise ask. A product directory may contain several
  nested repositories; record relevant service/package roots and their applicable instructions.
- Record each root's branch, short revision, and relevant working-tree changes so agents inspect the
  same state. Worktrees and generated files are separate evidence, not automatically the active code.
  Do not fetch or switch branches for analysis; disclose a missing root or version.
- If a `graphify-out/` graph exists, mention it in the dossier. Check its revision/coverage before
  relying on it; a missing graph result does not establish absence from current files.
- Before code conclusions, follow [`exploration.md`](exploration.md). Dossier sources and proposed
  module names guide search terms, not the boundaries of repository exploration.
