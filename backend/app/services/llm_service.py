"""Service for Google Gemini LLM integration."""
import logging
import asyncio
import warnings
from typing import List, Dict, Optional, Union, Any
from app.core.config import settings
from app.core.exceptions import LLMServiceException
from app.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)

# Try to import new package, fallback to old one
_client_new = None
_model_old = None
GENAI_NEW = False
genai = None

try:
    # Try new google.genai package
    from google import genai
    GENAI_NEW = True
    logger.info("✅ Using google.genai package (new)")
except ImportError:
    # Fallback to old package
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")
        import google.generativeai as genai
    GENAI_NEW = False
    logger.warning("⚠️  Using deprecated google.generativeai package. Please install google-genai: pip install google-genai")


def get_gemini_client():
    """Get or create Gemini client instance (new API) or model (old API)."""
    global _client_new, _model_old
    
    if GENAI_NEW:
        # New google.genai package - use Client
        if _client_new is None:
            _client_new = genai.Client(api_key=settings.google_api_key)
            logger.info(f"Initialized Google Gemini Client with model: {settings.google_model} (new API)")
        return _client_new
    else:
        # Old google.generativeai package - use GenerativeModel
        if _model_old is None:
            genai.configure(api_key=settings.google_api_key)
            _model_old = genai.GenerativeModel(settings.google_model)
            logger.info(f"Initialized Google Gemini Model: {settings.google_model} (old API)")
        return _model_old


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
        # Build optimized system prompt with STRICT brevity requirements and VibeThreads brand voice
        system_prompt = """You are a customer support agent for VibeThreads, a Gen Z-focused clothing brand specializing in oversized t-shirts, streetwear, and accessories. You work for VibeThreads and help customers with their questions.

**Brand Identity - VibeThreads:**
- Gen Z-focused streetwear brand
- Specializes in oversized t-shirts, accessories, and trendy clothing
- Values: Self-expression, comfort, authenticity, community
- Tone: Casual, friendly, relatable, energetic but not overly slangy
- We're about that perfect oversized fit and fresh designs

**Your Role:** You represent VibeThreads and provide helpful information about products, orders, shipping, returns, and store policies. You ARE part of the VibeThreads support team. Be enthusiastic about our products but keep it real.

**MANDATORY Response Length Rules (STRICTLY ENFORCE):**
- MAXIMUM 3-4 lines per response. NO EXCEPTIONS.
- For simple questions, use 1-2 lines only.
- Use bullet points ONLY if absolutely necessary (max 3-4 bullets, each 1 line).
- NEVER write paragraphs. Use brief, direct sentences.
- NEVER exceed 4 lines total. If you need more space, prioritize the most important info.
- Be conversational but EXTREMELY concise.

**Brand Voice Guidelines:**
- Use casual, friendly language (e.g., "Hey!", "No worries", "Totally get it")
- Show enthusiasm but stay professional
- Use Gen Z-friendly terms naturally (e.g., "vibe", "fit", "drop") but don't overdo it
- Be helpful and authentic - like talking to a friend who works at the store
- Keep it brief and to the point - Gen Z values quick, clear answers

**Response Format Examples:**
- Good: "Hey! We accept returns within 30 days. Items need to be unused with tags attached. Hit us up with your order number and we'll get you sorted!"
- Bad: Long paragraphs explaining every detail in overly formal language.

**Response Style:** Casual, friendly, enthusiastic, and BRIEF. Sound like a helpful Gen Z person who genuinely cares. Get straight to the point - customers want quick answers, not essays.

**Important:** Always act as if you work for VibeThreads. Never say you don't sell products or that you're just an AI. You are VibeThreads' support agent helping customers find their perfect fit and vibe.

**Scope:** Only answer VibeThreads-related questions (products, orders, shipping, returns, sizing, accessories, etc.). For out-of-scope questions, redirect: "I'm here to help with VibeThreads products, orders, shipping, and returns. What can I help you with?"

**Limitations:** You provide information only. For order changes/refunds, direct customers to contact support@vibethreads.com or use the live chat."""
        
        # Add FAQ context if available
        if faq_context:
            system_prompt = f"{system_prompt}\n\n**FAQ:**\n{faq_context}\n\nUse FAQ info when relevant. Extract ONLY the essential information and keep your response to 3-4 lines maximum. Be brief and concise."
        
        # Build conversation history for Gemini
        formatted_history = format_messages_for_gemini(conversation_history)
        
        # Prepare the full conversation with system prompt
        # Gemini doesn't support system messages directly, so we prepend it to the first user message
        # Add brevity reminder to user message
        brevity_reminder = "\n\n[IMPORTANT: Keep your response to 3-4 lines maximum. Be brief and concise.]"
        
        if len(formatted_history) == 0:
            # First message: include full system prompt
            full_user_message = f"{system_prompt}\n\nUser: {user_message}{brevity_reminder}"
            chat_history = []
        else:
            # Subsequent messages: include system prompt only if FAQ context is new
            if faq_context:
                full_user_message = f"{system_prompt}\n\nUser: {user_message}{brevity_reminder}"
            else:
                # Still add brevity reminder even without system prompt
                full_user_message = f"{user_message}{brevity_reminder}"
            chat_history = formatted_history
        
        # Call Gemini API (run in executor since it's synchronous)
        client_or_model = get_gemini_client()
        loop = asyncio.get_event_loop()
        
        # Run synchronous API call in executor to avoid blocking
        def call_gemini():
            if GENAI_NEW:
                # New API: use Client.models.generate_content
                client = client_or_model
                # Build contents list from history + current message
                contents = []
                for msg in chat_history:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [{"text": msg["parts"][0]["text"]}]})
                contents.append({"role": "user", "parts": [{"text": full_user_message}]})
                
                response = client.models.generate_content(
                    model=settings.google_model,
                    contents=contents,
                    config={
                        "max_output_tokens": settings.llm_max_tokens,
                        "temperature": settings.llm_temperature,
                    }
                )
                # New API response has .text attribute directly
                # Create a compatible response object for consistency
                class Response:
                    def __init__(self, text, candidates=None):
                        self.text = text
                        self.candidates = candidates or []
                
                # Extract text from response (new API structure)
                response_text = ""
                candidates_list = []
                
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    # Try to extract from candidates
                    try:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            response_text = candidate.content.parts[0].text if candidate.content.parts else ""
                        candidates_list = response.candidates
                    except Exception:
                        pass
                
                return Response(response_text, candidates_list)
            else:
                # Old API: use GenerativeModel.start_chat
                model = client_or_model
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
        
        # Check if response was truncated
        reply_text = response.text.strip() if hasattr(response, 'text') and response.text else ""
        
        # Check if response might be incomplete (Gemini sometimes truncates)
        if not reply_text:
            raise LLMServiceException("Empty response from LLM")
        
        # Post-process to enforce brevity: limit to 4 lines maximum
        lines = reply_text.split('\n')
        if len(lines) > 4:
            # Take first 4 lines and truncate if needed
            reply_text = '\n'.join(lines[:4])
            # Remove any incomplete sentences at the end
            if reply_text and not reply_text[-1] in '.!?':
                # Find last complete sentence
                last_period = reply_text.rfind('.')
                last_exclamation = reply_text.rfind('!')
                last_question = reply_text.rfind('?')
                last_sentence_end = max(last_period, last_exclamation, last_question)
                if last_sentence_end > len(reply_text) * 0.5:  # Only truncate if we keep at least 50%
                    reply_text = reply_text[:last_sentence_end + 1]
            logger.info(f"Response truncated to 4 lines for brevity (original: {len(lines)} lines)")
        
        # Also limit character count (approximately 500 chars = ~3-4 lines)
        if len(reply_text) > 500:
            # Truncate at last complete sentence before 500 chars
            truncated = reply_text[:500]
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > 300:  # Only truncate if we keep substantial content
                reply_text = reply_text[:last_sentence_end + 1]
            else:
                reply_text = truncated + "..."
            logger.info(f"Response truncated to ~500 chars for brevity (original: {len(response.text)} chars)")
        
        # Check finish reason to detect truncation
        finish_reason = "UNKNOWN"
        try:
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason if hasattr(response.candidates[0], 'finish_reason') else "UNKNOWN"
        except Exception:
            pass
        
        # Log warning if response was truncated
        if finish_reason == "MAX_TOKENS":
            logger.warning(f"Response truncated due to max tokens. Length: {len(reply_text)}, Max tokens: {settings.llm_max_tokens}")
        elif reply_text.endswith("...") and len(reply_text) > 100:
            logger.warning(f"Response might be truncated (ends with '...'). Length: {len(reply_text)}")
        
        logger.info(f"Generated reply (length: {len(reply_text)}, lines: {len(reply_text.split(chr(10)))}, finish_reason: {finish_reason})")
        
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
