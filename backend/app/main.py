"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import chat, health
from app.db.mongodb import create_indexes, close_mongodb_connection
from app.db.redis_client import close_redis_connection
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Spur AI Chat Agent",
    description="AI-powered live chat support agent",
    version="1.0.0"
)

# CORS configuration
# Allow localhost for development and common deployment domains
cors_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    # Add production domains via environment variable
    # Format: "https://your-app.vercel.app,https://your-app.netlify.app"
]

# Allow additional origins from environment variable
import os
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    cors_origins.extend([origin.strip() for origin in additional_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(health.router, tags=["health"])


@app.on_event("startup")
async def startup_event():
    """Initialize database connections and indexes on startup."""
    try:
        create_indexes()
    except Exception as e:
        logging.error(f"Failed to create indexes: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    close_mongodb_connection()
    close_redis_connection()

