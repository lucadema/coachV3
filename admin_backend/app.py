"""FastAPI app for the separate Aether Glimpse Admin backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin_backend.config import get_settings
from admin_backend.routes import router


settings = get_settings()
app = FastAPI(title="Aether Glimpse Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token"],
)

app.include_router(router)
