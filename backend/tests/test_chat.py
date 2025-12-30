"""Tests for chat service."""
import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from app.services.chat_service import process_message, get_conversation_history
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.exceptions import DatabaseException, LLMServiceException


@pytest.fixture
def mock_conversation():
    """Create mock conversation."""
    conv = Conversation(session_id="test-session-123")
    conv._id = ObjectId()
    return conv


@pytest.mark.asyncio
async def test_process_message_new_session(mock_conversation):
    """Test processing message with new session."""
    with patch("app.services.chat_service.Conversation.create_or_get", return_value=mock_conversation):
        with patch("app.services.chat_service.Message") as mock_message:
            mock_msg_instance = MagicMock()
            mock_message.return_value = mock_msg_instance
            
            with patch("app.services.chat_service.Message.find_by_conversation_id", return_value=[]):
                with patch("app.services.chat_service.get_relevant_faqs", return_value=[]):
                    with patch("app.services.chat_service.format_faq_context", return_value=""):
                        with patch("app.services.chat_service.generate_reply", return_value="AI reply"):
                            reply, session_id = await process_message("Hello")
                            
                            assert reply == "AI reply"
                            assert session_id is not None
                            assert mock_msg_instance.save.call_count == 2  # User + AI messages


@pytest.mark.asyncio
async def test_process_message_existing_session(mock_conversation):
    """Test processing message with existing session."""
    with patch("app.services.chat_service.Conversation.create_or_get", return_value=mock_conversation):
        with patch("app.services.chat_service.Message") as mock_message:
            mock_msg_instance = MagicMock()
            mock_message.return_value = mock_msg_instance
            
            with patch("app.services.chat_service.Message.find_by_conversation_id", return_value=[]):
                with patch("app.services.chat_service.get_relevant_faqs", return_value=[]):
                    with patch("app.services.chat_service.format_faq_context", return_value=""):
                        with patch("app.services.chat_service.generate_reply", return_value="AI reply"):
                            reply, session_id = await process_message("Hello", session_id="existing-session")
                            
                            assert reply == "AI reply"
                            assert session_id == "existing-session"


@pytest.mark.asyncio
async def test_process_message_llm_error(mock_conversation):
    """Test handling LLM service errors."""
    with patch("app.services.chat_service.Conversation.create_or_get", return_value=mock_conversation):
        with patch("app.services.chat_service.Message") as mock_message:
            mock_msg_instance = MagicMock()
            mock_message.return_value = mock_msg_instance
            
            with patch("app.services.chat_service.Message.find_by_conversation_id", return_value=[]):
                with patch("app.services.chat_service.get_relevant_faqs", return_value=[]):
                    with patch("app.services.chat_service.format_faq_context", return_value=""):
                        with patch("app.services.chat_service.generate_reply", side_effect=LLMServiceException("LLM error")):
                            reply, session_id = await process_message("Hello")
                            
                            # Should return error message
                            assert "difficulties" in reply.lower() or "error" in reply.lower()


def test_get_conversation_history(mock_conversation):
    """Test getting conversation history."""
    mock_messages = [
        Message(
            conversation_id=mock_conversation._id,
            sender="user",
            content="Hello"
        ),
        Message(
            conversation_id=mock_conversation._id,
            sender="ai",
            content="Hi there!"
        ),
    ]
    
    with patch("app.services.chat_service.Conversation.find_by_session_id", return_value=mock_conversation):
        with patch("app.services.chat_service.Message.find_by_conversation_id", return_value=mock_messages):
            history = get_conversation_history("test-session-123")
            
            assert len(history) == 2
            assert history[0]["sender"] == "user"
            assert history[1]["sender"] == "ai"


def test_get_conversation_history_not_found():
    """Test getting history for non-existent session."""
    with patch("app.services.chat_service.Conversation.find_by_session_id", return_value=None):
        history = get_conversation_history("non-existent")
        assert history == []

