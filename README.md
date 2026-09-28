# Architecture Analysis Engine — Milestone 1

An evidence-guided architecture conformance checker. This is Milestone 1
of a larger plan (see `docs/PROGRESS.md` for the full roadmap and design
decisions): repository → Tree-sitter parsing → component/dependency
extraction → explicit architecture rules → deterministic conformance
analysis → API → React visualization.

It is **not** a demo built to look good once and be thrown away — every
piece (parser, scanner, conformance engine, API, frontend) is the real
foundation the later milestones (Git-evolution mining, LLM-based semantic
analysis, escalation policy) plug directly into. See the `NotYetImplemented*`
stub classes in `backend/analysis/evolution/` and `backend/analysis/semantic/`
for exactly where that happens.

## What it does right now

1. Walks a Python repository and parses it with Tree-sitter (not regex).
2. Maps files to architectural roles (controller/service/repository/
   database/...) using a configurable `component_mapping`.
3. Resolves every `import` statement to a target file inside the repo.
4. Compares every observed dependency against an explicit architecture
   definition (YAML: `allowed` / `forbidden` rules).
5. Serves everything through a FastAPI backend and renders it in a React
   frontend: an overview, a layered dependency graph (violations
   highlighted), and a findings table with drill-down detail.

## Project layout

```
backend/            FastAPI app, parser, scanner, conformance engine
  analysis/
    parser/          Tree-sitter-based per-language parsers (Python only, for now)
    dependency/       repository scanning, module resolution, graph building
    conformance/      the deterministic rule-checking engine
    evolution/        NOT IMPLEMENTED — Milestone 2 interface (Git mining)
    semantic/         NOT IMPLEMENTED — Milestone 4 interface (LLM analysis)
  models/            Component, Dependency, Rule, Finding data models
  rules/             architecture YAML loader
  api/               routes + pydantic schemas
  storage/           in-memory analysis-run store (no DB dependency yet)
  tests/             40 pytest tests
frontend/            React (Vite) app — Overview / Graph / Findings views
datasets/
  sample-ecommerce/   demo repo: layered backend with one deliberate violation
docs/
  PROGRESS.md         living build log — read this first if picking this back up
```

## Running it

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Runs on `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

Run the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173` and proxies `/api/*` to the backend
(see `vite.config.js`) — no CORS configuration needed in dev.

### Using it

1. Open `http://localhost:5173`.
2. On the Overview page, the form is pre-filled with paths to the bundled
   demo repo (`datasets/sample-ecommerce`, relative to wherever the
   backend process's working directory is — adjust if you run `uvicorn`
   from somewhere else). Click **Run analysis**.
3. You'll land on the Graph view: files grouped into rows by architectural
   role, with dependency edges drawn between them. The one violating edge
   (`payment_service.py` → `connection.py`, service reaching around its
   repository straight into the database) is drawn in red.
4. The Findings tab lists every governed dependency with its status, and
   clicking one shows its full evidence record — including the empty
   `evolution_evidence` / `semantic_analysis` slots, so it's visible in
   the UI itself that those are designed-but-not-built yet, not silently
   missing.

## The demo repository

`datasets/sample-ecommerce/` is a small layered e-commerce backend
(controllers → services → repositories → database) with one deliberate
violation: `PaymentService.refund()` bypasses `PaymentRepository` and
imports the database connection directly, framed as a "hotfix shortcut"
— the kind of small, easy-to-miss thing architectural drift actually
looks like, rather than an obviously-wrong toy example. Everything else
in the repo is conformant. `datasets/sample-ecommerce/architecture/rules.yaml`
defines the expected architecture (7 rules: 3 allowed, 4 forbidden).

You can point the analyzer at any other Python repository by writing a
matching `architecture/*.yaml` file for it (see that file for the schema)
and giving its path on the Overview page.

## Known Milestone-1 limitations

- **Language support**: Python only. Adding a language is one new
  `LanguageParser` subclass in `backend/analysis/parser/` — nothing
  downstream changes (see `analysis/parser/base.py`).
- **Dependency types**: only `import` statements. Calls, inheritance,
  and instantiation are deliberately deferred (see plan).
- **Module resolution**: matches dotted import paths against filesystem
  suffixes rather than doing real `sys.path` resolution — can misresolve
  in repos with duplicate module basenames across unrelated packages.
  Isolated entirely inside `analysis/dependency/module_index.py`.
- **No persistence**: analysis runs live in memory
  (`backend/storage/memory_store.py`) and are lost on restart. Not on the
  critical path for the mid-viva demo; swap this one file for a
  PostgreSQL-backed store when persistence is needed.
- **Severity**: flat "high" for forbidden violations, "unset" otherwise —
  explicitly provisional, no calibrated severity model yet.

## Roadmap

See `docs/PROGRESS.md` for the full milestone plan and the reasoning
behind what's deliberately not built yet.
