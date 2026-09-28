from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze import router as analyze_router

app = FastAPI(
    title="Architecture Analysis Engine",
    description=(
        "Milestone 1: repository -> Tree-sitter parsing -> component/dependency "
        "extraction -> explicit architecture rules -> deterministic conformance "
        "analysis. See docs/PROGRESS.md for the full roadmap."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/")
def root() -> dict:
    return {
        "name": "Architecture Analysis Engine",
        "milestone": 1,
        "docs": "/docs",
    }
