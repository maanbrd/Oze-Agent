"""OZE-Agent FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.account import router as account_router
from api.routes.billing import router as billing_router
from api.routes.google_oauth import router as google_oauth_router
from api.routes.offers import router as offers_router
from api.routes.onboarding import router as onboarding_router

app = FastAPI(title="OZE-Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_oauth_router, prefix="/auth")
app.include_router(account_router, prefix="/api")
app.include_router(onboarding_router, prefix="/api/onboarding")
app.include_router(offers_router, prefix="/offers")
app.include_router(billing_router, prefix="/internal/billing")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
