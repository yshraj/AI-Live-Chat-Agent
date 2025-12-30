"""Service for Google Gemini LLM integration."""
import google.generativeai as genai
from typing import List, Dict, Optional
from app.core.config import settings
from app.core.exceptions import LLMServiceException
from app.utils.retry import retry_with_exponential_backoff
import logging
import asyncio

logger = logging.getLogger(__name__)

# Initialize Gemini client (will be initialized after settings are loaded)
_model: Optional[genai.GenerativeModel] = None


def get_gemini_model() -> genai.GenerativeModel:
    """Get or create Gemini model instance."""
    global _model
    if _model is None:
        genai.configure(api_key=settings.google_api_key)
        _model = genai.GenerativeModel(settings.google_model)
        logger.info(f"Initialized Google Gemini client with model: {settings.google_model}")
    return _model


def format_messages_for_gemini(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format messages for Gemini API.
    
    Gemini expects messages in format: [{"role": "user"|"model", "parts": [{"text": "..."}]}]
    """
    formatted = []
    for msg in messages:
        role = "user" if msg["sender"] == "user" else "model"
        formatted.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })
    return formatted


@retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)
async def generate_reply(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    faq_context: Optional[str] = None
) -> str:
    """
    Generate AI reply using Google Gemini.
    
    Args:
        user_message: Current user message
        conversation_history: Previous messages in conversation
        faq_context: Formatted FAQ context string
        
    Returns:
        AI-generated reply text
        
    Raises:
        LLMServiceException: If LLM API call fails
    """
    try:
        # Build system prompt with brand voice and context
        system_prompt = """You are an AI customer support agent for a small e-commerce store. Your role is to help customers with their questions about products, orders, shipping, returns, and general inquiries.

**YOUR PURPOSE:**
- Provide accurate, helpful, and friendly customer support
- Answer questions about products, shipping, returns, and store policies
- Guide customers through common issues and processes
- Maintain a professional yet warm and approachable tone

**WHAT YOU CAN DO:**
- Answer questions about products, shipping, returns, refunds, and store policies
- Provide information from the FAQ knowledge base
- Help with order tracking and status inquiries
- Explain store processes and procedures
- Offer general guidance on e-commerce topics related to the store

**WHAT YOU CANNOT DO:**
- Process orders, refunds, or payments (you can only provide information)
- Access customer accounts or personal information beyond what's shared
- Make changes to orders or accounts
- Provide technical support for third-party services
- Answer questions unrelated to the e-commerce store (e.g., general knowledge, unrelated topics)
- Provide medical, legal, or financial advice

**BRAND VOICE & COMMUNICATION STYLE:**
- Be friendly, empathetic, and solution-oriented
- Use clear, concise language (avoid jargon unless necessary)
- Be professional but warm and approachable
- Show genuine care for customer concerns
- Keep responses focused and relevant
- Use a helpful, supportive tone

**IMPORTANT GUIDELINES:**
- If a question is out of scope (not related to the store, products, orders, shipping, or returns), politely redirect: "I'm here to help with questions about our store, products, orders, shipping, and returns. Could you tell me how I can assist you with something related to our store?"
- If you don't know something specific, admit it honestly and offer to help find the answer or direct them to contact support
- Always prioritize accuracy over speed
- If a question requires account access or order modification, direct them to contact customer support directly"""
        
        # Add FAQ context if available
        if faq_context:
            system_prompt = f"{system_prompt}\n\n**RELEVANT FAQ KNOWLEDGE:**\n{faq_context}\n\nUse this information to answer customer questions accurately. If the FAQ doesn't contain relevant information, you can still help with general guidance, but be clear about limitations."
        
        # Build conversation history for Gemini
        formatted_history = format_messages_for_gemini(conversation_history)
        
        # Prepare the full conversation with system prompt
        # Gemini doesn't support system messages directly, so we prepend it to the first user message
        if len(formatted_history) == 0:
            # First message: include full system prompt
            full_user_message = f"{system_prompt}\n\nUser: {user_message}"
            chat_history = []
        else:
            # Subsequent messages: include system prompt only if FAQ context is new
            if faq_context:
                full_user_message = f"{system_prompt}\n\nUser: {user_message}"
            else:
                full_user_message = user_message
            chat_history = formatted_history
        
        # Call Gemini API (run in executor since it's synchronous)
        model = get_gemini_model()
        loop = asyncio.get_event_loop()
        
        # Run synchronous API call in executor to avoid blocking
        def call_gemini():
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(
                full_user_message,
                generation_config={
                    "max_output_tokens": settings.llm_max_tokens,
                    "temperature": settings.llm_temperature,
                }
            )
            return response
        
        response = await loop.run_in_executor(None, call_gemini)
        
        reply_text = response.text.strip()
        logger.info(f"Generated reply (length: {len(reply_text)})")
        
        return reply_text
        
    except Exception as e:
        error_msg = f"LLM API error: {str(e)}"
        logger.error(error_msg)
        
        # Handle specific error types
        if "API key" in str(e).lower() or "authentication" in str(e).lower() or "401" in str(e):
            raise LLMServiceException("Invalid API key. Please check your Google Gemini API key configuration.")
        elif "quota" in str(e).lower() or "rate limit" in str(e).lower() or "429" in str(e):
            raise LLMServiceException("API rate limit exceeded. Please try again later.")
        elif "timeout" in str(e).lower():
            raise LLMServiceException("Request timeout. Please try again.")
        elif "404" in str(e) or "not found" in str(e).lower():
            raise LLMServiceException(f"Model not found. Please check your Google Gemini model name (current: {settings.google_model}).")
        else:
            raise LLMServiceException(f"Failed to generate reply: {str(e)}")
