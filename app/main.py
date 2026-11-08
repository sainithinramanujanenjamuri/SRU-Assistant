"""Main FastAPI application entry point for SRU Assistant (Phase 10)."""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="SRU Assistant — Academic Query Resolution",
    description="A Grounded Retrieval-Augmented Generation (RAG) Framework for SR University",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local frontend and multi-origin interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount Frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    # Mount static assets if subfolder exists or serve root files
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index() -> FileResponse:
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return FileResponse(frontend_dir / "README.md")

    @app.get("/presentation", include_in_schema=False)
    @app.get("/presentation.html", include_in_schema=False)
    async def serve_presentation() -> FileResponse:
        pres_file = frontend_dir / "presentation.html"
        if pres_file.exists():
            return FileResponse(pres_file)
        return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
