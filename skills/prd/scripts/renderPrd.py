import argparse
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
    "axes",
    "sources",
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
AXIS_FIELDS = {"id", "title", "summary"}
SOURCE_FIELDS = {"title", "ref"}
REQUIREMENT_FIELDS = {"id", "axis", "kind", "title", "description", "priority", "status", "acceptance"}
TASK_FIELDS = {"id", "axis", "title", "expectedOutcome", "startCondition", "dependsOn", "acceptance", "boundaries"}
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
AXIS_IDENTIFIER_PATTERN = re.compile(r"^A[1-9][0-9]*$")
SCHEMA_VERSION = 2
MAX_AXES = 5


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
    if document["schemaVersion"] != SCHEMA_VERSION:
        errors.append(f"$.schemaVersion: expected {SCHEMA_VERSION}")
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
    validate_sources(document["sources"], errors)
    axis_ids = validate_axes(document["axes"], errors)
    requirement_ids, covered_axes = validate_requirements(document["requirements"], errors, axis_ids)
    validate_tasks(document["tasks"], errors, axis_ids)
    if len(requirement_ids) != len(set(requirement_ids)):
        errors.append("$.requirements: requirement IDs must be unique")
    for axis_id in axis_ids:
        if axis_id not in covered_axes:
            errors.append(f"$.axes: axis '{axis_id}' has no requirement")
    return errors


def validate_sources(sources, errors):
    if not isinstance(sources, list):
        errors.append("$.sources: expected an array")
        return
    entries = []
    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        if not require_object(source, path, errors):
            continue
        require_fields(source, SOURCE_FIELDS, SOURCE_FIELDS, path, errors)
        if SOURCE_FIELDS - source.keys():
            continue
        title_is_text = require_text(source["title"], f"{path}.title", errors)
        ref_is_text = require_text(source["ref"], f"{path}.ref", errors)
        if title_is_text and ref_is_text:
            entries.append((source["title"], source["ref"]))
    if len(entries) != len(set(entries)):
        errors.append("$.sources: duplicate items are not allowed")


def validate_axes(axes, errors):
    if not isinstance(axes, list) or not axes:
        errors.append("$.axes: expected at least one axis")
        return []
    if len(axes) > MAX_AXES:
        errors.append(f"$.axes: expected at most {MAX_AXES} axes")
    identifiers = []
    for index, axis in enumerate(axes):
        path = f"$.axes[{index}]"
        if not require_object(axis, path, errors):
            continue
        require_fields(axis, AXIS_FIELDS, AXIS_FIELDS, path, errors)
        if AXIS_FIELDS - axis.keys():
            continue
        if require_text(axis["id"], f"{path}.id", errors, AXIS_IDENTIFIER_PATTERN):
            identifiers.append(axis["id"])
        require_text(axis["title"], f"{path}.title", errors)
        require_text(axis["summary"], f"{path}.summary", errors)
    if len(identifiers) != len(set(identifiers)):
        errors.append("$.axes: axis IDs must be unique")
    return identifiers


def validate_axis_reference(value, path, errors, axis_ids):
    if not require_text(value, path, errors, AXIS_IDENTIFIER_PATTERN):
        return None
    if axis_ids and value not in axis_ids:
        errors.append(f"{path}: unknown axis '{value}'")
        return None
    return value


def validate_pre_draft(pre_draft, errors):
    if not require_object(pre_draft, "$.preDraft", errors):
        return
    require_fields(pre_draft, PRE_DRAFT_FIELDS, PRE_DRAFT_FIELDS, "$.preDraft", errors)
    if PRE_DRAFT_FIELDS - pre_draft.keys():
        return
    require_text_array(pre_draft["reuse"], "$.preDraft.reuse", errors)
    require_text_array(pre_draft["sharedSurfaces"], "$.preDraft.sharedSurfaces", errors)
    require_text_array(pre_draft["sourcePriority"], "$.preDraft.sourcePriority", errors, non_empty=True)


def validate_requirements(requirements, errors, axis_ids):
    if not isinstance(requirements, list) or not requirements:
        errors.append("$.requirements: expected at least one requirement")
        return [], set()
    identifiers = []
    covered_axes = set()
    for index, requirement in enumerate(requirements):
        path = f"$.requirements[{index}]"
        if not require_object(requirement, path, errors):
            continue
        require_fields(requirement, REQUIREMENT_FIELDS, REQUIREMENT_FIELDS, path, errors)
        if REQUIREMENT_FIELDS - requirement.keys():
            continue
        if require_text(requirement["id"], f"{path}.id", errors, IDENTIFIER_PATTERN):
            identifiers.append(requirement["id"])
        axis = validate_axis_reference(requirement["axis"], f"{path}.axis", errors, axis_ids)
        if axis is not None:
            covered_axes.add(axis)
        require_text(requirement["title"], f"{path}.title", errors)
        require_text(requirement["description"], f"{path}.description", errors)
        if requirement["kind"] not in {"functional", "non-functional"}:
            errors.append(f"{path}.kind: unsupported value")
        if requirement["priority"] not in {"must", "should", "could"}:
            errors.append(f"{path}.priority: unsupported value")
        if requirement["status"] not in {"proposed", "approved", "deferred"}:
            errors.append(f"{path}.status: unsupported value")
        require_text_array(requirement["acceptance"], f"{path}.acceptance", errors, non_empty=True)
    return identifiers, covered_axes


def validate_tasks(tasks, errors, axis_ids):
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
        validate_axis_reference(task["axis"], f"{path}.axis", errors, axis_ids)
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


