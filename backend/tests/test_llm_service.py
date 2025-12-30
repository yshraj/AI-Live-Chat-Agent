"""Tests for LLM service."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_service import generate_reply, get_gemini_model
from app.core.exceptions import LLMServiceException


@pytest.mark.asyncio
async def test_generate_reply_success():
    """Test successful reply generation."""
    mock_response = MagicMock()
    mock_response.text = "This is a test reply"
    
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response
    
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    
    with patch("app.services.llm_service.get_gemini_model", return_value=mock_model):
        reply = await generate_reply(
            user_message="Test message",
            conversation_history=[],
            faq_context=None
        )
        
        assert reply == "This is a test reply"
        mock_model.start_chat.assert_called_once()
        mock_chat.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_generate_reply_with_history():
    """Test reply generation with conversation history."""
    mock_response = MagicMock()
    mock_response.text = "Reply with history"
    
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response
    
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    
    history = [
        {"sender": "user", "content": "Hello"},
        {"sender": "ai", "content": "Hi there!"}
    ]
    
    with patch("app.services.llm_service.get_gemini_model", return_value=mock_model):
        reply = await generate_reply(
            user_message="How are you?",
            conversation_history=history,
            faq_context=None
        )
        
        assert reply == "Reply with history"
        mock_model.start_chat.assert_called_once()
        mock_chat.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_generate_reply_api_error():
    """Test handling of API errors."""
    mock_model = MagicMock()
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = Exception("API key invalid")
    mock_model.start_chat.return_value = mock_chat
    
    with patch("app.services.llm_service.get_gemini_model", return_value=mock_model):
        with pytest.raises(LLMServiceException) as exc_info:
            await generate_reply(
                user_message="Test",
                conversation_history=[],
                faq_context=None
            )
        
        assert "API key" in str(exc_info.value).lower() or "Failed" in str(exc_info.value)
