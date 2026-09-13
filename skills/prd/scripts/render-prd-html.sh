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

body = body.replace("<h2 id=\"pre-draft-findings\">", "<h2 class=\"callout-head\" id=\"pre-draft-findings\">")

TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  /* NOTE: forced light theme — a PRD is a reading/print document; the auto dark
     variant produced an unreadable near-black page for dark-mode users. */
  :root {
    --bg:#f6f7fb; --surface:#ffffff; --fg:#1f2430; --muted:#5b6270;
    --border:#e4e7ee; --accent:#4f46e5; --accent-soft:#eef2ff; --accent-border:#c7d2fe;
    --code:#f1f3f8;
  }
  * { box-sizing:border-box; }
  html { color-scheme: light; scroll-behavior:smooth; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  body::before { content:""; display:block; height:6px;
         background:linear-gradient(90deg,#4f46e5,#7c3aed,#db2777); }
  .layout { display:grid; grid-template-columns:15rem minmax(0,1fr); gap:2.5rem;
         max-width:80rem; margin:0 auto; padding:2.2rem 1.5rem 5rem; }
  aside.side { position:sticky; top:1.2rem; align-self:start;
         max-height:calc(100vh - 2.4rem); overflow-y:auto;
         display:flex; flex-direction:column; gap:.8rem; }
  main { min-width:0; }
  h1 { font-size:2rem; line-height:1.25; letter-spacing:-.02em; margin:.5rem 0 .5rem; }
  h2 { font-size:1.3rem; letter-spacing:-.01em; margin-top:3rem; padding-bottom:.4rem;
        border-bottom:1px solid var(--border); scroll-margin-top:1.2rem; }
  h2::before { content:""; display:inline-block; width:.55rem; height:.55rem; border-radius:2px;
        background:var(--accent); margin-right:.55rem; vertical-align:.08em; }
  h3 { margin-top:1.8rem; }
  a { color:var(--accent); }
  code { background:var(--code); border:1px solid var(--border); border-radius:5px;
          padding:.08em .35em; font-family:ui-monospace,"SF Mono",Menlo,monospace; font-size:.86em; }
  pre { background:#232733; color:#e8eaf2; border-radius:10px; padding:1rem 1.2rem;
         overflow-x:auto; box-shadow:0 2px 8px rgba(31,36,48,.12); }
  pre code { background:none; border:none; color:inherit; padding:0; }
  blockquote { margin:1.4rem 0; padding:1rem 1.3rem; background:var(--accent-soft);
         border:1px solid var(--accent-border); border-left:4px solid var(--accent);
         border-radius:10px; }
  blockquote p { margin:.4rem 0; }
  table { border-collapse:separate; border-spacing:0; width:100%; margin:1.2rem 0;
         background:var(--surface); border:1px solid var(--border); border-radius:10px;
         overflow:hidden; box-shadow:0 1px 3px rgba(31,36,48,.06); }
  th { background:var(--accent-soft); color:#3730a3; text-align:left;
        font-size:.82rem; text-transform:uppercase; letter-spacing:.04em;
        padding:.6rem .8rem; border-bottom:1px solid var(--accent-border); }
  td { text-align:left; padding:.55rem .8rem; border-bottom:1px solid var(--border);
        vertical-align:top; }
  tr:last-child td { border-bottom:none; }
  tbody tr:nth-child(even) { background:#fafbfe; }
  nav.toc { background:var(--surface); border:1px solid var(--border); border-radius:12px;
         padding:.9rem 1.1rem; box-shadow:0 1px 3px rgba(31,36,48,.06); }
  nav.toc strong { display:block; font-size:.78rem; text-transform:uppercase;
         letter-spacing:.06em; color:var(--muted); margin-bottom:.45rem; }
  nav.toc ul { margin:0; padding:0; list-style:none; }
  nav.toc li { padding:.14rem 0; }
  nav.toc a { display:block; text-decoration:none; color:var(--fg); font-size:.88rem;
         border-left:2px solid transparent; padding-left:.55rem; margin-left:-.55rem; }
  nav.toc a:hover { color:var(--accent); }
  nav.toc a.active { color:var(--accent); font-weight:600; border-left-color:var(--accent); }
  button.density { border:1px solid var(--border); background:var(--surface); color:var(--muted);
         font:600 .78rem/1 inherit; font-family:inherit; letter-spacing:.04em;
         border-radius:99px; padding:.5rem .9rem; cursor:pointer; align-self:flex-start; }
  button.density:hover { color:var(--accent); border-color:var(--accent-border); }
  .callout-head, .callout-head + * { border-left:4px solid var(--accent); padding-left:.8rem; }
  .date { color:var(--muted); margin-bottom:1rem; }
  input[type=checkbox] { width:1rem; height:1rem; margin-right:.5rem; accent-color:var(--accent); }
  li.task-list-item { list-style:none; margin-left:-1.2rem; }
  li:has(> input[type=checkbox]) { list-style:none; margin-left:-1.2rem; padding:.15rem 0; }
  hr { border:none; border-top:1px solid var(--border); margin:2.5rem 0; }

  body.compact main { font-size:14px; line-height:1.45; }
  body.compact h1 { font-size:1.55rem; }
  body.compact h2 { font-size:1.1rem; margin-top:1.7rem; padding-bottom:.25rem; }
  body.compact h3 { margin-top:1.1rem; }
  body.compact main p, body.compact main ul, body.compact main ol { margin:.5rem 0; }
  body.compact main li { margin:.1rem 0; }
  body.compact th { padding:.35rem .6rem; font-size:.72rem; }
  body.compact td { padding:.3rem .6rem; }
  body.compact pre { padding:.6rem .8rem; }
  body.compact blockquote { padding:.6rem .9rem; margin:.9rem 0; }
  body.compact table { margin:.8rem 0; }

  @media (max-width:900px) {
    .layout { grid-template-columns:1fr; gap:1.2rem; }
    aside.side { position:static; max-height:none; }
    h1 { font-size:1.6rem; }
  }
  @media print {
    body::before, aside.side { display:none; }
    .layout { display:block; padding-top:0; }
  }
</style>
</head>
<body>
<div class="layout">
<aside class="side">
<nav class="toc"><strong>Sommaire</strong><ul>__TOC__</ul></nav>
<button class="density" id="density-toggle" type="button">Mode compact</button>
</aside>
<main>
__BODY__
</main>
</div>
<script>
(function () {
  var KEY = "prd-density";
  var btn = document.getElementById("density-toggle");
  function apply(compact) {
    document.body.classList.toggle("compact", compact);
    btn.textContent = compact ? "Mode confort" : "Mode compact";
  }
  apply(localStorage.getItem(KEY) === "compact");
  btn.addEventListener("click", function () {
    var compact = !document.body.classList.contains("compact");
    localStorage.setItem(KEY, compact ? "compact" : "comfort");
    apply(compact);
  });

  var links = {};
  document.querySelectorAll("nav.toc a").forEach(function (a) {
    links[decodeURIComponent(a.getAttribute("href")).slice(1)] = a;
  });
  var headings = Array.prototype.slice.call(document.querySelectorAll("h2[id]"));
  var current = null;
  function updateActive() {
    if (!headings.length) return;
    var line = window.innerHeight * 0.35;
    var chosen = headings[0];
    headings.forEach(function (h) {
      if (h.getBoundingClientRect().top <= line) chosen = h;
    });
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 2) {
      chosen = headings[headings.length - 1];
    }
    var link = links[chosen.id];
    if (link === current) return;
    if (current) current.classList.remove("active");
    current = link;
    if (current) current.classList.add("active");
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; updateActive(); });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  btn.addEventListener("click", onScroll);
  updateActive();
})();
</script>
</body>
</html>
"""

page = (TEMPLATE
        .replace("__TITLE__", html.escape(title))
        .replace("__TOC__", toc_html)
        .replace("__BODY__", body))

with open(out, "w") as f:
    f.write(page)
print(out)
PY
