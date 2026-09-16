import html
import json
import re
import sys
from pathlib import Path


TOP_LEVEL_FIELDS = {
    "$schema",
    "schemaVersion",
    "id",
    "revision",
    "title",
    "summary",
    "locale",
    "preDraft",
    "goals",
    "users",
    "userStories",
    "requirements",
    "designConsiderations",
    "successMetrics",
    "outOfScope",
    "openQuestions",
    "tasks",
}
REQUIRED_TOP_LEVEL_FIELDS = TOP_LEVEL_FIELDS - {"$schema"}
PRE_DRAFT_FIELDS = {"reuse", "sharedSurfaces", "sourcePriority"}
REQUIREMENT_FIELDS = {"id", "kind", "title", "description", "priority", "status", "acceptance"}
TASK_FIELDS = {"id", "title", "expectedOutcome", "startCondition", "dependsOn", "acceptance", "boundaries"}
TEXT_ARRAY_FIELDS = {
    "goals",
    "users",
    "userStories",
    "designConsiderations",
    "successMetrics",
    "outOfScope",
    "openQuestions",
}
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
TASK_IDENTIFIER_PATTERN = re.compile(r"^T[1-9][0-9]*$")


def require_object(value, path, errors):
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return False
    return True


def require_fields(value, required, allowed, path, errors):
    missing = sorted(required - value.keys())
    extra = sorted(value.keys() - allowed)
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
    if extra:
        errors.append(f"{path}: unsupported fields: {', '.join(extra)}")


def require_text(value, path, errors, pattern=None):
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}: expected non-empty text")
        return False
    if pattern is not None and pattern.fullmatch(value) is None:
        errors.append(f"{path}: invalid identifier '{value}'")
    if pattern is not None and len(value) > 100:
        errors.append(f"{path}: identifiers cannot exceed 100 characters")
    return True


def require_text_array(value, path, errors, non_empty=False, pattern=None):
    if not isinstance(value, list):
        errors.append(f"{path}: expected an array")
        return False
    if non_empty and not value:
        errors.append(f"{path}: expected at least one item")
    for index, item in enumerate(value):
        require_text(item, f"{path}[{index}]", errors, pattern)
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        errors.append(f"{path}: duplicate items are not allowed")
    return True


def validate_document(document):
    errors = []
    if not require_object(document, "$", errors):
        return errors
    require_fields(document, REQUIRED_TOP_LEVEL_FIELDS, TOP_LEVEL_FIELDS, "$", errors)
    if errors:
        return errors
    if document["schemaVersion"] != 1:
        errors.append("$.schemaVersion: expected 1")
    if "$schema" in document:
        require_text(document["$schema"], "$.$schema", errors)
    require_text(document["id"], "$.id", errors, IDENTIFIER_PATTERN)
    require_text(document["revision"], "$.revision", errors)
    require_text(document["title"], "$.title", errors)
    require_text(document["summary"], "$.summary", errors)
    if document["locale"] not in {"fr", "en"}:
        errors.append("$.locale: expected 'fr' or 'en'")
    for field in TEXT_ARRAY_FIELDS:
        require_text_array(document[field], f"$.{field}", errors)
    validate_pre_draft(document["preDraft"], errors)
    requirement_ids = validate_requirements(document["requirements"], errors)
    validate_tasks(document["tasks"], errors)
    if len(requirement_ids) != len(set(requirement_ids)):
        errors.append("$.requirements: requirement IDs must be unique")
    return errors


def validate_pre_draft(pre_draft, errors):
    if not require_object(pre_draft, "$.preDraft", errors):
        return
    require_fields(pre_draft, PRE_DRAFT_FIELDS, PRE_DRAFT_FIELDS, "$.preDraft", errors)
    if PRE_DRAFT_FIELDS - pre_draft.keys():
        return
    require_text_array(pre_draft["reuse"], "$.preDraft.reuse", errors)
    require_text_array(pre_draft["sharedSurfaces"], "$.preDraft.sharedSurfaces", errors)
    require_text_array(pre_draft["sourcePriority"], "$.preDraft.sourcePriority", errors, non_empty=True)


