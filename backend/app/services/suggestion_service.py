"""Service for generating chat suggestions based on ingested data."""
from typing import List
from app.models.message import Message
from app.models.conversation import Conversation
from app.services.llm_service import generate_reply
import logging
from collections import Counter
import re

logger = logging.getLogger(__name__)


def analyze_user_messages(limit: int = 100) -> List[str]:
    """
    Analyze user messages from conversations to identify common patterns and generate suggestions.
    
    Args:
        limit: Maximum number of recent messages to analyze
        
    Returns:
        List of suggested prompts based on user behavior
    """
    try:
        # Get all conversations
        all_conversations = Conversation.find_all()
        
        if not all_conversations:
            # Return default suggestions if no data - support-focused
            return [
                "What is your return policy?",
                "How can you help me?",
                "What are your shipping options?",
                "Tell me about your products"
            ]
        
        # Collect user messages from all conversations
        user_messages = []
        for conv in all_conversations[:50]:  # Limit to 50 most recent conversations
            messages = Message.find_by_conversation_id(conv._id, limit=20)
            user_msgs = [msg.content for msg in messages if msg.sender == "user"]
            user_messages.extend(user_msgs)
        
        if not user_messages:
            return [
                "What is your return policy?",
                "How can you help me?",
                "What are your shipping options?",
                "Tell me about your products"
            ]
        
        # Analyze patterns in user messages
        suggestions = _generate_suggestions_from_messages(user_messages)
        
        # Ensure we have at least 2 suggestions
        if len(suggestions) < 2:
            suggestions.extend([
                "What is your return policy?",
                "How can you help me?"
            ])
        
        return suggestions[:4]  # Return top 4 suggestions
        
    except Exception as e:
        logger.error(f"Error analyzing user messages: {e}", exc_info=True)
        # Return default suggestions on error - support-focused
        return [
            "What is your return policy?",
            "How can you help me?",
            "What are your shipping options?",
            "Tell me about your products"
        ]


def _generate_suggestions_from_messages(messages: List[str]) -> List[str]:
    """
    Generate suggestions by analyzing message patterns.
    
    Args:
        messages: List of user message contents
        
    Returns:
        List of suggested prompts
    """
    # Extract common action verbs and patterns
    action_patterns = {
        "analyze": ["analysis", "analyze", "analyzing", "break down"],
        "identify": ["identify", "find", "list", "show"],
        "create": ["create", "make", "build", "generate", "write"],
        "summarize": ["summarize", "summary", "brief", "overview"],
        "explain": ["explain", "how", "what", "why", "describe"],
        "compare": ["compare", "difference", "vs", "versus"],
        "improve": ["improve", "better", "optimize", "enhance"],
        "plan": ["plan", "strategy", "roadmap", "schedule"]
    }
    
    # Count occurrences of action patterns
    pattern_counts = Counter()
    message_lower = " ".join([msg.lower() for msg in messages])
    
    for pattern, keywords in action_patterns.items():
        count = sum(message_lower.count(keyword) for keyword in keywords)
        if count > 0:
            pattern_counts[pattern] = count
    
    # Generate suggestions based on most common patterns
    suggestions = []
    
    # Get top 3 most common patterns
    top_patterns = [pattern for pattern, _ in pattern_counts.most_common(3)]
    
    # Map patterns to suggestion templates
    suggestion_templates = {
        "analyze": "Create in-depth analysis",
        "identify": "Identify actionable tasks",
        "create": "Create a detailed plan",
        "summarize": "Summarize key points",
        "explain": "Explain the main concepts",
        "compare": "Compare different options",
        "improve": "Suggest improvements",
        "plan": "Create a strategic plan"
    }
    
    for pattern in top_patterns:
        if pattern in suggestion_templates:
            suggestions.append(suggestion_templates[pattern])
    
    # If we have messages, try to extract common topics
    if messages:
        # Look for common question patterns
        questions = [msg for msg in messages if "?" in msg]
        if questions:
            # Extract common question starters
            question_starters = []
            for q in questions[:10]:  # Sample first 10 questions
                # Extract first few words
                words = q.split()[:4]
                if len(words) >= 2:
                    starter = " ".join(words).rstrip("?")
                    question_starters.append(starter)
            
            if question_starters:
                # Get most common question starter
                most_common = Counter(question_starters).most_common(1)
                if most_common:
                    suggestions.append(most_common[0][0])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)
    
    return unique_suggestions


async def generate_ai_suggestions(context: str = "") -> List[str]:
    """
    Use LLM to generate intelligent suggestions based on conversation context.
    
    Args:
        context: Optional context about the user's needs
        
    Returns:
        List of AI-generated suggestions
    """
    try:
        # Analyze recent messages
        recent_messages = analyze_user_messages(limit=50)
        
        # Use LLM to generate contextual suggestions
        prompt = f"""Based on the following common user queries, generate 4 concise, actionable chat suggestions that would be helpful:
        
Common queries: {', '.join(recent_messages[:5])}

Generate 4 short, actionable suggestions (each 3-6 words) that users might want to ask. Return only the suggestions, one per line, without numbering or bullets."""

        # Generate suggestions using LLM
        ai_suggestions = await generate_reply(
            user_message=prompt,
            conversation_history=[],
            faq_context=None
        )
        
        # Parse LLM response into list
        suggestions = []
        for line in ai_suggestions.split('\n'):
            line = line.strip()
            # Remove numbering, bullets, etc.
            line = re.sub(r'^[\d\.\-\*]\s*', '', line)
            if line and len(line) < 50:  # Reasonable length
                suggestions.append(line)
        
        # Fallback to analyzed suggestions if LLM fails
        if not suggestions or len(suggestions) < 2:
            return recent_messages[:4]
        
        return suggestions[:4]
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}", exc_info=True)
        # Fallback to analyzed suggestions
        return analyze_user_messages(limit=50)[:4]

