"""OZE-Agent FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.google_oauth import router as google_oauth_router

app = FastAPI(title="OZE-Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_oauth_router, prefix="/auth")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
