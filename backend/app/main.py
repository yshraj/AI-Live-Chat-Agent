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
    "http://localhost:5175",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:8080",
    # Production domains
    "https://ai-live-chat-agent-aijz.vercel.app",
    # Add additional production domains via environment variable
    # Format: "https://your-app.vercel.app,https://your-app.netlify.app"
]

# Allow additional origins from environment variable
import os
additional_origins = os.getenv("CORS_ORIGINS", "")
if additional_origins:
    # Split by comma and clean up whitespace
    origins_list = [origin.strip() for origin in additional_origins.split(",") if origin.strip()]
    cors_origins.extend(origins_list)
    logging.info(f"CORS: Added origins from environment: {origins_list}")

# Log allowed origins (without sensitive info)
logging.info(f"CORS: Configured with {len(cors_origins)} allowed origin(s)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
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

