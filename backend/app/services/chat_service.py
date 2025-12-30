"""Service for chat logic and message handling."""
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from bson import ObjectId
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.llm_service import generate_reply
from app.services.faq_service import get_relevant_faqs, format_faq_context
from app.core.config import settings
from app.core.exceptions import DatabaseException, LLMServiceException
import uuid
import logging

logger = logging.getLogger(__name__)


def _is_greeting(message: str) -> bool:
    """
    Check if message is a greeting that can be handled without RAG/LLM.
    
    Args:
        message: Lowercase message text
        
    Returns:
        True if message is a greeting
    """
    greeting_patterns = [
        "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
        "good evening", "hi there", "hello there", "hey there", "what's up",
        "howdy", "sup", "hiya", "morning", "afternoon", "evening"
    ]
    
    # Check if message is just a greeting (short and matches patterns)
    words = message.split()
    if len(words) <= 3:
        for pattern in greeting_patterns:
            if pattern in message:
                return True
    
    return False


def _is_simple_query(message: str) -> bool:
    """
    Check if message is a very simple query that doesn't need RAG.
    
    Args:
        message: Lowercase message text
        
    Returns:
        True if message is a simple query
    """
    simple_patterns = [
        "thanks", "thank you", "thank", "ty", "thx", "appreciate it",
        "ok", "okay", "got it", "understood", "cool", "nice", "good",
        "bye", "goodbye", "see you", "later", "have a good day"
    ]
    
    words = message.split()
    if len(words) <= 4:
        for pattern in simple_patterns:
            if pattern in message:
                return True
    
    return False


def _save_message_pair(
    conversation: Conversation,
    user_content: str,
    ai_content: str
) -> Tuple[Message, Message]:
    """
    Save both user and AI messages atomically.
    
    Args:
        conversation: Conversation object
        user_content: User message content
        ai_content: AI reply content
        
    Returns:
        Tuple of (user_message, ai_message)
    """
    # Save user message
    user_msg = Message(
        conversation_id=conversation._id,
        sender="user",
        content=user_content
    )
    user_msg.save()
    logger.debug(f"Saved user message: {user_content[:50]}...")
    
    # Save AI message
    ai_msg = Message(
        conversation_id=conversation._id,
        sender="ai",
        content=ai_content
    )
    ai_msg.save()
    logger.debug(f"Saved AI message: {ai_content[:50]}...")
    
    # Update conversation counts (both messages)
    conversation.increment_message_count(user_msg.created_at)
    conversation.increment_message_count(ai_msg.created_at)
    
    return user_msg, ai_msg


async def process_message(
    message: str,
    session_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Process a user message and generate AI response.
    
    This function ensures both user and AI messages are saved properly.
    
    Args:
        message: User message text
        session_id: Optional session ID for continuing conversation
        
    Returns:
        Tuple of (ai_reply, session_id)
        
    Raises:
        DatabaseException: If database operations fail
        LLMServiceException: If LLM service fails
    """
    # Get or create conversation
    if not session_id:
        session_id = str(uuid.uuid4())
    
    conversation = Conversation.create_or_get(session_id)
    logger.info(f"Processing message for session {session_id}, conversation {conversation._id}")
    
    try:
        # Get conversation history (before saving new message)
        all_messages = Message.find_by_conversation_id(
            conversation._id,
            limit=settings.message_history_limit * 2
        )
        
        # Format history for LLM (last N messages)
        recent_messages = all_messages[-settings.message_history_limit:]
        conversation_history = [
            {"sender": msg.sender, "content": msg.content}
            for msg in recent_messages
        ]
        
        # Check if this is a greeting or simple query
        message_lower = message.lower().strip()
        is_greeting = _is_greeting(message_lower)
        is_simple_query = _is_simple_query(message_lower)
        
        # Handle greetings directly without LLM call
        if is_greeting and len(conversation_history) == 0:
            ai_reply = "Hi there! 👋 I'm here to help you with questions about our store, products, orders, shipping, returns, and more. What can I help you with today?"
            
            # Save both messages atomically
            user_msg, ai_msg = _save_message_pair(conversation, message, ai_reply)
            
            logger.info(f"Processed greeting message for session {session_id} (skipped RAG/LLM). Saved {user_msg._id} and {ai_msg._id}")
            return ai_reply, session_id
        
        # Get FAQ context if needed
        faq_context = None
        if not is_greeting and not is_simple_query:
            relevant_faqs = get_relevant_faqs(message, top_k=3)
            faq_context = format_faq_context(relevant_faqs)
        
        # Generate AI reply
        try:
            ai_reply = await generate_reply(
                user_message=message,
                conversation_history=conversation_history,
                faq_context=faq_context
            )
            logger.info(f"Generated AI reply (length: {len(ai_reply)})")
        except LLMServiceException as e:
            # Use friendly error message
            ai_reply = "I apologize, but I'm experiencing technical difficulties right now. Please try again in a moment, or contact our support team directly."
            logger.error(f"LLM service error: {e}")
        
        # Ensure AI reply is not empty
        if not ai_reply or not ai_reply.strip():
            ai_reply = "I apologize, but I couldn't generate a response. Please try again."
            logger.warning("Empty AI reply generated, using fallback")
        
        # Save both messages atomically
        user_msg, ai_msg = _save_message_pair(conversation, message, ai_reply)
        
        logger.info(f"Successfully processed message for session {session_id}. User: {user_msg._id}, AI: {ai_msg._id}")
        
        return ai_reply, session_id
        
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}", exc_info=True)
        
        # Try to save error message if user message wasn't saved yet
        try:
            error_reply = "I apologize, but I encountered an error processing your message. Please try again."
            user_msg, ai_msg = _save_message_pair(conversation, message, error_reply)
            logger.info(f"Saved error messages: {user_msg._id}, {ai_msg._id}")
            return error_reply, session_id
        except Exception as save_error:
            logger.error(f"Failed to save error messages: {save_error}", exc_info=True)
        
        if isinstance(e, (DatabaseException, LLMServiceException)):
            raise
        raise DatabaseException(f"Failed to process message: {str(e)}")


def get_conversation_history(session_id: str) -> List[Dict[str, str]]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        List of messages with sender and content
    """
    conversation = Conversation.find_by_session_id(session_id)
    if not conversation:
        return []
    
    messages = Message.find_by_conversation_id(conversation._id)
    return [
        {
            "sender": msg.sender,
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        }
        for msg in messages
    ]

