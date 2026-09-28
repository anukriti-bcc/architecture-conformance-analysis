# Architecture Analysis Engine — Build Progress

Living handoff doc. Updated as work proceeds so this can be picked up in
a fresh conversation without re-deriving context. If you're resuming,
read this file first, then skim `currentplan.docx` (source of truth for
the plan) which this build follows section-by-section.

## Target: Milestone 1 (see currentplan.docx)

Repository → Tree-sitter parsing → component/dependency extraction →
explicit architecture rules (YAML) → deterministic conformance analysis
→ FastAPI → React visualization.

Explicitly OUT of scope for Milestone 1 (do not implement yet):
LLM/semantic analysis, Git evolution mining, learned classifiers,
architecture health score, architecture recovery, multi-language support
beyond Python. Stub interfaces only (`SemanticAnalyzer`,
`EvolutionAnalyzer`) so the shape is right without hard-coding a design
that isn't decided yet.

## Status: IN PROGRESS

### Done
- `backend/models/component.py` — Component, Dependency, DependencyType, SourceLocation
- `backend/models/rule.py` — ArchitectureRule, RelationType, Architecture
- `backend/models/finding.py` — Finding, with evidence slots for structural
  (filled now) + architectural_intent/evolution_evidence/semantic_analysis/decision
  (reserved None, to be filled by later milestones without a schema migration)
- `backend/analysis/parser/base.py` — LanguageParser ABC (the language-agnostic
  extension point — adding JS/TS/Java later = new subclass, nothing else changes)
- `backend/analysis/parser/python_parser.py` — Tree-sitter Python import
  extractor. Handles: `import a.b`, `import a.b as c`, `from a.b import c, d`,
  `from . import x`, `from .a import b`, `from ..a import b`, wildcard imports.
  Tested manually, works correctly (see test snippet in build history).
  Does NOT extract calls/inheritance/instantiation yet (deliberate — see plan §4D).
- `backend/analysis/parser/registry.py` — extension → parser lookup, currently
  just `.py` → PythonParser.
- `backend/rules/loader.py` — loads architecture YAML (component_mapping + rules)
  into `Architecture` + `ComponentMapping`. Validates required fields.
- `backend/analysis/dependency/module_index.py` — resolves a dotted import
  string (absolute or relative) to a file path in the repo, using dotted-suffix
  matching. KNOWN LIMITATION (documented in file docstring): doesn't do real
  sys.path resolution, so duplicate basenames across unrelated packages can
  misresolve. Isolated to this one file so it's swappable later.

- `backend/analysis/dependency/repository_scanner.py` — scans a repo, builds
  Components (dir → architectural_type, closest ancestor wins), resolves every
  import to a target Component via ModuleIndex, emits Dependency objects.
  Tested manually against the demo repo — works correctly, including the
  deliberate violation at the exact expected line.
- `backend/analysis/dependency/graph.py` — NetworkX DiGraph builder +
  `graph_to_dict` serializer for the API/frontend.
- `backend/analysis/conformance/engine.py` — deterministic conformance
  engine. Unspecified component pairs (no rule either way) are NOT flagged
  (avoids false positives). Severity is flat "high" for forbidden violations
  only — explicitly provisional, no calibrated severity model yet.
- `backend/analysis/evolution/base.py`, `backend/analysis/semantic/base.py` —
  abstract interfaces + `NotYetImplemented*` stub implementations, wired into
  the API so the boundary exists without committing to a design.
- `backend/storage/memory_store.py` — in-memory `AnalysisRun` store (no DB
  yet — not needed for the demo; only file to touch when adding persistence).
- `backend/api/schemas/analyze.py` — pydantic request/response models.
- `backend/api/routes/analyze.py` + `backend/main.py` — FastAPI app. Endpoints:
  `POST /repositories/analyze`, `GET /analysis`, `GET /analysis/{id}`,
  `GET /analysis/{id}/graph`, `GET /analysis/{id}/findings`,
  `GET /findings/{id}`, `GET /findings/{id}/evolution` (returns null evidence),
  `POST /findings/{id}/semantic-analysis` (returns 501 by design).
