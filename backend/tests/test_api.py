"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_send_message_success():
    """Test successful message sending."""
    with patch("app.api.routes.chat.process_message") as mock_process:
        mock_process.return_value = ("AI reply", "test-session-123")
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "AI reply"
        assert data["sessionId"] == "test-session-123"


def test_send_message_with_session_id():
    """Test sending message with existing session ID."""
    with patch("app.api.routes.chat.process_message") as mock_process:
        mock_process.return_value = ("AI reply", "existing-session")
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello", "sessionId": "existing-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sessionId"] == "existing-session"


def test_send_message_empty():
    """Test sending empty message."""
    response = client.post(
        "/chat/message",
        json={"message": ""}
    )
    
    assert response.status_code == 422  # Validation error


def test_send_message_too_long():
    """Test sending message that's too long."""
    long_message = "a" * 2001
    
    response = client.post(
        "/chat/message",
        json={"message": long_message}
    )
    
    assert response.status_code == 400


def test_send_message_llm_error():
    """Test handling LLM service errors."""
    from app.core.exceptions import LLMServiceException
    
    with patch("app.api.routes.chat.process_message") as mock_process:
        mock_process.side_effect = LLMServiceException("LLM unavailable")
        
        response = client.post(
            "/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert "unavailable" in data["detail"].lower()


def test_get_history():
    """Test getting conversation history."""
    mock_messages = [
        {"sender": "user", "content": "Hello", "created_at": "2024-01-01T00:00:00"},
        {"sender": "ai", "content": "Hi!", "created_at": "2024-01-01T00:00:01"},
    ]
    
    with patch("app.api.routes.chat.get_conversation_history", return_value=mock_messages):
        response = client.get("/chat/history/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2


def test_get_history_not_found():
    """Test getting history for non-existent session."""
    with patch("app.api.routes.chat.get_conversation_history", return_value=[]):
        response = client.get("/chat/history/non-existent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []

