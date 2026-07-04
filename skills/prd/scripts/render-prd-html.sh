#!/usr/bin/env bash
# Render <name>.prd.md into a self-contained <name>.prd.html (same directory).
# Usage: render-prd-html.sh path/to/feature.prd.md [output.html]
set -euo pipefail

MD="${1:?usage: render-prd-html.sh <file.prd.md> [output.html]}"
OUT="${2:-${MD%.md}.html}"
TITLE=$(grep -m1 '^# ' "$MD" | sed 's/^# //' || basename "$MD")

if command -v bunx >/dev/null 2>&1; then
  BODY=$(bunx marked --gfm -i "$MD")
elif command -v npx >/dev/null 2>&1; then
  BODY=$(npx -y marked --gfm -i "$MD")
else
  echo "error: need bunx or npx to run 'marked'" >&2
  exit 1
fi

BODY="$BODY" TITLE="$TITLE" python3 - "$OUT" <<'PY'
import html, os, re, sys

body = os.environ["BODY"]
title = os.environ["TITLE"]
out = sys.argv[1]

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

toc = []
def add_id(m):
    text = re.sub(r"<[^>]+>", "", m.group(1))
    slug = slugify(text)
    toc.append((slug, text))
    return f'<h2 id="{slug}">{m.group(1)}</h2>'

body = re.sub(r"<h2>(.*?)</h2>", add_id, body)
toc_html = "".join(f'<li><a href="#{s}">{html.escape(t)}</a></li>' for s, t in toc)

# highlight the pre-draft findings section as a callout
body = body.replace("<h2 id=\"pre-draft-findings\">", "<h2 class=\"callout-head\" id=\"pre-draft-findings\">")

page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{ --bg:#fafafa; --fg:#1a1a1a; --muted:#666; --border:#e2e2e2; --accent:#2563eb; --code:#f0f0f0; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#111214; --fg:#e6e6e6; --muted:#9a9a9a; --border:#2e3136; --accent:#60a5fa; --code:#26282d; }}
  }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
         font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  main {{ max-width:60rem; margin:0 auto; padding:2rem 1.25rem 4rem; }}
  h1 {{ font-size:1.7rem; margin-bottom:.25rem; }}
  h2 {{ border-bottom:2px solid var(--border); padding-bottom:.3rem; margin-top:2.2rem; }}
  code {{ background:var(--code); border-radius:4px; padding:.1em .35em;
          font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:.88em; }}
  pre {{ background:var(--code); border-radius:8px; padding:.9rem 1.1rem; overflow-x:auto; }}
  pre code {{ background:none; padding:0; }}
  table {{ border-collapse:collapse; width:100%; }}
  th,td {{ text-align:left; padding:.45rem .7rem; border-bottom:1px solid var(--border); }}
  nav.toc {{ background:var(--code); border-radius:8px; padding:.7rem 1.1rem; margin:1.2rem 0; }}
  nav.toc ul {{ margin:.3rem 0; padding-left:1.2rem; }}
  .callout-head, .callout-head + * {{ border-left:4px solid var(--accent); padding-left:.8rem; }}
  .date {{ color:var(--muted); margin-bottom:1rem; }}
  input[type=checkbox] {{ margin-right:.4rem; }}
  li.task-list-item {{ list-style:none; margin-left:-1.2rem; }}
</style>
</head>
<body>
<main>
<nav class="toc"><strong>Sommaire</strong><ul>{toc_html}</ul></nav>
{body}
</main>
</body>
</html>
"""

with open(out, "w") as f:
    f.write(page)
print(out)
PY