- `datasets/sample-ecommerce/` — demo repo. Layered: controllers → services →
  repositories → database. `PaymentService.refund()` deliberately bypasses
  `PaymentRepository` and imports `database.connection` directly at line 45 —
  this is the one intentional violation, framed in a comment as a "hotfix
  shortcut" (realistic drift, not a contrived example). Everything else is
  conformant. `architecture/rules.yaml` defines 7 rules (3 allowed, 4 forbidden).
- `backend/tests/` — 40 pytest tests across parser, scanner, rule loader,
  conformance engine, and API (TestClient). **All 40 passing.**
- `backend/requirements.txt` — pinned dependency list.

- `frontend/` — React (Vite) app, blueprint/schematic visual theme
  (deliberate choice — the subject matter literally is architecture
  diagrams). 3 views: Overview (run analysis, stat cards), Graph
  (deterministic layered SVG layout by architectural_type, violation edges
  in red, click an edge for details), Findings (table + drill-down detail
  showing all four evidence slots — structural filled, the other three
  explicitly labelled "not analyzed — Milestone N, see path/to/base.py"
  rather than hidden, so the extensibility story is visible in the UI
  itself, not just in code comments). `npm run build` verified clean.
- `README.md` — setup/run instructions for backend + frontend, project
  layout, demo repo explanation, and an explicit "known limitations"
  section (language support, dependency types, module resolution,
  no persistence yet, provisional severity).
- `.gitignore` at project root.

### Next (in order)
1. Not yet done: one manual click-through of backend + frontend running
   together (Overview → Graph → Findings → detail) has NOT been done in
   this session — only `npm run build` (compiles clean) and the backend
   API (tested via TestClient, all 40 pytest tests pass) have been
   verified. If picking this back up: `cd backend && uvicorn main:app
   --reload` in one terminal, `cd frontend && npm install && npm run dev`
   in another, then click through once before considering this "verified
   end-to-end."
2. Zip the whole `architecture-analyzer/` dir and present to user via
   present_files, OR hand off as-is if the user wants to keep working in
   this same environment/session.
3. NOT yet started, per user's explicit instruction: the mid-viva report
   document. Only start when user asks — brief and guidelines docx files
   are already read and summarized above for when that time comes.

## Tech stack (locked, from currentplan.docx)
Backend: Python + FastAPI · Parsing: Tree-sitter (`tree-sitter`,
`tree-sitter-python`, both installed via pip already) · Graph: NetworkX ·
DB: PostgreSQL (not yet wired up — Milestone 1 can run in-memory/no DB
first; add persistence if time allows, it's not on the critical path for
the mid-viva demo) · Frontend: React · Git: not used yet (Milestone 2) ·
LLM: not used yet (Milestone 4+).

## Key design decisions already made (don't re-litigate)
- Component = file-level implementation entity; architectural_type = its
  Level-1 role (service/controller/repository/database/...), derived from
  directory structure via a configurable `component_mapping`, not hard-coded.
- Dependency types: only `import` for Milestone 1.
- Rule relations: `allowed` / `forbidden` acted on now; `required` /
  `conditional` accepted by schema but not implemented.
- Finding object has evidence slots for all future milestones already
  present (set to None) so the schema doesn't need to migrate later.
- `SemanticAnalyzer` / `EvolutionAnalyzer` are abstract interfaces only —
  explicitly do NOT implement or pick an LLM/Git library yet (per plan,
  this is intentional to avoid locking in a wrong design early).

## Where the source of truth lives
- `/mnt/user-data/uploads/currentplan.docx` — the actual conversation/plan
  this build follows (already read in full, contents reproduced in this
  project's docstrings where relevant).
- `/mnt/user-data/uploads/Major_Project_Direction_Working_Brief.docx` —
  the research framing (why evolution-aware evidence-guided escalation,
  RQs, hypotheses, baselines M1–M5). Relevant for the report later, not
  for Milestone 1 code.
- `/mnt/user-data/uploads/Major_Project_Guidelines_Reference.docx` —
  department rules (no Keras/TensorFlow/MATLAB — none used here; WP/EA
  classification — to be filled into the compliance table later, in the
  report, not urgent for code).

## Report
Explicitly NOT started yet, per user's request ("report comes later once
our demo is ready"). Do not start report/document work until the user
asks for it.
