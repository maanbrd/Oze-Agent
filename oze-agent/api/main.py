"""OZE-Agent FastAPI application."""

from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.config import Config
from api.routes.account import router as account_router
from api.routes.admin import router as admin_router
from api.routes.billing import router as billing_router
from api.routes.dashboard import router as dashboard_router
from api.routes.decisions import router as decisions_router
from api.routes.google_oauth import router as google_oauth_router
from api.routes.insights import router as insights_router
from api.routes.offers import router as offers_router
from api.routes.onboarding import router as onboarding_router

app = FastAPI(title="OZE-Agent API", version="0.1.0")


def _origin(value: str) -> str | None:
    value = (value or "").strip().rstrip("/")
    if not value:
        return None
    try:
        parsed = urlparse(value)
    except Exception:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def build_cors_origins() -> list[str]:
    origins: set[str] = set()
    for raw in (Config.CORS_ALLOWED_ORIGINS or "").split(","):
        origin = _origin(raw)
        if origin:
            origins.add(origin)
    for raw in (Config.DASHBOARD_URL, Config.ADMIN_URL):
        origin = _origin(raw)
        if origin:
            origins.add(origin)
    if Config.ENV == "dev":
        origins.update(
            {
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            }
        )
    return sorted(origins)


def build_cors_origin_regex() -> str | None:
    if Config.ENV == "dev":
        return r"^https://[a-z0-9-]+-maanbrds-projects\.vercel\.app$"
    if Config.CORS_ALLOWED_ORIGINS:
        return r"^https://[a-z0-9-]+-maanbrds-projects\.vercel\.app$"
    return None


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_origin_regex=build_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_oauth_router, prefix="/auth")
app.include_router(account_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(decisions_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(onboarding_router, prefix="/api/onboarding")
app.include_router(offers_router, prefix="/offers")
app.include_router(billing_router, prefix="/internal/billing")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
