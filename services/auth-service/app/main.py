"""Auth Service - Main Application"""
import sys
sys.path.append('/app')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth
from shared.database.session import create_tables

app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication and Authorization Service"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
async def startup():
    create_tables()

# Include routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/health")
async def health():
    return {"service": "auth-service", "status": "healthy"}
