from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routers import auth, executives, briefing, health, connections, semantic_models, dashboards
from app.auth import get_password_hash
from app.database import AsyncSessionLocal
from app.models import User
from app.auth import get_user_by_email

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_demo_user()
    yield


async def seed_demo_user():
    """Create a demo user on first startup."""
    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, "demo@prism.ai")
        if not existing:
            user = User(
                email="demo@prism.ai",
                full_name="Demo User",
                company="Acme Corp",
                hashed_password=get_password_hash("demo1234"),
                is_active=True,
            )
            db.add(user)
            await db.commit()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTPException", "detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred."},
    )

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(executives.router, prefix="/api/v1")
app.include_router(briefing.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")
app.include_router(semantic_models.router, prefix="/api/v1")
app.include_router(dashboards.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Prism API — AI Operating System for Business Decisions", "docs": "/docs"}
