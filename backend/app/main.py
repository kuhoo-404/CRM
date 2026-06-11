from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.database import engine, Base
from app.utils.exceptions import CRMException

# Import all models so Base.metadata knows about them before create_all
import app.models  # noqa: F401


from app.routers import ingest, threads, contacts, dashboard, rag, agent, respond

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL)

app = FastAPI(
    title="SenAI CRM",
    description="AI-powered CRM with autonomous email triage, RAG, and agent reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler — always returns consistent error envelope ───────
@app.exception_handler(CRMException)
async def crm_exception_handler(request: Request, exc: CRMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.APP_ENV == "development" else None,
        },
    )

# ── Create tables on startup (dev convenience — use Alembic in production) ───
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(threads.router)
app.include_router(contacts.router)
app.include_router(dashboard.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(respond.router)
@app.get("/")
def root():
    return {"message": "SenAI CRM Backend", "docs": "/docs", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}