DEFAULT_SOURCE_PRIORITY = ["user instruction", "Figma mockup", "business document", "existing code"]
WORDS_PER_MINUTE = 200
MINIMUM_READING_MINUTES = 1
SINGULAR_COUNT = 1
SUMMARY_WORD_BUDGET = 60
AXIS_SUMMARY_WORD_BUDGET = 20
LIST_ITEM_WORD_BUDGET = 25
REQUIREMENT_DESCRIPTION_WORD_BUDGET = 40
ACCEPTANCE_WORD_BUDGET = 30
EXPECTED_OUTCOME_WORD_BUDGET = 30
MAX_MUST_REQUIREMENTS = 7
MAX_ACCEPTANCE_ITEMS = 5
MUST_PRIORITY = "must"
BUDGETED_LIST_FIELDS = ("goals", "successMetrics", "outOfScope")
SECONDARY_FIELDS = ("users", "userStories", "designConsiderations", "successMetrics")
WARNING_PREFIX = "warning: "
DENSITY_STORAGE_KEY = "prd-density"
AGENT_STORAGE_KEY = "prd-agent-context"
THEME_STORAGE_KEY = "prd-theme"
THEME_ATTRIBUTE = "data-theme"
DARK_THEME_VALUE = "dark"
LIGHT_THEME_VALUE = "light"
COUNT_SEPARATOR = " · "
COUNT_PLACEHOLDER = "{count}"
COUNT_DECISION_CLASS = "count-decision"
DEPENDENCY_SEPARATOR = ", "
SOURCE_SEPARATOR = ", "
LINK_PREFIXES = ("http://", "https://")
SLIDE_KIND_ATTRIBUTE = "data-slide-kind"
SLIDE_TITLE_ATTRIBUTE = "data-slide-title"
SLIDE_REF_ATTRIBUTE = "data-slide-ref"
SLIDE_KEY_ATTRIBUTE = "data-slide-key"
PRESENTING_KIND_ATTRIBUTE = "data-presenting-kind"
SLIDE_DENSE_CLASS = "slide-dense"
DENSE_SLIDE_ITEM_THRESHOLD = 4
KIND_CONTEXT = "context"
KIND_DECISION = "decision"
KIND_AXIS = "axis"
KIND_REQUIREMENT = "requirement"
KIND_TASK = "task"
KIND_LABEL_KEYS = {
    KIND_CONTEXT: "kindContext",
    KIND_DECISION: "kindDecision",
    KIND_AXIS: "kindAxis",
    KIND_REQUIREMENT: "kindRequirement",
    KIND_TASK: "kindTask",
}
AXIS_KEY_PREFIX = "axis:"
REQUIREMENT_KEY_PREFIX = "requirement:"
TASK_KEY_PREFIX = "task:"
AXIS_ANCHOR_PREFIX = "axis-"
REQUIREMENT_ANCHOR_PREFIX = "req-"
TASK_ANCHOR_PREFIX = "task-"
SLIDE_TARGET_ATTRIBUTE = "data-slide-target"
PRESENTATION_RAIL_ID = "presentation-rail"
PRESENTATION_GRID_ID = "presentation-grid"
PRESENTATION_OVERVIEW_ID = "presentation-overview"
PAGE_HEAD_ID = "page-head"
CHANGES_ID = "changes"
BRIEF_ID = "brief"
DECISIONS_ID = "decisions"
AXES_ID = "axes"
OUT_OF_SCOPE_ID = "out-of-scope"
SECONDARY_ID = "secondary"
IMPACT_ID = "impact"
AGENT_CONTEXT_ID = "agent-context"
AGENT_NAV_ID = "agent-context-nav"
AGENT_NOTE_ID = "agent-note"
CHANGES_BUTTON_ID = "changes-only"
DEPENDENCIES_PLACEHOLDER = "{dependencies}"
CHANGE_NEW = "new"
CHANGE_MODIFIED = "changed"
CHANGE_SAME = "same"
CHANGE_ATTRIBUTE = "data-change"
CHANGE_LABEL_KEYS = {CHANGE_NEW: "changeNew", CHANGE_MODIFIED: "changeModified"}
DIFFED_FIELDS = ("axes", "requirements", "tasks")
QUESTIONS_FIELD = "openQuestions"
ID_FIELD = "id"
REVISION_FIELD = "revision"
SCHEMA_VERSION_FIELD = "schemaVersion"
NOTE_PREFIX = "note: "
OUT_OF_SCOPE_BLOCK = (OUT_OF_SCOPE_ID, "outOfScope", "outOfScope", "block slide", "ul", KIND_CONTEXT)
TOOLBAR_BUTTONS = (
    ("density", "compact"),
    ("agent-toggle", "showAgent"),
    ("expand-all", "expandAll"),
    ("presentation", "presentation"),
    ("theme", "darkTheme"),
)
CHANGES_TOOLBAR_BUTTON = (CHANGES_BUTTON_ID, "changesOnly")
VAGUE_WORDS = {
    "fr": (
        "rapide", "rapidement", "intuitif", "intuitive", "robuste", "fluide", "simple", "simplement",
        "sécurisé", "sécurisée", "performant", "performante", "ergonomique", "convivial", "efficace",
    ),
    "en": (
        "fast", "quickly", "intuitive", "robust", "seamless", "simple", "easy", "secure", "performant",
        "user-friendly", "efficient",
    ),
}
VAGUE_WORD_PATTERNS = {
    locale: re.compile(r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\b", re.IGNORECASE)
    for locale, words in VAGUE_WORDS.items()
}
EDGE_CASE_PATTERNS = {
    "fr": re.compile(r"^(?:Si|S['’]il)\b", re.IGNORECASE),
    "en": re.compile(r"^If\b", re.IGNORECASE),
}

LABELS = {
    "fr": {
        "brief": "Résumé",
        "revision": "Révision",
        "contents": "Sommaire",
        "decisions": "Décisions attendues",
        "need": "Besoin",
        "goals": "Objectifs",
        "axes": "Axes",
        "sources": "Sources",
        "outOfScope": "Hors périmètre",
        "requirements": "Exigences",
        "tasks": "Tâches",
        "secondary": "Contexte complémentaire",
        "users": "Utilisateurs cibles",
        "userStories": "Récits utilisateurs",
        "designConsiderations": "Considérations de design",
        "successMetrics": "Indicateurs de succès",
        "impact": "Impact et compatibilité",
        "agentContext": "Contexte agent",
        "reuse": "Carte de réutilisation",
        "sourcePriority": "Ordre de priorité des sources",
        "boundaries": "Périmètre",
        "mustGroup": "Indispensable",
        "otherGroup": "Ensuite",
        "acceptance": "Critères observables",
        "startCondition": "Condition de démarrage",
        "afterChip": "après {dependencies}",
        "countRequirements": {"one": "{count} exigence", "many": "{count} exigences"},
        "countTasks": {"one": "{count} tâche", "many": "{count} tâches"},
        "countQuestions": {"one": "{count} question ouverte", "many": "{count} questions ouvertes"},
        "countReadingTime": {"one": "~{count} min de lecture", "many": "~{count} min de lecture"},
        "agentHiddenNote": "{count} entrées réservées à l'agent sont masquées — elles restent dans le JSON",
        "showAgent": "Afficher le contexte agent",
        "hideAgent": "Masquer le contexte agent",
        "expandAll": "Tout déplier",
        "collapseAll": "Tout replier",
        "presentation": "Mode présentation",
        "exitPresentation": "Quitter la présentation",
        "overview": "Vue d'ensemble (g)",
        "kindContext": "Contexte",
        "kindDecision": "Décision attendue",
        "kindAxis": "Axe",
        "kindRequirement": "Exigence",
        "kindTask": "Tâche",
        "previous": "Précédent",
        "next": "Suivant",
        "compact": "Mode compact",
        "comfort": "Mode confort",
        "darkTheme": "Thème sombre",
        "lightTheme": "Thème clair",
        "empty": "Aucun élément.",
        "crossAxisDependency": "Tâche de l'axe {axis}",
        "changesOnly": "Seulement les changements",
        "showAll": "Tout afficher",
        "changeNew": "nouveau",
        "changeModified": "modifié",
        "changesSince": "Changements depuis la révision {revision}",
        "changesSincePrevious": "Changements depuis la révision précédente",
        "removed": "Retirés : {items}",
        "countNew": {"one": "{count} nouveau", "many": "{count} nouveaux"},
        "countModified": {"one": "{count} modifié", "many": "{count} modifiés"},
    },
    "en": {
        "brief": "Brief",
        "revision": "Revision",
        "contents": "Contents",
        "decisions": "Decisions needed",
        "need": "Need",
        "goals": "Goals",
        "axes": "Axes",
        "sources": "Sources",
        "outOfScope": "Out of scope",
        "requirements": "Requirements",
        "tasks": "Tasks",
        "secondary": "Additional context",
        "users": "Target users",
        "userStories": "User stories",
        "designConsiderations": "Design considerations",
        "successMetrics": "Success metrics",
        "impact": "Impact and compatibility",
        "agentContext": "Agent context",
        "reuse": "Reuse map",
        "sourcePriority": "Source priority order",
        "boundaries": "Boundaries",
        "mustGroup": "Must have",
        "otherGroup": "Next",
        "acceptance": "Observable acceptance",
        "startCondition": "Start condition",
        "afterChip": "after {dependencies}",
        "countRequirements": {"one": "{count} requirement", "many": "{count} requirements"},
        "countTasks": {"one": "{count} task", "many": "{count} tasks"},
        "countQuestions": {"one": "{count} open question", "many": "{count} open questions"},
        "countReadingTime": {"one": "~{count} min read", "many": "~{count} min read"},
        "agentHiddenNote": "{count} entries reserved for the agent are hidden — they stay in the JSON",
        "showAgent": "Show agent context",
        "hideAgent": "Hide agent context",
        "expandAll": "Expand all",
        "collapseAll": "Collapse all",
        "presentation": "Presentation mode",
        "exitPresentation": "Exit presentation",
        "overview": "Overview (g)",
        "kindContext": "Context",
        "kindDecision": "Decision needed",
        "kindAxis": "Axis",
        "kindRequirement": "Requirement",
        "kindTask": "Task",
        "previous": "Previous",
        "next": "Next",
        "compact": "Compact mode",
        "comfort": "Comfort mode",
        "darkTheme": "Dark theme",
        "lightTheme": "Light theme",
        "empty": "None recorded.",
        "crossAxisDependency": "Task in axis {axis}",
        "changesOnly": "Only changes",
        "showAll": "Show everything",
        "changeNew": "new",
        "changeModified": "changed",
        "changesSince": "Changes since revision {revision}",
        "changesSincePrevious": "Changes since the previous revision",
        "removed": "Removed: {items}",
        "countNew": {"one": "{count} new", "many": "{count} new"},
        "countModified": {"one": "{count} changed", "many": "{count} changed"},
    },
}

LIGHT_TOKENS_PLACEHOLDER = "__LIGHT_TOKENS__"
DARK_TOKENS_PLACEHOLDER = "__DARK_TOKENS__"

LIGHT_TOKENS = """color-scheme:light;
  --bg:#f6f7f9;--surface:#ffffff;--fg:#191b20;--muted:#5b616d;--border:#e1e4ea;
  --accent:#3a4fb8;--accent-soft:#eef1fb;--decision-bg:#fdf6e6;--decision-border:#e0c98d;
  --decision-fg:#7a5a0c;--task:#1f7a6b;--ghost:#e6eaf2;
  --chip-bg:#eef1fb;--code-bg:#f0f2f6;--print-border:#cccccc;--measure:70ch;"""

DARK_TOKENS = """color-scheme:dark;
  --bg:#121317;--surface:#1a1c22;--fg:#e7e8ec;--muted:#a2a7b3;--border:#2b2e37;
  --accent:#9aa9f5;--accent-soft:#222639;--decision-bg:#2a2416;--decision-border:#5a4c27;
  --decision-fg:#e6c777;--task:#6fd0bd;--ghost:#232732;
  --chip-bg:#222639;--code-bg:#22252d;--print-border:#cccccc;--measure:70ch;"""

STYLE_TEMPLATE = """
:root{
  __LIGHT_TOKENS__
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    __DARK_TOKENS__
  }
}
:root[data-theme="dark"]{
  __DARK_TOKENS__
}
:root{
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --pres-topbar:2.9rem;--pres-bar:4.4rem;--pres-rail:1.9rem;
  --stage-max:1200px;--stage-pad:clamp(1rem,4vw,3.5rem);--slide-gap:clamp(.6rem,1.5vh,1.4rem);
  --slide-title:clamp(2rem,4.5vw + 1vh,4.5rem);
  --slide-lede:clamp(1.15rem,1.4vw + .7vh,2rem);
  --slide-body:clamp(1.15rem,1.2vw + .6vh,1.75rem);
  --slide-eyebrow:clamp(.72rem,.4vw + .3vh,1.05rem);
  --slide-number:clamp(2.3rem,3.4vw + 1.4vh,4.6rem);
  --slide-ghost:clamp(5rem,14vw,12rem);
  --title-measure:34ch;--body-measure:60ch;
}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);overflow-wrap:anywhere;
  font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.topbar{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;justify-content:space-between;
  padding:.6rem 1.25rem;background:var(--surface);border-bottom:1px solid var(--border)}
.topbar-title{font-size:.82rem;font-weight:600;letter-spacing:.02em;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:24rem}
.toolbar{display:flex;flex-wrap:wrap;gap:.4rem}
button{font:inherit;font-size:.82rem;border:1px solid var(--border);background:var(--surface);color:var(--fg);
  border-radius:99px;padding:.34rem .8rem;cursor:pointer}
button:hover{border-color:var(--accent);color:var(--accent)}
button[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.layout{display:grid;grid-template-columns:14rem minmax(0,1fr);gap:2.5rem;max-width:74rem;margin:0 auto;padding:1.75rem 1.25rem 4rem}
aside{position:sticky;top:4.2rem;align-self:start;max-height:calc(100vh - 5.5rem);overflow:auto}
main{min-width:0}
nav{border:1px solid var(--border);border-radius:10px;background:var(--surface);padding:.85rem .95rem}
nav strong{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
nav ul{list-style:none;margin:.5rem 0 0;padding:0}
nav a{display:block;padding:.16rem 0;font-size:.86rem;color:var(--fg);text-decoration:none}
nav a:hover{color:var(--accent)}
nav .nav-sub{margin:0 0 .2rem;padding-left:.8rem;border-left:1px solid var(--border)}
nav .nav-sub a{font-size:.8rem;color:var(--muted)}
h1{font-size:1.9rem;line-height:1.2;margin:.4rem 0 .6rem;max-width:var(--measure)}
h2{font-size:1.18rem;line-height:1.3;margin:0 0 .9rem;scroll-margin-top:4.5rem}
h3,h4{font-size:.95rem;margin:1.2rem 0 .4rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
h4{font-size:.82rem}
section[id],details[id]{scroll-margin-top:4.5rem}
.page-head{margin:0 0 1.6rem}
.changes-banner{margin:0 0 1.6rem;padding:.7rem 1rem;border:1px solid var(--accent);border-radius:10px;background:var(--accent-soft)}
.changes-banner p{margin:0;font-size:.9rem}
.axis-section{margin:0 0 2.6rem}
.axis-head>h2{padding-bottom:.4rem;border-bottom:1px solid var(--border)}
.axis-part>h3{margin-top:1.4rem}
.group-label{margin:.7rem 0 .35rem;font-size:.8rem;font-weight:600;color:var(--muted)}
.dep-link{color:inherit;text-decoration:underline dotted;text-underline-offset:2px}
.dep-cross{padding:0 .3em;border:1px dashed var(--task);border-radius:4px;text-decoration:none}
.axes a{color:var(--fg);text-decoration:none}
.axes a:hover .axis-name{color:var(--accent)}
p,li{max-width:var(--measure)}
a{color:var(--accent)}
code{background:var(--code-bg);border:1px solid var(--border);border-radius:5px;padding:.05em .32em;font-size:.86em}
.meta{color:var(--muted);font-size:.85rem;margin:0}
.summary{font-size:1.08rem;margin:0 0 1rem}
.counts{color:var(--muted);font-size:.86rem;margin:0}
.block{margin:0 0 2.2rem;padding:0}
.block>h2{padding-bottom:.4rem;border-bottom:1px solid var(--border)}
.decisions{background:var(--decision-bg);border:1px solid var(--decision-border);border-radius:12px;padding:1.1rem 1.2rem}
.decisions>h2{border-bottom:0;padding-bottom:0}
.decisions ol{margin:0;padding-left:1.2rem}
.decisions li{margin:.35rem 0}
.item{background:var(--surface);border:1px solid var(--border);border-radius:10px;margin:0 0 .5rem;padding:.55rem .85rem}
.item>summary{display:block;list-style:none;cursor:pointer}
.item>summary::-webkit-details-marker{display:none}
.item>summary::before{content:"▸";display:inline-block;width:1rem;color:var(--muted)}
.item[open]>summary::before{content:"▾"}
.item-title{font-weight:600}
.item-body{padding:.35rem 0 .2rem 1rem;border-top:1px solid var(--border);margin-top:.55rem}
.item-body ul{margin:.3rem 0;padding-left:1.1rem}
.outcome{display:block;margin:.25rem 0 0 1rem;color:var(--muted);font-size:.92rem;max-width:var(--measure)}
.axis-name{font-weight:600}
.sources ul{margin:.3rem 0 0;padding-left:1.1rem}
.sources li{font-size:.9rem}
.sources-footer{display:none}
.axes li{margin:.35rem 0}
.badge{display:inline-block;margin-left:.4rem;padding:.02rem .45rem;border-radius:99px;font-size:.72rem;
  border:1px solid var(--border);background:var(--chip-bg);color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.badge-must{border-color:var(--accent);color:var(--accent)}
.badge-new{border-color:var(--task);color:var(--task)}
.badge-changed{border-color:var(--decision-border);color:var(--decision-fg);background:var(--decision-bg)}
body.changes-only:not(.presenting) [data-change="same"]{display:none}
.chip{display:inline-block;margin-left:.4rem;padding:.02rem .45rem;border-radius:99px;font-size:.72rem;
  background:var(--chip-bg);color:var(--muted)}
.group>summary{cursor:pointer;font-weight:600}
.group>summary h2{display:inline;border-bottom:0;font-size:1.18rem}
.sub{border-top:1px solid var(--border);padding:.5rem 0}
.sub>summary{cursor:pointer;color:var(--muted)}
.agent-block{border:1px dashed var(--border);border-radius:10px;padding:1rem 1.2rem;background:var(--surface)}
.agent-note{color:var(--muted);font-size:.85rem;font-style:italic;margin:2rem 0 0}
.empty,.muted{color:var(--muted)}
.presentation-bar{position:fixed;left:50%;bottom:1rem;transform:translateX(-50%);display:flex;gap:.5rem;align-items:center;
  background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:.4rem .7rem;z-index:10}
.presentation-counter{font-size:.82rem;color:var(--muted);min-width:4rem;text-align:center;font-variant-numeric:tabular-nums}
.presentation-rail{position:fixed;left:0;right:0;top:var(--pres-topbar);z-index:6;
  display:flex;gap:2px;align-items:flex-end;height:var(--pres-rail);padding:.55rem clamp(.5rem,2vw,1.2rem) 0}
.rail-segment{flex:1 1 0;min-width:0;height:6px;padding:0;border:0;border-radius:2px;background:var(--border);cursor:pointer}
.rail-segment:hover{border-color:transparent}
.rail-segment[data-slide-kind="decision"]{background:var(--decision-border)}
.rail-segment[data-slide-kind="axis"]{background:var(--muted)}
.rail-segment[data-slide-kind="requirement"]{background:var(--accent)}
.rail-segment[data-slide-kind="task"]{background:var(--task)}
.rail-segment.is-past{opacity:.3}
.rail-segment.is-current{height:13px;background:var(--fg);opacity:1}
.presentation-grid{position:fixed;left:0;right:0;top:calc(var(--pres-topbar) + var(--pres-rail));bottom:var(--pres-bar);
  z-index:7;overflow:auto;background:var(--bg);padding:clamp(.8rem,2vw,1.5rem);
  display:grid;grid-template-columns:repeat(auto-fill,minmax(10.5rem,1fr));gap:.6rem;align-content:start}
.grid-tile{display:flex;flex-direction:column;gap:.2rem;text-align:left;border-radius:6px;
  border:1px solid var(--border);border-top:3px solid var(--border);background:var(--surface);
  padding:.5rem .6rem;font-size:.78rem;line-height:1.3;cursor:pointer}
.grid-tile:hover{color:var(--fg)}
.grid-tile[data-slide-kind="decision"]{border-top-color:var(--decision-border)}
.grid-tile[data-slide-kind="axis"]{border-top-color:var(--muted)}
.grid-tile[data-slide-kind="requirement"]{border-top-color:var(--accent)}
.grid-tile[data-slide-kind="task"]{border-top-color:var(--task)}
.grid-tile.is-current{outline:2px solid var(--fg);outline-offset:1px}
.grid-tile-ref{font-family:var(--mono);font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
body.presenting{overflow:hidden}
body.presenting .topbar{height:var(--pres-topbar);flex-wrap:nowrap;gap:.4rem;padding:.25rem .8rem;overflow:hidden}
body.presenting .topbar-title{font-size:.72rem;max-width:45vw}
body.presenting #density,body.presenting #agent-toggle,body.presenting #expand-all,body.presenting #changes-only{display:none}
body.presenting aside,body.presenting .agent-note,body.presenting .changes-banner{display:none}
body.presenting .layout{display:block;max-width:none;margin:0;padding:0}
body.presenting main{height:calc(100vh - var(--pres-topbar) - var(--pres-bar));
  height:calc(100dvh - var(--pres-topbar) - var(--pres-bar));overflow:auto;
  display:grid;align-content:safe center;justify-items:center;
  padding:calc(var(--pres-rail) + var(--stage-pad)) var(--stage-pad) var(--stage-pad)}
body.presenting .slide{width:min(100%,var(--stage-max));margin:0}
body.presenting .block,body.presenting .axis-section,body.presenting .axis-part,body.presenting .page-head{
  margin:0;padding:0;width:min(100%,var(--stage-max))}
body.presenting .page-head{margin-bottom:var(--slide-gap);display:flex;flex-direction:column;gap:var(--slide-gap)}
body.presenting .pres-group{display:flex;flex-direction:column;gap:var(--slide-gap)}
body.presenting .axis-part>h3,body.presenting .need>h2{font-size:var(--slide-eyebrow);font-weight:600;text-transform:uppercase;
  letter-spacing:.12em;color:var(--muted);border-bottom:0;padding:0;margin:0;max-width:none}
body.presenting .group-label{display:none}
body.presenting header.slide,body.presenting section.slide,body.presenting div.slide{display:flex;flex-direction:column;gap:var(--slide-gap)}
body.presenting .slide h1,body.presenting .page-head h1,body.presenting .slide>h2,body.presenting .group>summary h2,body.presenting .item-title{
  font-size:var(--slide-title);line-height:1.08;letter-spacing:-.025em;font-weight:700;
  max-width:var(--title-measure);margin:0;border:0;padding:0;text-wrap:balance}
body.presenting .need>h2{font-size:var(--slide-eyebrow);letter-spacing:.12em;font-weight:600;line-height:1.3}
body.presenting .slide p,body.presenting .slide li{font-size:var(--slide-body);line-height:1.45;max-width:var(--body-measure)}
body.presenting .slide ul,body.presenting .slide ol{display:flex;flex-direction:column;gap:.45em;margin:0;padding-left:1.1em}
body.presenting .slide .summary{font-size:var(--slide-lede);color:var(--muted);margin:0}
body.presenting .meta{font-size:var(--slide-eyebrow);text-transform:uppercase;letter-spacing:.12em;margin:0}
body.presenting .meta code{background:none;border:0;padding:0;font-family:var(--mono)}
body.presenting .counts{display:flex;flex-wrap:wrap;gap:.6rem clamp(1.4rem,4vw,3.5rem);max-width:none;margin:0}
body.presenting .count{display:flex;flex-direction:column}
body.presenting .count-sep{display:none}
body.presenting .count-value{font-size:var(--slide-number);font-weight:700;line-height:1;
  letter-spacing:-.03em;font-variant-numeric:tabular-nums;color:var(--fg)}
body.presenting .count-label{font-size:var(--slide-eyebrow);color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
body.presenting .count-decision .count-value{color:var(--decision-fg)}
body.presenting .sources{display:none}
body.presenting .slide .sources-footer{display:block;margin:0;max-width:none;
  font-size:var(--slide-eyebrow);color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
body.presenting .decisions{background:none;border:0;border-radius:0}
body.presenting[data-presenting-kind="decision"] main{background:var(--decision-bg)}
body.presenting[data-presenting-kind="decision"] .presentation-rail{background:var(--decision-bg)}
body.presenting[data-presenting-kind="decision"] .slide .meta{color:var(--decision-fg)}
body.presenting details.item.slide{display:flex;flex-direction:column;gap:var(--slide-gap);
  position:relative;overflow:hidden;background:none;border:0;padding:0}
body.presenting .slide[data-slide-ref]::after{content:attr(data-slide-ref);position:fixed;left:0;
  bottom:calc(var(--pres-bar) - 1.6rem);font-family:var(--mono);font-weight:700;font-size:var(--slide-ghost);
  line-height:.8;letter-spacing:-.06em;color:var(--ghost);pointer-events:none;user-select:none;z-index:0}
body.presenting.overview-open .slide[data-slide-ref]::after{content:none}
body.presenting .item>summary{display:flex;flex-direction:column;align-items:flex-start;gap:var(--slide-gap);
  position:relative;z-index:1;cursor:default}
body.presenting .item>summary::before{content:none}
body.presenting .item>summary>code{order:0;background:none;border:0;padding:0;font-family:var(--mono);
  font-size:var(--slide-eyebrow);letter-spacing:.1em;color:var(--muted)}
body.presenting .item>summary .badges{order:1;display:flex;flex-wrap:wrap;gap:.4rem}
body.presenting .badge,body.presenting .chip{margin-left:0;font-size:var(--slide-eyebrow);padding:.15rem .75rem}
body.presenting .axes .badge{margin-left:.6rem}
body.presenting .item-title{order:2}
body.presenting .outcome{order:3;font-size:var(--slide-lede);color:var(--muted);margin:0;max-width:var(--body-measure)}
body.presenting .item-body{position:relative;z-index:1;border-top:0;margin:0;padding:0;
  display:flex;flex-direction:column;gap:var(--slide-gap)}
body.presenting .item-body h4,body.presenting .slide>h3{font-size:var(--slide-eyebrow);margin:0;
  letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
body.presenting .item-body ul{list-style:none;padding-left:0}
body.presenting .item-body li{display:flex;gap:.6em;align-items:baseline}
body.presenting .item-body li::before{content:"";flex:none;width:.7em;height:.7em;border-radius:3px;
  border:2px solid var(--accent);transform:translateY(.08em)}
body.presenting .group,body.presenting .sub{border:0;padding:0}
body.presenting .group>summary,body.presenting .sub>summary{list-style:none;cursor:default}
body.presenting .group>summary::-webkit-details-marker,body.presenting .sub>summary::-webkit-details-marker{display:none}
body.presenting .sub>summary{font-size:var(--slide-eyebrow);text-transform:uppercase;letter-spacing:.12em;color:var(--muted)}
body.presenting .group{column-gap:clamp(1.5rem,4vw,3rem)}
body.presenting .group>summary{column-span:all;margin-bottom:var(--slide-gap)}
body.presenting .sub{break-inside:avoid-column;margin-bottom:var(--slide-gap)}
body.presenting .slide-dense{--slide-title:clamp(1.5rem,2.4vw + .8vh,2.8rem);
  --slide-lede:clamp(1rem,.9vw + .5vh,1.4rem);--slide-body:clamp(1rem,.75vw + .45vh,1.3rem);
  --slide-ghost:clamp(4.5rem,11vw,10rem)}
@media (max-width:640px){
  body.presenting{--pres-bar:6.4rem}
  body.presenting .topbar-title{display:none}
  body.presenting .presentation-bar{left:.5rem;right:.5rem;transform:none;flex-wrap:wrap;justify-content:center;border-radius:14px}
  body.presenting .presentation-bar button{white-space:nowrap}
}
@media (min-width:1100px){
  body.presenting details.item.slide{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);
    gap:clamp(1.5rem,4vw,4rem);align-items:start;--slide-title:clamp(1.8rem,2.6vw + .9vh,3.5rem)}
  body.presenting details.item.slide-dense{grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr)}
  body.presenting .group{columns:3}
}
@media (prefers-reduced-motion:no-preference){
  body.presenting .slide.is-entering-forward>*{animation:slide-enter-forward .26s cubic-bezier(.2,.7,.2,1)}
  body.presenting .slide.is-entering-backward>*{animation:slide-enter-backward .26s cubic-bezier(.2,.7,.2,1)}
  body.presenting .slide.is-entering-forward::after,
  body.presenting .slide.is-entering-backward::after{animation:slide-ghost-enter .26s ease-out}
  @keyframes slide-ghost-enter{from{opacity:0}to{opacity:1}}
  @keyframes slide-enter-forward{from{opacity:0;transform:translateX(2.5rem)}to{opacity:1;transform:none}}
  @keyframes slide-enter-backward{from{opacity:0;transform:translateX(-2.5rem)}to{opacity:1;transform:none}}
}
body.compact main{font-size:14px;line-height:1.45}
body.compact .block{margin-bottom:1.4rem}
body.compact .item{padding:.35rem .7rem}
@media (max-width:900px){
  .layout{grid-template-columns:minmax(0,1fr);gap:1.5rem}
  aside{position:static;max-height:none}
}
@media (max-width:480px){
  .layout{padding:1.25rem .9rem 4rem}
  .topbar{padding:.5rem .9rem}
  .topbar-title{max-width:100%}
  h1{font-size:1.5rem}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *{transition:none!important;animation:none!important}
}
@media print{
  :root,:root:not([data-theme="light"]),:root[data-theme="dark"]{
    __LIGHT_TOKENS__
  }
  .topbar,aside,.presentation-bar,.presentation-rail,.presentation-grid,.agent-block,.agent-note{display:none!important}
  body{background:var(--surface)}
  .layout{display:block;max-width:none;padding:0}
  .item,.block{break-inside:avoid;border-color:var(--print-border)}
}
"""

STYLE_CSS = STYLE_TEMPLATE.replace(LIGHT_TOKENS_PLACEHOLDER, LIGHT_TOKENS).replace(
    DARK_TOKENS_PLACEHOLDER, DARK_TOKENS
)

THEME_BOOTSTRAP_TEMPLATE = """
(function(){
  try {
    var stored = window.localStorage.getItem("__THEME_KEY__");
    if (stored === "__DARK_VALUE__" || stored === "__LIGHT_VALUE__") {
      document.documentElement.setAttribute("__THEME_ATTRIBUTE__", stored);
    }
  } catch (error) { return; }
})();
"""

THEME_KEY_PLACEHOLDER = "__THEME_KEY__"
THEME_ATTRIBUTE_PLACEHOLDER = "__THEME_ATTRIBUTE__"
DARK_VALUE_PLACEHOLDER = "__DARK_VALUE__"
LIGHT_VALUE_PLACEHOLDER = "__LIGHT_VALUE__"

THEME_BOOTSTRAP_JS = (
    THEME_BOOTSTRAP_TEMPLATE.replace(THEME_KEY_PLACEHOLDER, THEME_STORAGE_KEY)
    .replace(THEME_ATTRIBUTE_PLACEHOLDER, THEME_ATTRIBUTE)
    .replace(DARK_VALUE_PLACEHOLDER, DARK_THEME_VALUE)
    .replace(LIGHT_VALUE_PLACEHOLDER, LIGHT_THEME_VALUE)
)

SCRIPT_JS = """
(function(){
  var labels = PRD_CONFIG.labels;
  var INTERACTIVE_TAGS = ["INPUT", "TEXTAREA", "SELECT"];
  var COUNTER_SEPARATOR = " / ";
  var LABEL_SEPARATOR = " · ";
  var COMPACT_VALUE = "compact";
  var COMFORT_VALUE = "comfort";
  var VISIBLE_VALUE = "visible";
  var HIDDEN_VALUE = "hidden";
  var PRESENTATION_KEY = "d";
  var OVERVIEW_KEY = "g";
  var DARK_SCHEME_QUERY = "(prefers-color-scheme: dark)";
  var SEGMENT_CLASS = "rail-segment";
  var TILE_CLASS = "grid-tile";
  var TILE_REFERENCE_CLASS = "grid-tile-ref";
  var OVERVIEW_CLASS = "overview-open";
  var PAST_CLASS = "is-past";
  var CURRENT_CLASS = "is-current";
  var FORWARD_CLASS = "is-entering-forward";
  var BACKWARD_CLASS = "is-entering-backward";
  var CHANGES_ONLY_CLASS = "changes-only";
  var NOT_FOUND = -1;
  var HASH_PREFIX_LENGTH = 1;
  var FORWARD_STEP = 1;
  var BACKWARD_STEP = -1;
  var densityButton = document.getElementById("density");
  var changesButton = document.getElementById(PRD_CONFIG.changesButtonId);
  var pageHead = document.getElementById(PRD_CONFIG.pageHeadId);
  var agentNavEntry = document.getElementById(PRD_CONFIG.agentNavId);
  var themeButton = document.getElementById("theme");
  var agentButton = document.getElementById("agent-toggle");
  var expandButton = document.getElementById("expand-all");
  var presentationButton = document.getElementById("presentation");
  var presentationBar = document.getElementById("presentation-bar");
  var presentationCounter = document.getElementById("presentation-counter");
  var previousButton = document.getElementById("presentation-previous");
  var nextButton = document.getElementById("presentation-next");
  var overviewButton = document.getElementById("presentation-overview");
  var presentationRail = document.getElementById("presentation-rail");
  var presentationGrid = document.getElementById("presentation-grid");
  var agentSection = document.getElementById(PRD_CONFIG.agentSectionId);
  var agentNote = document.getElementById(PRD_CONFIG.agentNoteId);
  var stage = document.querySelector("main");
  var slides = sortedSlides();
  var groups = Array.prototype.slice.call(document.querySelectorAll(".pres-group"));
  var allDetails = Array.prototype.slice.call(document.querySelectorAll("details"));
  var agentVisible = false;
  var expanded = false;
  var presenting = false;
  var overviewVisible = false;
  var changesOnly = false;
  var slideIndex = 0;
  var slideDirection = FORWARD_STEP;
  var printState = null;

  function slidePosition(slide){
    return PRD_CONFIG.slideOrder.indexOf(slide.getAttribute(PRD_CONFIG.keyAttribute));
  }

  function sortedSlides(){
    var found = Array.prototype.slice.call(document.querySelectorAll(".slide"));
    return found.sort(function(first, second){ return slidePosition(first) - slidePosition(second); });
  }

  function readStored(key){
    try { return window.localStorage.getItem(key); } catch (error) { return null; }
  }

  function writeStored(key, value){
    try { window.localStorage.setItem(key, value); } catch (error) { return; }
  }

  function prefersDarkScheme(){
    if (!window.matchMedia) { return false; }
    return window.matchMedia(DARK_SCHEME_QUERY).matches;
  }

  function storedTheme(){
    return document.documentElement.getAttribute(PRD_CONFIG.themeAttribute);
  }

  function currentTheme(){
    var theme = storedTheme();
    if (theme === PRD_CONFIG.darkTheme || theme === PRD_CONFIG.lightTheme) { return theme; }
    if (prefersDarkScheme()) { return PRD_CONFIG.darkTheme; }
    return PRD_CONFIG.lightTheme;
  }

  function refreshThemeButton(){
    var dark = currentTheme() === PRD_CONFIG.darkTheme;
    themeButton.textContent = dark ? labels.lightTheme : labels.darkTheme;
    themeButton.setAttribute("aria-pressed", dark ? "true" : "false");
  }

  function applyTheme(theme){
    document.documentElement.setAttribute(PRD_CONFIG.themeAttribute, theme);
    writeStored(PRD_CONFIG.themeKey, theme);
    refreshThemeButton();
  }

  function watchSchemeChanges(){
    if (!window.matchMedia) { return; }
    var query = window.matchMedia(DARK_SCHEME_QUERY);
    if (!query.addEventListener) { return; }
    query.addEventListener("change", function(){
      if (storedTheme()) { return; }
      refreshThemeButton();
    });
  }

  function applyDensity(compact){
    document.body.classList.toggle(COMPACT_VALUE, compact);
    densityButton.textContent = compact ? labels.comfort : labels.compact;
    densityButton.setAttribute("aria-pressed", compact ? "true" : "false");
  }

  function applyAgentVisibility(){
    if (agentSection) { agentSection.hidden = presenting || !agentVisible; }
    if (agentNote) { agentNote.hidden = presenting || agentVisible; }
    if (agentNavEntry) { agentNavEntry.hidden = !agentVisible; }
    agentButton.textContent = agentVisible ? labels.hideAgent : labels.showAgent;
    agentButton.setAttribute("aria-pressed", agentVisible ? "true" : "false");
  }

  function applyExpansion(){
    allDetails.forEach(function(element){ element.open = expanded; });
    expandButton.textContent = expanded ? labels.collapseAll : labels.expandAll;
    expandButton.setAttribute("aria-pressed", expanded ? "true" : "false");
  }

  function applyChangesFilter(){
    if (!changesButton) { return; }
    document.body.classList.toggle(CHANGES_ONLY_CLASS, changesOnly);
    changesButton.textContent = changesOnly ? labels.showAll : labels.changesOnly;
    changesButton.setAttribute("aria-pressed", changesOnly ? "true" : "false");
  }

  function slideIndexForKey(key){
    for (var index = 0; index < slides.length; index += 1) {
      if (slides[index].getAttribute(PRD_CONFIG.keyAttribute) === key) { return index; }
    }
    return NOT_FOUND;
  }

  function revealTarget(identifier){
    if (!identifier) { return; }
    var target = document.getElementById(identifier);
    if (target && target.tagName === "DETAILS") { target.open = true; }
  }

  function revealHash(){
    revealTarget(decodeURIComponent(window.location.hash.slice(HASH_PREFIX_LENGTH)));
  }

  function slideKind(slide){
    return slide.getAttribute(PRD_CONFIG.kindAttribute) || "";
  }

  function slideTitle(slide){
    return slide.getAttribute(PRD_CONFIG.titleAttribute) || "";
  }

  function slideReference(slide){
    return slide.getAttribute(PRD_CONFIG.referenceAttribute) || "";
  }

  function kindLabel(kind){
    var key = PRD_CONFIG.kindLabelKeys[kind];
    if (!key) { return ""; }
    return labels[key];
  }

  function buildSegment(slide, index){
    var segment = document.createElement("button");
    segment.type = "button";
    segment.className = SEGMENT_CLASS;
    segment.setAttribute(PRD_CONFIG.kindAttribute, slideKind(slide));
    segment.setAttribute("aria-label", kindLabel(slideKind(slide)) + LABEL_SEPARATOR + slideTitle(slide));
    segment.addEventListener("click", function(){ goToSlide(index); });
    return segment;
  }

  function buildTile(slide, index){
    var tile = document.createElement("button");
    tile.type = "button";
    tile.className = TILE_CLASS;
    tile.setAttribute(PRD_CONFIG.kindAttribute, slideKind(slide));
    var reference = document.createElement("span");
    reference.className = TILE_REFERENCE_CLASS;
    reference.textContent = slideReference(slide) || kindLabel(slideKind(slide));
    var title = document.createElement("span");
    title.textContent = slideTitle(slide);
    tile.appendChild(reference);
    tile.appendChild(title);
    tile.addEventListener("click", function(){
      setOverview(false);
      goToSlide(index);
    });
    return tile;
  }

  function buildNavigation(){
    slides.forEach(function(slide, index){
      presentationRail.appendChild(buildSegment(slide, index));
      presentationGrid.appendChild(buildTile(slide, index));
    });
  }

  function refreshNavigation(){
    Array.prototype.forEach.call(presentationRail.children, function(segment, index){
      segment.classList.toggle(PAST_CLASS, index < slideIndex);
      segment.classList.toggle(CURRENT_CLASS, index === slideIndex);
    });
    Array.prototype.forEach.call(presentationGrid.children, function(tile, index){
      tile.classList.toggle(CURRENT_CLASS, index === slideIndex);
    });
  }

  function animateSlide(slide){
    slide.classList.remove(FORWARD_CLASS);
    slide.classList.remove(BACKWARD_CLASS);
    void slide.offsetWidth;
    slide.classList.add(slideDirection === BACKWARD_STEP ? BACKWARD_CLASS : FORWARD_CLASS);
  }

  function openSlideDetails(slide){
    if (slide.tagName === "DETAILS") { slide.open = true; }
    Array.prototype.forEach.call(slide.querySelectorAll("details"), function(element){
      element.open = true;
    });
  }

  function setOverview(visible){
    overviewVisible = visible && presenting;
    presentationGrid.hidden = !overviewVisible;
    document.body.classList.toggle(OVERVIEW_CLASS, overviewVisible);
    overviewButton.setAttribute("aria-pressed", overviewVisible ? "true" : "false");
  }

  function applyPresentation(){
    document.body.classList.toggle("presenting", presenting);
    presentationBar.hidden = !presenting;
    presentationRail.hidden = !presenting;
    presentationButton.textContent = presenting ? labels.exitPresentation : labels.presentation;
    presentationButton.setAttribute("aria-pressed", presenting ? "true" : "false");
    if (!presenting) {
      setOverview(false);
      document.body.removeAttribute(PRD_CONFIG.presentingKindAttribute);
      slides.forEach(function(slide){
        slide.hidden = false;
        slide.classList.remove(FORWARD_CLASS);
        slide.classList.remove(BACKWARD_CLASS);
      });
      groups.forEach(function(group){ group.hidden = false; });
      if (pageHead) { pageHead.hidden = false; }
      applyAgentVisibility();
      return;
    }
    var current = slides[slideIndex];
    slides.forEach(function(slide, index){ slide.hidden = index !== slideIndex; });
    groups.forEach(function(group){ group.hidden = !group.contains(current); });
    if (pageHead) { pageHead.hidden = !current || current.id !== PRD_CONFIG.briefId; }
    if (current) {
      openSlideDetails(current);
      animateSlide(current);
      document.body.setAttribute(PRD_CONFIG.presentingKindAttribute, slideKind(current));
      if (stage) { stage.scrollTop = 0; }
    }
    presentationCounter.textContent = (slideIndex + 1) + COUNTER_SEPARATOR + slides.length;
    refreshNavigation();
    applyAgentVisibility();
    window.scrollTo(0, 0);
  }

  function goToSlide(index){
    if (!presenting || slides.length === 0) { return; }
    slideDirection = index < slideIndex ? BACKWARD_STEP : FORWARD_STEP;
    slideIndex = Math.min(slides.length - 1, Math.max(0, index));
    applyPresentation();
  }

  function moveSlide(offset){
    if (!presenting || slides.length === 0) { return; }
    goToSlide(slideIndex + offset);
  }

  buildNavigation();
  applyDensity(readStored(PRD_CONFIG.densityKey) === COMPACT_VALUE);
  agentVisible = readStored(PRD_CONFIG.agentKey) === VISIBLE_VALUE;
  applyAgentVisibility();
  applyExpansion();
  applyChangesFilter();
  refreshThemeButton();
  watchSchemeChanges();
  revealHash();
  window.addEventListener("hashchange", revealHash);

  if (changesButton) {
    changesButton.addEventListener("click", function(){
      changesOnly = !changesOnly;
      applyChangesFilter();
    });
  }

  document.addEventListener("click", function(event){
    var target = event.target;
    if (!target || !target.closest) { return; }
    var link = target.closest("[" + PRD_CONFIG.slideTargetAttribute + "]");
    if (link && presenting) {
      event.preventDefault();
      var index = slideIndexForKey(link.getAttribute(PRD_CONFIG.slideTargetAttribute));
      if (index !== NOT_FOUND) { goToSlide(index); }
      return;
    }
    if (link) {
      revealTarget(link.hash.slice(HASH_PREFIX_LENGTH));
      return;
    }
    if (presenting && target.closest("summary")) { event.preventDefault(); }
  });

  themeButton.addEventListener("click", function(){
    if (currentTheme() === PRD_CONFIG.darkTheme) {
      applyTheme(PRD_CONFIG.lightTheme);
      return;
    }
    applyTheme(PRD_CONFIG.darkTheme);
  });

  densityButton.addEventListener("click", function(){
    var compact = !document.body.classList.contains(COMPACT_VALUE);
    writeStored(PRD_CONFIG.densityKey, compact ? COMPACT_VALUE : COMFORT_VALUE);
    applyDensity(compact);
  });

  agentButton.addEventListener("click", function(){
    agentVisible = !agentVisible;
    writeStored(PRD_CONFIG.agentKey, agentVisible ? VISIBLE_VALUE : HIDDEN_VALUE);
    applyAgentVisibility();
  });

  expandButton.addEventListener("click", function(){
    expanded = !expanded;
    applyExpansion();
  });

  presentationButton.addEventListener("click", function(){
    presenting = !presenting;
    slideIndex = 0;
    applyPresentation();
    presentationButton.blur();
  });

  previousButton.addEventListener("click", function(){ moveSlide(BACKWARD_STEP); previousButton.blur(); });
  nextButton.addEventListener("click", function(){ moveSlide(FORWARD_STEP); nextButton.blur(); });
  overviewButton.addEventListener("click", function(){ setOverview(!overviewVisible); });

  document.addEventListener("keydown", function(event){
    var target = event.target;
    if (target && INTERACTIVE_TAGS.indexOf(target.tagName) !== -1) { return; }
    if (target && target.isContentEditable) { return; }
    if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) { return; }
    if (event.key === PRESENTATION_KEY) {
      presenting = !presenting;
      slideIndex = 0;
      applyPresentation();
      return;
    }
    if (event.key === OVERVIEW_KEY && presenting) {
      setOverview(!overviewVisible);
      return;
    }
    if (event.key === "Escape" && overviewVisible) {
      setOverview(false);
      return;
    }
    if (event.key === "Escape" && presenting) {
      presenting = false;
      applyPresentation();
      return;
    }
    if (event.key === "ArrowRight") { moveSlide(FORWARD_STEP); }
    if (event.key === "ArrowLeft") { moveSlide(BACKWARD_STEP); }
  });

  window.addEventListener("beforeprint", function(){
    if (presenting) { presenting = false; applyPresentation(); }
    printState = allDetails.map(function(element){ return element.open; });
    allDetails.forEach(function(element){ element.open = true; });
  });

  window.addEventListener("afterprint", function(){
    if (!printState) { return; }
    allDetails.forEach(function(element, index){ element.open = printState[index]; });
    printState = null;
  });
})();
"""


def escape(value):
    return html.escape(value, quote=True)


def labels_for(document):
    return LABELS[document["locale"]]


def count_words(text):
    return len(text.split())


def list_html(items, empty_label, list_tag="ul"):
    if not items:
        return f'<p class="empty">{escape(empty_label)}</p>'
    entries = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f"<{list_tag}>{entries}</{list_tag}>"


def slide_attributes(kind, title, key, reference=""):
    attributes = (
        f' {SLIDE_KIND_ATTRIBUTE}="{escape(kind)}" {SLIDE_TITLE_ATTRIBUTE}="{escape(title)}"'
        f' {SLIDE_KEY_ATTRIBUTE}="{escape(key)}"'
    )
    if reference:
        attributes += f' {SLIDE_REF_ATTRIBUTE}="{escape(reference)}"'
    return attributes


def slide_key(prefix, identifier):
    return f"{prefix}{identifier}"


def axis_items(items, axis_id):
    return [item for item in items if item["axis"] == axis_id]


def requirement_priority_groups(requirements):
    must_items = [item for item in requirements if item["priority"] == MUST_PRIORITY]
    other_items = [item for item in requirements if item["priority"] != MUST_PRIORITY]
    return must_items, other_items


def ordered_requirements(requirements):
    must_items, other_items = requirement_priority_groups(requirements)
    return must_items + other_items


def slide_order(document):
    keys = [DECISIONS_ID, BRIEF_ID, AXES_ID]
    for axis in document["axes"]:
        keys.append(slide_key(AXIS_KEY_PREFIX, axis["id"]))
        axis_requirements = ordered_requirements(axis_items(document["requirements"], axis["id"]))
        keys.extend(slide_key(REQUIREMENT_KEY_PREFIX, item["id"]) for item in axis_requirements)
        keys.extend(slide_key(TASK_KEY_PREFIX, item["id"]) for item in axis_items(document["tasks"], axis["id"]))
    keys.extend([OUT_OF_SCOPE_ID, SECONDARY_ID, IMPACT_ID])
    return keys


def slide_classes(classes, item_count):
    if item_count > DENSE_SLIDE_ITEM_THRESHOLD:
        return f"{classes} {SLIDE_DENSE_CLASS}"
    return classes


def block_html(identifier, title, content, classes, extra_attributes=""):
    heading_id = f"{identifier}-title"
    return (
        f'<section id="{identifier}" class="{classes}" aria-labelledby="{heading_id}"{extra_attributes}>'
        f'<h2 id="{heading_id}">{escape(title)}</h2>{content}</section>'
    )


def uses_default_source_priority(document):
    return document["preDraft"]["sourcePriority"] == DEFAULT_SOURCE_PRIORITY


def reading_minutes(word_count):
    minutes = -(-word_count // WORDS_PER_MINUTE)
    return max(MINIMUM_READING_MINUTES, minutes)


def visible_words(document):
    texts = [document["title"], document["summary"]]
    for field in ("openQuestions", "goals", "outOfScope") + SECONDARY_FIELDS:
        texts.extend(document[field])
    texts.extend(document["preDraft"]["sharedSurfaces"])
    for axis in document["axes"]:
        texts.append(axis["title"])
        texts.append(axis["summary"])
    if not uses_default_source_priority(document):
        texts.extend(document["preDraft"]["sourcePriority"])
    for requirement in document["requirements"]:
        texts.append(requirement["title"])
        texts.append(requirement["description"])
        texts.extend(requirement["acceptance"])
    for task in document["tasks"]:
        texts.append(task["title"])
        texts.append(task["expectedOutcome"])
        texts.append(task["startCondition"])
        texts.extend(task["acceptance"])
    return sum(count_words(text) for text in texts)


def agent_entry_count(document):
    total = len(document["preDraft"]["reuse"])
    total += sum(len(task["boundaries"]) for task in document["tasks"])
    if uses_default_source_priority(document):
        total += len(document["preDraft"]["sourcePriority"])
    return total


def plural_form(labels, key, count):
    forms = labels[key]
    if count == SINGULAR_COUNT:
        return forms["one"]
    return forms["many"]


def count_html(labels, key, count, extra_class=""):
    form = plural_form(labels, key, count)
    prefix, _, suffix = form.partition(COUNT_PLACEHOLDER)
    classes = f"count {extra_class}".strip()
    return (
        f'<span class="{classes}"><span class="count-value">{escape(prefix)}{count}</span>'
        f'<span class="count-label">{escape(suffix)}</span></span>'
    )


def count_strip_html(document, labels):
    parts = [
        count_html(labels, "countRequirements", len(document["requirements"])),
        count_html(labels, "countTasks", len(document["tasks"])),
        count_html(labels, "countQuestions", len(document["openQuestions"]), COUNT_DECISION_CLASS),
        count_html(labels, "countReadingTime", reading_minutes(visible_words(document))),
    ]
    separator = f'<span class="count-sep">{escape(COUNT_SEPARATOR)}</span>'
    return f'<p class="counts">{separator.join(parts)}</p>'


def source_entry_html(source):
    title = escape(source["title"])
    reference = escape(source["ref"])
    if source["ref"].startswith(LINK_PREFIXES):
        return f'<li><a href="{reference}" target="_blank" rel="noopener">{title}</a></li>'
    return f"<li>{title} <code>{reference}</code></li>"


def sources_html(sources, labels):
    if not sources:
        return ""
    entries = "".join(source_entry_html(source) for source in sources)
    titles = SOURCE_SEPARATOR.join(source["title"] for source in sources)
    return (
        f'<div class="sources"><h3>{escape(labels["sources"])}</h3><ul>{entries}</ul></div>'
        f'<p class="sources-footer">{escape(labels["sources"])}'
        f"{escape(COUNT_SEPARATOR)}{escape(titles)}</p>"
    )


def page_head_html(document, labels):
    return (
        f'<header id="{PAGE_HEAD_ID}" class="page-head">'
        f'<p class="meta"><code>{escape(document["id"])}</code>{escape(COUNT_SEPARATOR)}'
        f'{escape(labels["revision"])} {escape(document["revision"])}</p>'
        f'<h1>{escape(document["title"])}</h1></header>'
    )


def brief_html(document, labels):
    content = (
        f'<p class="summary">{escape(document["summary"])}</p>'
        f'<h3>{escape(labels["goals"])}</h3>'
        f'{list_html(document["goals"], labels["empty"])}'
        f"{count_strip_html(document, labels)}"
        f'{sources_html(document["sources"], labels)}'
    )
    return block_html(
        BRIEF_ID,
        labels["need"],
        content,
        slide_classes("block slide need", len(document["goals"])),
        extra_attributes=slide_attributes(KIND_CONTEXT, labels["need"], BRIEF_ID),
    )


def change_status(changes, field, key):
    if changes is None:
        return None
    return changes[field].get(key)


def change_badge(status, labels):
    label_key = CHANGE_LABEL_KEYS.get(status)
    if label_key is None:
        return ""
    return f'<span class="badge badge-{status}">{escape(labels[label_key])}</span>'


def unchanged_attribute(statuses):
    if statuses and all(status == CHANGE_SAME for status in statuses):
        return f' {CHANGE_ATTRIBUTE}="{CHANGE_SAME}"'
    return ""


def axis_statuses(document, axis, changes):
    axis_id = axis["id"]
    statuses = [change_status(changes, "axes", axis_id)]
    statuses.extend(change_status(changes, "requirements", item["id"]) for item in axis_items(document["requirements"], axis_id))
    statuses.extend(change_status(changes, "tasks", item["id"]) for item in axis_items(document["tasks"], axis_id))
    return statuses


def axis_anchor(axis_id):
    return f"{AXIS_ANCHOR_PREFIX}{axis_id}"


def slide_link_attributes(anchor, key):
    return f'href="#{escape(anchor)}" {SLIDE_TARGET_ATTRIBUTE}="{escape(key)}"'


def axes_html(document, labels, changes):
    entries = "".join(
        f'<li{unchanged_attribute(axis_statuses(document, axis, changes))}>'
        f'<a {slide_link_attributes(axis_anchor(axis["id"]), slide_key(AXIS_KEY_PREFIX, axis["id"]))}>'
        f'<code>{escape(axis["id"])}</code> '
        f'<span class="axis-name">{escape(axis["title"])}</span></a>'
        f'{change_badge(change_status(changes, "axes", axis["id"]), labels)}'
        f'<span class="outcome">{escape(axis["summary"])}</span></li>'
        for axis in document["axes"]
    )
    return block_html(
        AXES_ID,
        labels["axes"],
        f"<ul>{entries}</ul>",
        slide_classes("block slide axes", len(document["axes"])),
        extra_attributes=slide_attributes(KIND_AXIS, labels["axes"], AXES_ID),
    )


def axis_head_html(axis, labels, changes):
    heading_id = f"{axis_anchor(axis['id'])}-title"
    attributes = slide_attributes(KIND_AXIS, axis["title"], slide_key(AXIS_KEY_PREFIX, axis["id"]), axis["id"])
    return (
        f'<div class="slide axis-head"{attributes}>'
        f'<h2 id="{heading_id}">{escape(axis["id"])}{escape(COUNT_SEPARATOR)}{escape(axis["title"])}'
        f'{change_badge(change_status(changes, "axes", axis["id"]), labels)}</h2>'
        f'<p class="summary">{escape(axis["summary"])}</p></div>'
    )


def requirement_html(requirement, labels, status):
    priority = escape(requirement["priority"])
    badges = (
        '<span class="badges">'
        f'<span class="badge badge-{priority}">{priority}</span>'
        f'<span class="badge">{escape(requirement["status"])}</span>'
        f'<span class="badge">{escape(requirement["kind"])}</span>'
        f"{change_badge(status, labels)}"
        "</span>"
    )
    classes = slide_classes("item slide", len(requirement["acceptance"]))
    attributes = slide_attributes(
        KIND_REQUIREMENT,
        requirement["title"],
        slide_key(REQUIREMENT_KEY_PREFIX, requirement["id"]),
        requirement["id"],
    )
    return (
        f'<details id="{REQUIREMENT_ANCHOR_PREFIX}{escape(requirement["id"])}" class="{classes}"'
        f"{attributes}{unchanged_attribute([status])}>"
        f'<summary><code>{escape(requirement["axis"])}{escape(COUNT_SEPARATOR)}'
        f'{escape(requirement["id"])}</code> '
        f'<span class="item-title">{escape(requirement["title"])}</span>{badges}</summary>'
        f'<div class="item-body"><p>{escape(requirement["description"])}</p>'
        f'<h4>{escape(labels["acceptance"])}</h4>'
        f'{list_html(requirement["acceptance"], labels["empty"])}</div>'
        "</details>"
    )


def requirements_part_html(requirements, labels, changes):
    parts = [f'<h3>{escape(labels["requirements"])}</h3>']
    statuses = []
    must_items, other_items = requirement_priority_groups(requirements)
    for heading, group in ((labels["mustGroup"], must_items), (labels["otherGroup"], other_items)):
        if not group:
            continue
        group_statuses = [change_status(changes, "requirements", item["id"]) for item in group]
        statuses.extend(group_statuses)
        parts.append(f'<p class="group-label"{unchanged_attribute(group_statuses)}>{escape(heading)}</p>')
        parts.extend(requirement_html(item, labels, status) for item, status in zip(group, group_statuses))
    return f'<div class="axis-part pres-group"{unchanged_attribute(statuses)}>{"".join(parts)}</div>'


def dependency_link_html(dependency, task_axis, task_axes, labels):
    dependency_axis = task_axes.get(dependency)
    text = dependency
    classes = "dep-link"
    hint = ""
    if dependency_axis is not None and dependency_axis != task_axis:
        text = f"{dependency}{COUNT_SEPARATOR}{dependency_axis}"
        classes = f"{classes} dep-cross"
        hint = f' title="{escape(labels["crossAxisDependency"].format(axis=dependency_axis))}"'
    attributes = slide_link_attributes(f"{TASK_ANCHOR_PREFIX}{dependency}", slide_key(TASK_KEY_PREFIX, dependency))
    return f'<a class="{classes}" {attributes}{hint}>{escape(text)}</a>'


def dependency_chip_html(task, task_axes, labels):
    if not task["dependsOn"]:
        return ""
    prefix, _, suffix = labels["afterChip"].partition(DEPENDENCIES_PLACEHOLDER)
    links = escape(DEPENDENCY_SEPARATOR).join(
        dependency_link_html(dependency, task["axis"], task_axes, labels) for dependency in task["dependsOn"]
    )
    return f'<span class="chip">{escape(prefix)}{links}{escape(suffix)}</span>'


def task_html(task, labels, task_axes, status):
    badges = f"{dependency_chip_html(task, task_axes, labels)}{change_badge(status, labels)}"
    if badges:
        badges = f'<span class="badges">{badges}</span>'
    classes = slide_classes("item slide", len(task["acceptance"]))
    attributes = slide_attributes(
        KIND_TASK, task["title"], slide_key(TASK_KEY_PREFIX, task["id"]), task["id"]
    )
    return (
        f'<details id="{TASK_ANCHOR_PREFIX}{escape(task["id"])}" class="{classes}"'
        f"{attributes}{unchanged_attribute([status])}>"
        f'<summary><code>{escape(task["axis"])}{escape(COUNT_SEPARATOR)}'
        f'{escape(task["id"])}</code> '
        f'<span class="item-title">{escape(task["title"])}</span>{badges}'
        f'<span class="outcome">{escape(task["expectedOutcome"])}</span></summary>'
        f'<div class="item-body"><h4>{escape(labels["startCondition"])}</h4>'
        f'<p>{escape(task["startCondition"])}</p>'
        f'<h4>{escape(labels["acceptance"])}</h4>'
        f'{list_html(task["acceptance"], labels["empty"])}</div>'
        "</details>"
    )


def tasks_part_html(tasks, labels, changes, task_axes):
    if not tasks:
        return ""
    statuses = [change_status(changes, "tasks", task["id"]) for task in tasks]
    entries = "".join(task_html(task, labels, task_axes, status) for task, status in zip(tasks, statuses))
    return (
        f'<div class="axis-part pres-group"{unchanged_attribute(statuses)}>'
        f'<h3>{escape(labels["tasks"])}</h3>{entries}</div>'
    )


def axis_section_html(document, axis, labels, changes):
    anchor = axis_anchor(axis["id"])
    task_axes = {task["id"]: task["axis"] for task in document["tasks"]}
    requirements = axis_items(document["requirements"], axis["id"])
    tasks = axis_items(document["tasks"], axis["id"])
    return (
        f'<section id="{anchor}" class="axis-section pres-group" aria-labelledby="{anchor}-title"'
        f"{unchanged_attribute(axis_statuses(document, axis, changes))}>"
        f"{axis_head_html(axis, labels, changes)}"
        f"{requirements_part_html(requirements, labels, changes)}"
        f"{tasks_part_html(tasks, labels, changes, task_axes)}"
        "</section>"
    )


def secondary_html(document, labels):
    entries = "".join(
        f'<details class="sub"><summary>{escape(labels[field])}</summary>'
        f'{list_html(document[field], labels["empty"])}</details>'
        for field in SECONDARY_FIELDS
    )
    heading = f'<h2 id="{SECONDARY_ID}-title">{escape(labels["secondary"])}</h2>'
    item_count = sum(len(document[field]) for field in SECONDARY_FIELDS)
    classes = slide_classes("block slide", item_count)
    attributes = slide_attributes(KIND_CONTEXT, labels["secondary"], SECONDARY_ID)
    return (
        f'<section id="{SECONDARY_ID}" class="{classes}" aria-labelledby="{SECONDARY_ID}-title"{attributes}>'
        f'<details class="group"><summary>{heading}</summary>{entries}</details>'
        "</section>"
    )


def source_priority_html(pre_draft, labels):
    return (
        f'<h3>{escape(labels["sourcePriority"])}</h3>'
        f'{list_html(pre_draft["sourcePriority"], labels["empty"])}'
    )


def agent_context_html(document, labels):
    pre_draft = document["preDraft"]
    parts = [f'<h3>{escape(labels["reuse"])}</h3>', list_html(pre_draft["reuse"], labels["empty"])]
    if uses_default_source_priority(document):
        parts.append(source_priority_html(pre_draft, labels))
    for task in document["tasks"]:
        parts.append(f"<h3>{escape(task['id'])}{escape(COUNT_SEPARATOR)}{escape(task['title'])}</h3>")
        parts.append(list_html(task["boundaries"], labels["empty"]))
    return block_html(
        AGENT_CONTEXT_ID,
        labels["agentContext"],
        "".join(parts),
        "block agent-block",
        extra_attributes=" hidden",
    )


def impact_html(document, labels):
    pre_draft = document["preDraft"]
    parts = [list_html(pre_draft["sharedSurfaces"], labels["empty"])]
    item_count = len(pre_draft["sharedSurfaces"])
    if not uses_default_source_priority(document):
        parts.append(source_priority_html(pre_draft, labels))
        item_count += len(pre_draft["sourcePriority"])
    return block_html(
        IMPACT_ID,
        labels["impact"],
        "".join(parts),
        slide_classes("block slide", item_count),
        extra_attributes=slide_attributes(KIND_CONTEXT, labels["impact"], IMPACT_ID),
    )


def list_block(document, labels, entry):
    identifier, label_key, field, classes, list_tag, kind = entry
    title = labels[label_key]
    content = list_html(document[field], labels["empty"], list_tag=list_tag)
    return block_html(
        identifier,
        title,
        content,
        slide_classes(classes, len(document[field])),
        extra_attributes=slide_attributes(kind, title, identifier),
    )


def decisions_html(document, labels, changes):
    questions = document[QUESTIONS_FIELD]
    title = labels["decisions"]
    statuses = [change_status(changes, "questions", question) for question in questions]
    content = list_html(questions, labels["empty"], list_tag="ol")
    if changes is not None and questions:
        entries = "".join(
            f"<li{unchanged_attribute([status])}>{escape(question)}{change_badge(status, labels)}</li>"
            for question, status in zip(questions, statuses)
        )
        content = f"<ol>{entries}</ol>"
    attributes = slide_attributes(KIND_DECISION, title, DECISIONS_ID) + unchanged_attribute(statuses)
    return block_html(
        DECISIONS_ID,
        title,
        content,
        slide_classes("block slide decisions", len(questions)),
        extra_attributes=attributes,
    )


def changes_banner_html(changes, labels):
    if changes is None:
        return ""
    revision = changes["revision"]
    heading = labels["changesSincePrevious"]
    if revision is not None:
        heading = labels["changesSince"].format(revision=revision)
    statuses = [status for field in DIFFED_FIELDS + ("questions",) for status in changes[field].values()]
    counts = [
        count_html(labels, "countNew", statuses.count(CHANGE_NEW)),
        count_html(labels, "countModified", statuses.count(CHANGE_MODIFIED)),
    ]
    removed = list(changes["removed"])
    if changes["removedQuestions"]:
        removed_questions = changes["removedQuestions"]
        removed.append(plural_form(labels, "countQuestions", removed_questions).format(count=removed_questions))
    removed_line = ""
    if removed:
        removed_line = f'<p>{escape(labels["removed"].format(items=SOURCE_SEPARATOR.join(removed)))}</p>'
    return (
        f'<section id="{CHANGES_ID}" class="changes-banner" aria-label="{escape(heading)}">'
        f"<p><strong>{escape(heading)}</strong>{escape(COUNT_SEPARATOR)}"
        f"{escape(COUNT_SEPARATOR).join(counts)}</p>{removed_line}</section>"
    )


def build_blocks(document, labels, changes):
    axis_sections = "".join(axis_section_html(document, axis, labels, changes) for axis in document["axes"])
    return "".join(
        [
            page_head_html(document, labels),
            changes_banner_html(changes, labels),
            decisions_html(document, labels, changes),
            brief_html(document, labels),
            list_block(document, labels, OUT_OF_SCOPE_BLOCK),
            axes_html(document, labels, changes),
            axis_sections,
            secondary_html(document, labels),
            impact_html(document, labels),
            agent_context_html(document, labels),
        ]
    )


def navigation_entry_html(identifier, title, children="", attributes=""):
    return f'<li{attributes}><a href="#{identifier}">{escape(title)}</a>{children}</li>'


def navigation_html(document, labels):
    axis_entries = "".join(
        navigation_entry_html(axis_anchor(axis["id"]), f"{axis['id']}{COUNT_SEPARATOR}{axis['title']}")
        for axis in document["axes"]
    )
    entries = [
        navigation_entry_html(DECISIONS_ID, labels["decisions"]),
        navigation_entry_html(BRIEF_ID, labels["need"]),
        navigation_entry_html(OUT_OF_SCOPE_ID, labels["outOfScope"]),
        navigation_entry_html(AXES_ID, labels["axes"], f'<ul class="nav-sub">{axis_entries}</ul>'),
        navigation_entry_html(SECONDARY_ID, labels["secondary"]),
        navigation_entry_html(IMPACT_ID, labels["impact"]),
        navigation_entry_html(AGENT_CONTEXT_ID, labels["agentContext"], attributes=f' id="{AGENT_NAV_ID}" hidden'),
    ]
    return "".join(entries)


def toolbar_html(labels, changes):
    buttons = list(TOOLBAR_BUTTONS)
    if changes is not None:
        buttons.insert(0, CHANGES_TOOLBAR_BUTTON)
    markup = "".join(
        f'<button id="{identifier}" type="button" aria-pressed="false">{escape(labels[label_key])}</button>'
        for identifier, label_key in buttons
    )
    return f'<div class="toolbar">{markup}</div>'


def presentation_bar_html(labels):
    return (
        f'<div id="{PRESENTATION_RAIL_ID}" class="presentation-rail" hidden></div>'
        f'<div id="{PRESENTATION_GRID_ID}" class="presentation-grid" hidden></div>'
        '<div id="presentation-bar" class="presentation-bar" hidden>'
        f'<button id="presentation-previous" type="button">{escape(labels["previous"])}</button>'
        '<span id="presentation-counter" class="presentation-counter"></span>'
        f'<button id="presentation-next" type="button">{escape(labels["next"])}</button>'
        f'<button id="{PRESENTATION_OVERVIEW_ID}" type="button" aria-pressed="false">'
        f'{escape(labels["overview"])}</button>'
        "</div>"
    )


def script_config_html(document, labels):
    config = {
        "labels": labels,
        "slideOrder": slide_order(document),
        "keyAttribute": SLIDE_KEY_ATTRIBUTE,
        "densityKey": DENSITY_STORAGE_KEY,
        "agentKey": AGENT_STORAGE_KEY,
        "themeKey": THEME_STORAGE_KEY,
        "themeAttribute": THEME_ATTRIBUTE,
        "darkTheme": DARK_THEME_VALUE,
        "lightTheme": LIGHT_THEME_VALUE,
        "agentSectionId": AGENT_CONTEXT_ID,
        "agentNoteId": AGENT_NOTE_ID,
        "agentNavId": AGENT_NAV_ID,
        "pageHeadId": PAGE_HEAD_ID,
        "briefId": BRIEF_ID,
        "changesButtonId": CHANGES_BUTTON_ID,
        "slideTargetAttribute": SLIDE_TARGET_ATTRIBUTE,
        "kindAttribute": SLIDE_KIND_ATTRIBUTE,
        "titleAttribute": SLIDE_TITLE_ATTRIBUTE,
        "referenceAttribute": SLIDE_REF_ATTRIBUTE,
        "presentingKindAttribute": PRESENTING_KIND_ATTRIBUTE,
        "kindLabelKeys": KIND_LABEL_KEYS,
    }
    payload = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    return f"<script>const PRD_CONFIG = {payload};</script>"


def render_document(document, changes=None):
    labels = labels_for(document)
    navigation = navigation_html(document, labels)
    body = build_blocks(document, labels, changes)
    note = labels["agentHiddenNote"].format(count=agent_entry_count(document))
    agent_note = f'<p class="agent-note" id="{AGENT_NOTE_ID}">{escape(note)}</p>'
    return (
        "<!doctype html>\n"
        f'<html lang="{escape(document["locale"])}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{escape(document["title"])}</title>\n'
        f"<style>{STYLE_CSS}</style>\n"
        f"<script>{THEME_BOOTSTRAP_JS}</script>\n"
        "</head>\n"
        "<body>\n"
        f'<div class="topbar"><span class="topbar-title">{escape(document["title"])}</span>'
        f"{toolbar_html(labels, changes)}</div>\n"
        '<div class="layout">'
        f'<aside><nav aria-label="{escape(labels["contents"])}"><strong>{escape(labels["contents"])}</strong>'
        f"<ul>{navigation}</ul></nav></aside>"
        f"<main>{body}{agent_note}</main></div>\n"
        f"{presentation_bar_html(labels)}\n"
        f"{script_config_html(document, labels)}\n"
        f"<script>{SCRIPT_JS}</script>\n"
        "</body>\n"
        "</html>\n"
    )


def budget_warning(path, unit_count, budget, unit):
    return f"{WARNING_PREFIX}{path} has {unit_count} {unit} (budget {budget})"


def check_text_budget(text, path, budget, warnings):
    words = count_words(text)
    if words > budget:
        warnings.append(budget_warning(path, words, budget, "words"))


def check_acceptance_budget(acceptance, path, warnings):
    for position, item in enumerate(acceptance):
        check_text_budget(item, f"{path}.acceptance[{position}]", ACCEPTANCE_WORD_BUDGET, warnings)


def missing_task_warning(path, axis_id):
    return f"{WARNING_PREFIX}{path}: axis '{axis_id}' has no task"


def check_vague_words(text, path, locale, warnings):
    for match in VAGUE_WORD_PATTERNS[locale].finditer(text):
        warnings.append(f"{WARNING_PREFIX}{path} uses vague word '{match.group(0)}'")


def check_items_vague_words(items, path, locale, warnings):
    for position, item in enumerate(items):
        check_vague_words(item, f"{path}[{position}]", locale, warnings)


def has_edge_case(acceptance, locale):
    pattern = EDGE_CASE_PATTERNS[locale]
    return any(pattern.match(item.strip()) for item in acceptance)


def missing_edge_case_warning(path):
    return f"{WARNING_PREFIX}{path}: must requirement has no error or edge-case acceptance criterion"


def collect_writing_warnings(document):
    warnings = []
    locale = document["locale"]
    for index, requirement in enumerate(document["requirements"]):
        path = f"requirements[{index}]"
        check_vague_words(requirement["description"], f"{path}.description", locale, warnings)
        check_items_vague_words(requirement["acceptance"], f"{path}.acceptance", locale, warnings)
        if requirement["priority"] == MUST_PRIORITY and not has_edge_case(requirement["acceptance"], locale):
            warnings.append(missing_edge_case_warning(f"{path}.acceptance"))
    for index, task in enumerate(document["tasks"]):
        path = f"tasks[{index}]"
        check_vague_words(task["expectedOutcome"], f"{path}.expectedOutcome", locale, warnings)
        check_items_vague_words(task["acceptance"], f"{path}.acceptance", locale, warnings)
    return warnings


def previous_index(previous, field):
    items = previous.get(field)
    if not isinstance(items, list):
        return {}
    return {
        item[ID_FIELD]: item
        for item in items
        if isinstance(item, dict) and isinstance(item.get(ID_FIELD), str)
    }


def item_change(item, previous_items):
    earlier = previous_items.get(item["id"])
    if earlier is None:
        return CHANGE_NEW
    if any(key in earlier and earlier[key] != value for key, value in item.items()):
        return CHANGE_MODIFIED
    return CHANGE_SAME


def previous_questions(previous):
    questions = previous.get(QUESTIONS_FIELD)
    if not isinstance(questions, list):
        return []
    return [question for question in questions if isinstance(question, str)]


def build_changes(document, previous):
    changes = {"removed": []}
    for field in DIFFED_FIELDS:
        earlier = previous_index(previous, field)
        current_ids = {item["id"] for item in document[field]}
        changes[field] = {item["id"]: item_change(item, earlier) for item in document[field]}
        changes["removed"].extend(identifier for identifier in earlier if identifier not in current_ids)
    earlier_questions = previous_questions(previous)
    changes["questions"] = {
        question: CHANGE_SAME if question in earlier_questions else CHANGE_NEW
        for question in document[QUESTIONS_FIELD]
    }
    changes["removedQuestions"] = sum(1 for question in earlier_questions if question not in document[QUESTIONS_FIELD])
    revision = previous.get(REVISION_FIELD)
    changes["revision"] = revision if isinstance(revision, str) and revision.strip() else None
    return changes


def collect_warnings(document):
    warnings = []
    check_text_budget(document["summary"], "summary", SUMMARY_WORD_BUDGET, warnings)
    for index, axis in enumerate(document["axes"]):
        path = f"axes[{index}]"
        check_text_budget(axis["summary"], f"{path}.summary", AXIS_SUMMARY_WORD_BUDGET, warnings)
        if not axis_items(document["tasks"], axis["id"]):
            warnings.append(missing_task_warning(path, axis["id"]))
    for field in BUDGETED_LIST_FIELDS:
        for index, item in enumerate(document[field]):
            check_text_budget(item, f"{field}[{index}]", LIST_ITEM_WORD_BUDGET, warnings)
    must_count = 0
    for index, requirement in enumerate(document["requirements"]):
        path = f"requirements[{index}]"
        acceptance = requirement["acceptance"]
        check_text_budget(requirement["description"], f"{path}.description", REQUIREMENT_DESCRIPTION_WORD_BUDGET, warnings)
        check_acceptance_budget(acceptance, path, warnings)
        if len(acceptance) > MAX_ACCEPTANCE_ITEMS:
            warnings.append(budget_warning(f"{path}.acceptance", len(acceptance), MAX_ACCEPTANCE_ITEMS, "items"))
        if requirement["priority"] == MUST_PRIORITY:
            must_count += 1
    if must_count > MAX_MUST_REQUIREMENTS:
        warnings.append(budget_warning("requirements", must_count, MAX_MUST_REQUIREMENTS, "must items"))
    for index, task in enumerate(document["tasks"]):
        path = f"tasks[{index}]"
        check_text_budget(task["expectedOutcome"], f"{path}.expectedOutcome", EXPECTED_OUTCOME_WORD_BUDGET, warnings)
        check_acceptance_budget(task["acceptance"], path, warnings)
    return warnings + collect_writing_warnings(document)


def report_warnings(warnings):
    for warning in warnings:
        print(warning, file=sys.stderr)
    if warnings:
        print(f"{WARNING_PREFIX}{len(warnings)} warnings", file=sys.stderr)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error


def load_previous(path):
    previous = load_json(path)
    if not isinstance(previous, dict):
        raise SystemExit(f"error: {path}: expected a JSON object")
    if previous.get(SCHEMA_VERSION_FIELD) != SCHEMA_VERSION:
        print(
            f"{NOTE_PREFIX}{path} uses schemaVersion {previous.get(SCHEMA_VERSION_FIELD)}; "
            "items are compared by identifier on the fields both versions share",
            file=sys.stderr,
        )
    return previous


def parse_arguments():
    parser = argparse.ArgumentParser(prog="renderPrd.py")
    parser.add_argument("input", help="PRD JSON source")
    parser.add_argument("output", help="HTML output path")
    parser.add_argument("--previous", help="earlier revision of the PRD JSON to highlight changes against")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    document = load_json(arguments.input)
    errors = validate_document(document)
    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"validation failed:\n{details}")
    changes = None
    if arguments.previous is not None:
        changes = build_changes(document, load_previous(arguments.previous))
    output_path = Path(arguments.output)
    output_path.write_text(render_document(document, changes), encoding="utf-8")
    print(output_path)
    report_warnings(collect_warnings(document))


if __name__ == "__main__":
    main()
