"""OZE-Agent FastAPI application."""

from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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


# Explicit allowlists instead of "*": with allow_credentials=True a wildcard is
# both risky and (per the CORS spec) ignored by browsers. Methods/headers are
# scoped to what the web app actually uses (JWT bearer auth + JSON/multipart).
CORS_ALLOWED_METHODS = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "x-oze-timestamp",
    "x-oze-signature",
]
# Response headers the browser is allowed to read (PDF download filename).
CORS_EXPOSE_HEADERS = ["Content-Disposition"]


# Cap request bodies to blunt memory-exhaustion DoS. JSON endpoints are small;
# only the offer-logo multipart upload needs headroom (the route itself enforces
# a 2 MB image cap). We reject early on a declared Content-Length — uvicorn/the
# platform also bound truly unbounded chunked streams.
JSON_BODY_LIMIT_BYTES = 1 * 1024 * 1024  # 1 MB
MULTIPART_BODY_LIMIT_BYTES = 6 * 1024 * 1024  # 6 MB


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
            except ValueError:
                size = None
            if size is not None:
                content_type = request.headers.get("content-type", "")
                limit = (
                    MULTIPART_BODY_LIMIT_BYTES
                    if content_type.startswith("multipart/form-data")
                    else JSON_BODY_LIMIT_BYTES
                )
                if size > limit:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large."},
                    )
        return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_origin_regex=build_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=CORS_ALLOWED_METHODS,
    allow_headers=CORS_ALLOWED_HEADERS,
    expose_headers=CORS_EXPOSE_HEADERS,
)
app.add_middleware(BodySizeLimitMiddleware)

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
@app.get("/healthz")
async def health():
    return {"status": "ok", "version": "0.1.0"}
