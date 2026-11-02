

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import models
from .database import engine
from .routers import auth, produce, orders, logistics, payments, analytics

# Ensure all database tables exist upon server startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FarmCart API",
    description="Direct Farm-to-Consumer Marketplace: Farmer/FPO -> Marketplace -> Smart Order Engine -> Logistics -> Delivery -> Payment Settlement",
    version="1.0.0",
)

# CORS Policy configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to specific frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Business & Domain Routers
app.include_router(auth.router)
app.include_router(produce.router)
app.include_router(orders.router)
app.include_router(logistics.router)
app.include_router(payments.router)
app.include_router(analytics.router)

# Serve static frontend assets if directory exists
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/")
def health_check():
    """Service health check & entry point directory."""
    return {
        "status": "ok",
        "service": "FarmCart API",
        "tagline": "Direct Farm-to-Consumer Marketplace",
        "docs": "/docs",
        "frontend": "/frontend/"
    }