def validate_requirements(requirements, errors):
    if not isinstance(requirements, list) or not requirements:
        errors.append("$.requirements: expected at least one requirement")
        return []
    identifiers = []
    for index, requirement in enumerate(requirements):
        path = f"$.requirements[{index}]"
        if not require_object(requirement, path, errors):
            continue
        require_fields(requirement, REQUIREMENT_FIELDS, REQUIREMENT_FIELDS, path, errors)
        if REQUIREMENT_FIELDS - requirement.keys():
            continue
        if require_text(requirement["id"], f"{path}.id", errors, IDENTIFIER_PATTERN):
            identifiers.append(requirement["id"])
        require_text(requirement["title"], f"{path}.title", errors)
        require_text(requirement["description"], f"{path}.description", errors)
        if requirement["kind"] not in {"functional", "non-functional"}:
            errors.append(f"{path}.kind: unsupported value")
        if requirement["priority"] not in {"must", "should", "could"}:
            errors.append(f"{path}.priority: unsupported value")
        if requirement["status"] not in {"proposed", "approved", "deferred"}:
            errors.append(f"{path}.status: unsupported value")
        require_text_array(requirement["acceptance"], f"{path}.acceptance", errors, non_empty=True)
    return identifiers


def validate_tasks(tasks, errors):
    if not isinstance(tasks, list) or not tasks:
        errors.append("$.tasks: expected at least one task")
        return
    identifiers = []
    dependencies = []
    for index, task in enumerate(tasks):
        path = f"$.tasks[{index}]"
        if not require_object(task, path, errors):
            continue
        require_fields(task, TASK_FIELDS, TASK_FIELDS, path, errors)
        if TASK_FIELDS - task.keys():
            continue
        valid_identifier = require_text(task["id"], f"{path}.id", errors, TASK_IDENTIFIER_PATTERN)
        if valid_identifier:
            identifiers.append(task["id"])
        require_text(task["title"], f"{path}.title", errors)
        require_text(task["expectedOutcome"], f"{path}.expectedOutcome", errors)
        require_text(task["startCondition"], f"{path}.startCondition", errors)
        valid_dependencies = require_text_array(task["dependsOn"], f"{path}.dependsOn", errors, pattern=TASK_IDENTIFIER_PATTERN)
        require_text_array(task["acceptance"], f"{path}.acceptance", errors, non_empty=True)
        require_text_array(task["boundaries"], f"{path}.boundaries", errors, non_empty=True)
        if valid_identifier and valid_dependencies:
            dependencies.append((task["id"], task["dependsOn"]))
    if len(identifiers) != len(set(identifiers)):
        errors.append("$.tasks: task IDs must be unique")
    known = set(identifiers)
    for task_id, task_dependencies in dependencies:
        for dependency in task_dependencies:
            if dependency == task_id:
                errors.append(f"$.tasks[{task_id}].dependsOn: a task cannot depend on itself")
            elif dependency not in known:
                errors.append(f"$.tasks[{task_id}].dependsOn: unknown task '{dependency}'")
    validate_dependency_cycles(dependencies, known, errors)


def validate_dependency_cycles(dependencies, known, errors):
    graph = {task_id: [dependency for dependency in task_dependencies if dependency in known] for task_id, task_dependencies in dependencies}
    visiting = set()
    visited = set()

    def visit(task_id):
        if task_id in visiting:
            errors.append(f"$.tasks: dependency cycle includes '{task_id}'")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in graph.get(task_id, []):
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id)


def escape(value):
    return html.escape(value, quote=True)


def list_html(items):
    if not items:
        return '<p class="empty">None recorded.</p>'
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def section(identifier, title, content):
    return f'<section aria-labelledby="{identifier}"><h2 id="{identifier}">{escape(title)}</h2>{content}</section>'


