"""Message model for MongoDB."""
from datetime import datetime
from typing import Optional, Literal
from bson import ObjectId
from pymongo.collection import Collection
from app.db.mongodb import get_database


SenderType = Literal["user", "ai"]


class Message:
    """Message model."""
    
    def __init__(
        self,
        conversation_id: ObjectId,
        sender: SenderType,
        content: str,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id
        self.conversation_id = conversation_id
        self.sender = sender
        self.content = content
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        doc = {
            "conversation_id": self.conversation_id,
            "sender": self.sender,
            "content": self.content,
            "created_at": self.created_at
        }
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_dict(cls, doc: dict) -> "Message":
        """Create from MongoDB document."""
        return cls(
            _id=doc.get("_id"),
            conversation_id=doc["conversation_id"],
            sender=doc["sender"],
            content=doc["content"],
            created_at=doc.get("created_at")
        )
    
    @staticmethod
    def get_collection() -> Collection:
        """Get MongoDB collection."""
        return get_database().messages
    
    def save(self) -> ObjectId:
        """Save message to database."""
        collection = self.get_collection()
        doc = self.to_dict()
        result = collection.insert_one(doc)
        self._id = result.inserted_id
        
        # Verify the message was saved
        if not self._id:
            raise Exception("Failed to save message: no ID returned")
        
        return self._id
    
    @classmethod
    def count_by_conversation(cls, conversation_id: ObjectId) -> int:
        """Count messages in a conversation."""
        collection = cls.get_collection()
        return collection.count_documents({"conversation_id": conversation_id})
    
    @classmethod
    def get_latest_by_conversation(cls, conversation_id: ObjectId, limit: int = 1) -> list["Message"]:
        """Get latest messages from a conversation."""
        collection = cls.get_collection()
        cursor = collection.find({"conversation_id": conversation_id}).sort("created_at", -1).limit(limit)
        return [cls.from_dict(doc) for doc in cursor]
    
    @classmethod
    def find_by_conversation_id(
        cls,
        conversation_id: ObjectId,
        limit: Optional[int] = None
    ) -> list["Message"]:
        """Find messages by conversation ID, ordered by created_at."""
        collection = cls.get_collection()
        query = {"conversation_id": conversation_id}
        cursor = collection.find(query).sort("created_at", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return [cls.from_dict(doc) for doc in cursor]

