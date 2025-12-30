"""MongoDB database connection and utilities."""
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.core.config import settings
from app.core.exceptions import DatabaseException
import logging

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_mongodb_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            _client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise DatabaseException(f"Failed to connect to MongoDB: {e}")
    return _client


def get_database() -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        client = get_mongodb_client()
        _db = client[settings.mongodb_db_name]
    return _db


def close_mongodb_connection():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def create_indexes():
    """Create database indexes for better performance."""
    db = get_database()
    
    # Indexes for conversations collection
    db.conversations.create_index("session_id", unique=True)
    db.conversations.create_index("created_at")
    db.conversations.create_index("updated_at")
    db.conversations.create_index("last_message_at")
    
    # Indexes for messages collection
    db.messages.create_index("conversation_id")
    db.messages.create_index("created_at")
    db.messages.create_index([("conversation_id", 1), ("created_at", 1)])  # Compound index for efficient queries
    db.messages.create_index("sender")  # For filtering by sender type
    
    logger.info("Database indexes created successfully")

