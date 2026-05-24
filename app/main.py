from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.sync import router as sync_router
from app.api.webhook import router as webhook_router
from app.api.privacy import router as privacy_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup — nothing needed yet (engine is lazy)
    yield
    # Shutdown — dispose engine
    from app.database import engine
    await engine.dispose()


app = FastAPI(
    title="Live in a Week API",
    description="Backend for the Live in a Week browser extension",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the extension and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# --- Routers ---
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(sync_router)
app.include_router(webhook_router)
app.include_router(privacy_router)
