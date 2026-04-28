"""OZE-Agent FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.billing import router as billing_router
from api.routes.dashboard import router as dashboard_router
from api.routes.google_oauth import router as google_oauth_router
from bot.config import Config

app = FastAPI(title="OZE-Agent API", version="0.1.0")

allowed_origins = [
    "http://localhost:3000",
]
if Config.DASHBOARD_URL:
    allowed_origins.append(Config.DASHBOARD_URL.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(google_oauth_router, prefix="/auth")
app.include_router(dashboard_router, prefix="/api")
app.include_router(billing_router, prefix="/internal/billing")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