def render_requirements(requirements):
    rows = []
    for requirement in requirements:
        acceptance = list_html(requirement["acceptance"])
        rows.append(
            "<tr>"
            f'<td><code>{escape(requirement["id"])}</code></td>'
            f'<td>{escape(requirement["kind"])}</td>'
            f'<td><strong>{escape(requirement["title"])}</strong><br>{escape(requirement["description"])}</td>'
            f'<td>{escape(requirement["priority"])}</td>'
            f'<td>{escape(requirement["status"])}</td>'
            f"<td>{acceptance}</td>"
            "</tr>"
        )
    return '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Kind</th><th>Requirement</th><th>Priority</th><th>Status</th><th>Acceptance</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"


def render_tasks(tasks):
    cards = []
    for task in tasks:
        dependencies = ", ".join(task["dependsOn"]) or "None"
        cards.append(
            '<article class="task">'
            f'<h3><input type="checkbox" disabled aria-label="{escape(task["id"])} complete"> <code>{escape(task["id"])}</code> {escape(task["title"])}</h3>'
            f'<dl><dt>Expected outcome</dt><dd>{escape(task["expectedOutcome"])}</dd>'
            f'<dt>Dependencies / start condition</dt><dd>{escape(task["startCondition"])}<br><span class="muted">Depends on: {escape(dependencies)}</span></dd>'
            f'<dt>Observable acceptance criteria</dt><dd>{list_html(task["acceptance"])}</dd>'
            f'<dt>Relevant boundaries</dt><dd>{list_html(task["boundaries"])}</dd></dl>'
            "</article>"
        )
    return "".join(cards)


