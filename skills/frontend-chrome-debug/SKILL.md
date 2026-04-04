---
name: frontend-chrome-debug
description: Debug the frontend in a real browser using MCP Chrome DevTools. Use when investigating UI bugs, network errors, or console errors. Discovers test credentials and frontend URL from the project automatically.
---

# Frontend Chrome Debug

## Overview

Use the MCP Chrome DevTools tools (`mcp__chrome-devtools__*`) to open a real browser, log in with a seeded test user, and inspect the frontend.

## Prerequisites — Discover Project Context

Before interacting with the browser, gather project-specific details by scanning the codebase. Do NOT hardcode or assume values — always look them up.

### 1. Frontend URL

Find the dev server URL by checking (in order):
- `vite.config.*` → look for `server.port`
- `.env*` files → look for `PORT`, `VITE_PORT`, `NEXT_PUBLIC_URL`, or similar
- `package.json` scripts → look for `--port` flags or `dev` script
- `next.config.*` → look for port config
- Default: `http://localhost:3000` if nothing is found

### 2. Test Credentials

Find seeded/test users by searching for:
- Seeder files: glob `**/seed*/**/*.{ts,js}`, `**/fixtures/**/*.{ts,js}`
- Factory files: glob `**/factor*/**/*.{ts,js}`
- Look for `password`, `email`, `username` assignments in those files
- Read the seeder to extract at least one usable login (username/email + password)
- If multiple roles exist (admin, basic user…), note them for permission testing

### 3. Login Page Shape

Navigate to the frontend URL and `take_screenshot` to see the actual login form. Identify:
- Field labels (email? username? phone? license number?)
- Submit button text
- Any extra steps (2FA, entity selection, workspace picker…)

### 4. Auth Bypass (optional)

Check `.env*` files for 2FA/OTP disable flags (e.g. `DISABLE_2FA`, `VITE_DISABLE_2FA_FEATURE`, `SKIP_OTP`). If present and set, note that 2FA is bypassed locally.

## Login Flow

Once prerequisites are gathered, log in:

1. `navigate_page` → frontend URL
2. `take_screenshot` → confirm login page is loaded
3. `fill` → each credential field (use labels or selectors from the screenshot)
4. `click` → submit button
5. `take_screenshot` → confirm post-login state
6. If extra steps (entity/workspace selection, 2FA…), handle them based on what the screenshot shows
7. Confirm the app reaches an authenticated layout

Use `mcp__chrome-devtools__fill` for text fields and `mcp__chrome-devtools__click` for buttons.

## Debugging Workflow

### 1. Open a page

```
mcp__chrome-devtools__navigate_page  →  url discovered from prerequisites
mcp__chrome-devtools__take_screenshot  →  verify current state visually
```

### 2. Interact

```
mcp__chrome-devtools__fill        →  fill an input by selector or label
mcp__chrome-devtools__click       →  click a button/link
mcp__chrome-devtools__hover       →  hover to trigger tooltips/dropdowns
mcp__chrome-devtools__press_key   →  send keyboard events (Enter, Tab, Escape…)
mcp__chrome-devtools__type_text   →  type freely in focused element
```

### 3. Inspect visual output

```
mcp__chrome-devtools__take_screenshot   →  full-page or viewport screenshot
mcp__chrome-devtools__take_snapshot     →  DOM snapshot for structural analysis
```

### 4. Inspect errors and network

```
mcp__chrome-devtools__list_console_messages   →  all console output (errors, warnings, logs)
mcp__chrome-devtools__get_console_message     →  single message detail
mcp__chrome-devtools__list_network_requests   →  all XHR/fetch requests
mcp__chrome-devtools__get_network_request     →  single request detail (headers, body, response)
```

### 5. Run JavaScript

```
mcp__chrome-devtools__evaluate_script  →  run arbitrary JS in page context
```

Useful snippets:

- `window.__REACT_DEVTOOLS_GLOBAL_HOOK__` — check React mount
- `document.querySelector('[data-testid="..."]')` — find elements
- `localStorage` / `sessionStorage` — inspect stored state

### 6. Wait for async changes

```
mcp__chrome-devtools__wait_for  →  wait for selector, network idle, or navigation
```

## When to use proactively

- **After any table column/row-action change** — always take a screenshot to validate alignment (buttons, icons, arrows) before handing back. Layout shifts between rows are easy to miss without visual verification.
- **After adding or repositioning UI elements** in a list/table (icons, action cells, drag handles…) — confirm nothing shifted or disappeared.

## Common Debug Scenarios

### API call returning error

1. Log in and reproduce the action
2. `list_network_requests` → find the failing request
3. `get_network_request` → inspect request payload and response body
4. Cross-check with backend logs or API contract definitions in the codebase

### Component not rendering / blank page

1. `take_screenshot` to confirm visual state
2. `list_console_messages` → look for React errors or unhandled promise rejections
3. `evaluate_script` with `document.body.innerHTML` to inspect raw DOM
4. `take_snapshot` for full DOM tree

### Form validation not working

1. `fill` fields with edge-case values
2. `click` submit
3. `take_screenshot` to capture validation messages
4. `list_console_messages` to check for thrown validation errors

### Permissions issue (feature hidden or 403)

- Use the **admin** seeded user for full access
- Use a **restricted** seeded user to test limited permissions
- Read the seeder/rights files to understand role assignments
- Switch between users to compare behavior

## Troubleshooting

- **MCP tools not available** — Verify the Chrome DevTools MCP server is running (`list_pages` should return results). If not, ask the user to start it.
- **`navigate_page` fails or blank page** — Confirm the dev server is running: `curl -s -o /dev/null -w "%{http_code}" <frontend_url>` should return 200.
- **Tools timing out** — Use `wait_for` with a selector before interacting. Heavy pages may need extra time after navigation.
- **Cannot find element** — Use `take_snapshot` to get the DOM tree, then refine selectors. Prefer `data-testid` attributes over CSS classes.

## Tips

- Always call `take_screenshot` after each interaction to confirm the UI state before continuing.
- Use `list_pages` to see all open tabs and `select_page` to switch between them.
- If the page is stuck loading, `list_network_requests` first — a failed preflight or 401 is often the root cause.
- React Query errors surface in the console as `[Query]` entries; filter by `error` in `list_console_messages`.
- The `evaluate_script` tool can read TanStack Query cache: `window.__REACT_QUERY_DEVTOOLS_CLIENT__` if devtools are mounted.

## Gotchas
