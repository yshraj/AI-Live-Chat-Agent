"""FAQ model for MongoDB."""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pymongo.collection import Collection
from app.db.mongodb import get_database


class FAQ:
    """FAQ model with embeddings."""
    
    def __init__(
        self,
        category: str,
        question: str,
        answer: str,
        embedding: Optional[List[float]] = None,
        created_at: Optional[datetime] = None,
        _id: Optional[ObjectId] = None
    ):
        self._id = _id
        self.category = category
        self.question = question
        self.answer = answer
        self.embedding = embedding or []
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB."""
        doc = {
            "category": self.category,
            "question": self.question,
            "answer": self.answer,
            "embedding": self.embedding,
            "created_at": self.created_at
        }
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_dict(cls, doc: dict) -> "FAQ":
        """Create from MongoDB document."""
        return cls(
            _id=doc.get("_id"),
            category=doc["category"],
            question=doc["question"],
            answer=doc["answer"],
            embedding=doc.get("embedding", []),
            created_at=doc.get("created_at")
        )
    
    @staticmethod
    def get_collection() -> Collection:
        """Get MongoDB collection."""
        return get_database().faqs
    
    def save(self) -> ObjectId:
        """Save FAQ to database."""
        collection = self.get_collection()
        if self._id:
            collection.update_one(
                {"_id": self._id},
                {"$set": self.to_dict()}
            )
        else:
            result = collection.insert_one(self.to_dict())
            self._id = result.inserted_id
        return self._id
    
    @classmethod
    def find_all(cls) -> list["FAQ"]:
        """Find all FAQs."""
        collection = cls.get_collection()
        return [cls.from_dict(doc) for doc in collection.find()]

