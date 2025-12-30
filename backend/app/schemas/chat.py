"""Pydantic schemas for chat API."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    sessionId: Optional[str] = Field(None, description="Session ID for continuing conversation")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty after stripping."""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    reply: str = Field(..., description="AI agent reply")
    sessionId: str = Field(..., description="Session ID for the conversation")


class ChatHistoryResponse(BaseModel):
    """Response schema for conversation history."""
    messages: list[dict] = Field(..., description="List of messages")

