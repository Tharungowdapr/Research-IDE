"""ResearchIDE Backend - Main FastAPI Application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time

from api.routes import auth, project, pipeline, agents, llm_config, export
from core.database import Base, engine
from core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResearchIDE API",
    description="AI-powered research assistant with multi-LLM support",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — must expose headers for SSE streaming
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Cache-Control", "X-Requested-With"],
    expose_headers=["Content-Type", "Content-Disposition"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start_time)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

app.include_router(auth.router,       prefix="/api/auth",     tags=["Authentication"])
app.include_router(project.router,    prefix="/api/projects", tags=["Projects"])
app.include_router(pipeline.router,   prefix="/api/pipeline", tags=["NLP Pipeline"])
app.include_router(agents.router,     prefix="/api/agents",   tags=["Agents"])
app.include_router(llm_config.router, prefix="/api/llm",      tags=["LLM Configuration"])
app.include_router(export.router,     prefix="/api/export",   tags=["Export"])

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
