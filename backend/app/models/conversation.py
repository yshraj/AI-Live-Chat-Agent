"""Conversation model for MongoDB."""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pymongo.collection import Collection
from app.db.mongodb import get_database


class Conversation:
    """Conversation model."""
    
    def __init__(
        self,
        session_id: str,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        message_count: int = 0,
        last_message_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id
        self.session_id = session_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.message_count = message_count
        self.last_message_at = last_message_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        doc = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
        }
        if self.last_message_at:
            doc["last_message_at"] = self.last_message_at
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_dict(cls, doc: dict) -> "Conversation":
        """Create from MongoDB document."""
        return cls(
            _id=doc.get("_id"),
            session_id=doc["session_id"],
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at"),
            message_count=doc.get("message_count", 0),
            last_message_at=doc.get("last_message_at")
        )
    
    @staticmethod
    def get_collection() -> Collection:
        """Get MongoDB collection."""
        return get_database().conversations
    
    def save(self) -> ObjectId:
        """Save conversation to database."""
        collection = self.get_collection()
        if self._id:
            # Update existing
            self.updated_at = datetime.utcnow()
            update_data = self.to_dict()
            # Don't update _id in update operation
            update_data.pop("_id", None)
            collection.update_one(
                {"_id": self._id},
                {"$set": update_data}
            )
        else:
            # Insert new
            result = collection.insert_one(self.to_dict())
            self._id = result.inserted_id
        return self._id
    
    def increment_message_count(self, last_message_time: Optional[datetime] = None):
        """Increment message count and update last message timestamp."""
        collection = self.get_collection()
        self.message_count += 1
        if last_message_time:
            self.last_message_at = last_message_time
        else:
            self.last_message_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        update_data = {
            "$inc": {"message_count": 1},
            "$set": {
                "updated_at": self.updated_at,
                "last_message_at": self.last_message_at
            }
        }
        collection.update_one({"_id": self._id}, update_data)
    
    @classmethod
    def find_by_session_id(cls, session_id: str) -> Optional["Conversation"]:
        """Find conversation by session ID."""
        collection = cls.get_collection()
        doc = collection.find_one({"session_id": session_id})
        if doc:
            return cls.from_dict(doc)
        return None
    
    @classmethod
    def create_or_get(cls, session_id: str) -> "Conversation":
        """Create new conversation or get existing one."""
        conversation = cls.find_by_session_id(session_id)
        if conversation:
            return conversation
        
        conversation = cls(session_id=session_id)
        conversation.save()
        return conversation
    
    def get_message_count(self) -> int:
        """Get actual message count from database."""
        from app.models.message import Message
        messages = Message.find_by_conversation_id(self._id)
        return len(messages)
    
    def sync_message_count(self):
        """Sync message_count field with actual message count."""
        actual_count = self.get_message_count()
        if actual_count != self.message_count:
            self.message_count = actual_count
            collection = self.get_collection()
            collection.update_one(
                {"_id": self._id},
                {"$set": {"message_count": actual_count}}
            )