def render_document(document):
    labels = {
        "preDraft": "Pre-draft findings",
        "goals": "Goals / Objectives",
        "users": "Target audience / User personas",
        "userStories": "User stories / Use cases",
        "requirements": "Requirements",
        "designConsiderations": "Design considerations / Mockups",
        "successMetrics": "Success metrics",
        "outOfScope": "Out of scope",
        "openQuestions": "Open questions / Future considerations",
        "tasks": "Tasks",
    }
    pre_draft = document["preDraft"]
    pre_draft_html = (
        "<h3>Reuse map</h3>" + list_html(pre_draft["reuse"])
        + "<h3>Shared-surface impact and strategy</h3>" + list_html(pre_draft["sharedSurfaces"])
        + "<h3>Source-priority order</h3>" + list_html(pre_draft["sourcePriority"])
    )
    sections = [
        section("pre-draft", labels["preDraft"], pre_draft_html),
        section("goals", labels["goals"], list_html(document["goals"])),
        section("users", labels["users"], list_html(document["users"])),
        section("user-stories", labels["userStories"], list_html(document["userStories"])),
        section("requirements", labels["requirements"], render_requirements(document["requirements"])),
        section("design", labels["designConsiderations"], list_html(document["designConsiderations"])),
        section("metrics", labels["successMetrics"], list_html(document["successMetrics"])),
        section("out-of-scope", labels["outOfScope"], list_html(document["outOfScope"])),
        section("open-questions", labels["openQuestions"], list_html(document["openQuestions"])),
        section("tasks", labels["tasks"], render_tasks(document["tasks"])),
    ]
    navigation = "".join(
        f'<li><a href="#{identifier}">{escape(label)}</a></li>'
        for identifier, label in [
            ("pre-draft", labels["preDraft"]), ("goals", labels["goals"]),
            ("users", labels["users"]), ("user-stories", labels["userStories"]),
            ("requirements", labels["requirements"]), ("design", labels["designConsiderations"]),
            ("metrics", labels["successMetrics"]), ("out-of-scope", labels["outOfScope"]),
            ("open-questions", labels["openQuestions"]), ("tasks", labels["tasks"]),
        ]
    )
    language = escape(document["locale"])
    title = escape(document["title"])
    summary = escape(document["summary"])
    document_id = escape(document["id"])
    revision = escape(document["revision"])
    body = "".join(sections)
    return f'''<!doctype html>
<html lang="{language}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#f6f7fb;--surface:#fff;--fg:#1f2430;--muted:#5b6270;--border:#e4e7ee;--accent:#4f46e5;--soft:#eef2ff}}
*{{box-sizing:border-box}}html{{color-scheme:light;scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}body::before{{content:"";display:block;height:6px;background:linear-gradient(90deg,#4f46e5,#7c3aed,#db2777)}}.layout{{display:grid;grid-template-columns:15rem minmax(0,1fr);gap:2.5rem;max-width:80rem;margin:auto;padding:2rem 1.5rem 5rem}}aside{{position:sticky;top:1rem;align-self:start;max-height:calc(100vh - 2rem);overflow:auto}}main{{min-width:0}}h1{{font-size:2.1rem;line-height:1.2;margin:.5rem 0}}h2{{font-size:1.3rem;margin-top:3rem;padding-bottom:.4rem;border-bottom:1px solid var(--border);scroll-margin-top:1rem}}h2::before{{content:"";display:inline-block;width:.55rem;height:.55rem;border-radius:2px;background:var(--accent);margin-right:.55rem}}h3{{margin-top:1.5rem}}a{{color:var(--accent)}}code{{background:#f1f3f8;border:1px solid var(--border);border-radius:5px;padding:.08em .35em}}nav,.task{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;box-shadow:0 1px 3px #1f24300f}}nav strong{{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}nav ul{{list-style:none;padding:0;margin:.5rem 0 0}}nav a{{display:block;text-decoration:none;color:var(--fg);font-size:.88rem;padding:.14rem 0}}nav a:hover{{color:var(--accent)}}.summary{{font-size:1.12rem;max-width:52rem}}.meta,.muted,.empty{{color:var(--muted)}}section:first-of-type{{background:var(--soft);border:1px solid #c7d2fe;border-radius:12px;padding:0 1.2rem 1rem;margin-top:2rem}}section:first-of-type h2{{margin-top:1rem}}.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:var(--surface)}}th,td{{border:1px solid var(--border);padding:.6rem .7rem;text-align:left;vertical-align:top}}th{{background:var(--soft);font-size:.8rem;text-transform:uppercase}}td ul{{margin:0;padding-left:1.1rem}}.task{{margin:1rem 0}}.task h3{{margin:.1rem 0 1rem}}.task input{{accent-color:var(--accent)}}dl{{margin:0}}dt{{font-weight:700;margin-top:.75rem}}dd{{margin:.15rem 0 0}}dd ul{{margin:.2rem 0}}button{{margin-top:.8rem;border:1px solid var(--border);background:var(--surface);color:var(--muted);border-radius:99px;padding:.5rem .9rem;cursor:pointer}}body.compact main{{font-size:14px;line-height:1.4}}body.compact h2{{margin-top:1.7rem}}body.compact .task{{padding:.65rem .9rem}}@media(max-width:900px){{.layout{{grid-template-columns:1fr}}aside{{position:static;max-height:none}}}}@media print{{body::before,aside{{display:none}}.layout{{display:block;padding:0}}.task{{break-inside:avoid}}}}
</style>
</head>
<body>
<div class="layout"><aside><nav aria-label="Document sections"><strong>Contents</strong><ul>{navigation}</ul></nav><button id="density" type="button">Compact mode</button></aside><main><header><p class="meta"><code>{document_id}</code> · Revision {revision}</p><h1>{title}</h1><p class="summary">{summary}</p></header>{body}</main></div>
<script>const button=document.getElementById("density");const apply=compact=>{{document.body.classList.toggle("compact",compact);button.textContent=compact?"Comfort mode":"Compact mode"}};apply(localStorage.getItem("prd-density")==="compact");button.addEventListener("click",()=>{{const compact=!document.body.classList.contains("compact");localStorage.setItem("prd-density",compact?"compact":"comfort");apply(compact)}});</script>
</body>
</html>'''


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: renderPrd.py <file.prd.json> <output.html>")
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    try:
        document = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error
    errors = validate_document(document)
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"validation failed:\n{details}")
    output_path.write_text(render_document(document), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
