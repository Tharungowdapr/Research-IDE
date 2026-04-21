"""
ResearchIDE Backend - Main FastAPI Application
Handles: Auth, Projects, NLP Pipeline, Agent Orchestration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time

from api.routes import auth, project, pipeline, agents, llm_config
from core.database import Base, engine
from core.config import settings

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResearchIDE API",
    description="AI-powered research assistant with multi-LLM support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(project.router, prefix="/api/projects", tags=["Projects"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["NLP Pipeline"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(llm_config.router, prefix="/api/llm", tags=["LLM Configuration"])

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,
    )
