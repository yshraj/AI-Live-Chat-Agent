"""Chat API routes."""
from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.chat_service import process_message, get_conversation_history
from app.core.exceptions import ChatException, LLMServiceException, DatabaseException, ValidationException
from app.models.conversation import Conversation
from app.models.message import Message
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(request: ChatMessageRequest):
    """
    Send a message and get AI response.
    
    Args:
        request: Chat message request with message and optional sessionId
        
    Returns:
        ChatMessageResponse with AI reply and sessionId
        
    Raises:
        HTTPException: If validation fails or service errors occur
    """
    try:
        # Validate message length
        if len(request.message) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message exceeds maximum length of 2000 characters"
            )
        
        # Process message
        reply, session_id = await process_message(
            message=request.message,
            session_id=request.sessionId
        )
        
        return ChatMessageResponse(
            reply=reply,
            sessionId=session_id
        )
        
    except ValidationException as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except LLMServiceException as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please try again later."
        )
    except DatabaseException as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        ChatHistoryResponse with list of messages
    """
    try:
        messages = get_conversation_history(session_id)
        return ChatHistoryResponse(messages=messages)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation history"
        )


@router.get("/debug/{session_id}")
async def debug_conversation(session_id: str):
    """
    Debug endpoint to verify conversation and message saving.
    
    Args:
        session_id: Session ID
        
    Returns:
        Debug information about the conversation
    """
    try:
        conversation = Conversation.find_by_session_id(session_id)
        if not conversation:
            return {
                "session_id": session_id,
                "conversation_exists": False,
                "message": "No conversation found for this session"
            }
        
        # Get message count
        message_count = Message.count_by_conversation(conversation._id)
        latest_messages = Message.get_latest_by_conversation(conversation._id, limit=5)
        
        return {
            "session_id": session_id,
            "conversation_exists": True,
            "conversation_id": str(conversation._id),
            "conversation_message_count": conversation.message_count,
            "actual_message_count": message_count,
            "counts_match": conversation.message_count == message_count,
            "latest_messages": [
                {
                    "id": str(msg._id),
                    "sender": msg.sender,
                    "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in reversed(latest_messages)  # Show oldest first
            ]
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )

