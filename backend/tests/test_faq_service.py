"""Tests for FAQ service."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.faq_service import get_relevant_faqs, format_faq_context
from app.models.faq import FAQ
from datetime import datetime


@pytest.fixture
def mock_faqs():
    """Create mock FAQs for testing."""
    return [
        FAQ(
            category="Shipping",
            question="What is your shipping policy?",
            answer="We offer free shipping on orders over $50.",
            embedding=[0.1, 0.2, 0.3]
        ),
        FAQ(
            category="Returns",
            question="What is your return policy?",
            answer="We offer 30-day returns.",
            embedding=[0.4, 0.5, 0.6]
        ),
    ]


def test_get_relevant_faqs(mock_faqs):
    """Test FAQ retrieval."""
    with patch("app.services.faq_service.FAQ.find_all", return_value=mock_faqs):
        with patch("app.services.faq_service.generate_embedding", return_value=[0.15, 0.25, 0.35]):
            with patch("app.services.faq_service.get_redis_client", return_value=None):
                results = get_relevant_faqs("shipping policy", top_k=2)
                
                assert len(results) == 2
                assert all(isinstance(item, tuple) and len(item) == 2 for item in results)
                assert all(isinstance(faq, FAQ) for faq, _ in results)


def test_get_relevant_faqs_empty():
    """Test FAQ retrieval with no FAQs."""
    with patch("app.services.faq_service.FAQ.find_all", return_value=[]):
        with patch("app.services.faq_service.get_redis_client", return_value=None):
            results = get_relevant_faqs("test query")
            assert results == []


def test_format_faq_context():
    """Test FAQ context formatting."""
    faqs = [
        (FAQ(
            category="Shipping",
            question="What is shipping?",
            answer="Shipping info",
            embedding=[]
        ), 0.9),
        (FAQ(
            category="Returns",
            question="What is returns?",
            answer="Returns info",
            embedding=[]
        ), 0.8),
    ]
    
    context = format_faq_context(faqs)
    
    assert "Relevant FAQ Knowledge:" in context
    assert "What is shipping?" in context
    assert "What is returns?" in context
    assert "Shipping info" in context


def test_format_faq_context_empty():
    """Test formatting empty FAQ list."""
    context = format_faq_context([])
    assert context == ""

