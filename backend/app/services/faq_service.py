"""Service for FAQ retrieval using semantic search."""
from typing import List, Tuple
from app.models.faq import FAQ
from app.services.embedding_service import generate_embedding, cosine_similarity
from app.db.redis_client import get_redis_client
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

# Cache TTL in seconds (1 hour)
FAQ_CACHE_TTL = 3600


def _get_cache_key(query: str, top_k: int) -> str:
    """
    Generate a deterministic cache key for FAQ search.
    
    Uses SHA256 hash for consistent caching across sessions.
    """
    # Normalize query: lowercase and strip whitespace
    normalized_query = query.lower().strip()
    # Include top_k in cache key since results depend on it
    cache_string = f"{normalized_query}:{top_k}"
    # Use SHA256 for deterministic hashing
    cache_hash = hashlib.sha256(cache_string.encode()).hexdigest()
    return f"faq_search:{cache_hash}"


def get_relevant_faqs(query: str, top_k: int = 3) -> List[Tuple[FAQ, float]]:
    """
    Retrieve relevant FAQs using semantic search.
    
    Args:
        query: User query text
        top_k: Number of top FAQs to return
        
    Returns:
        List of tuples (FAQ, similarity_score) sorted by relevance
    """
    # Check Redis cache first
    redis_client = get_redis_client()
    cache_key = _get_cache_key(query, top_k)
    
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query: {query[:50]}")
                # Parse cached result
                cached_data = json.loads(cached_result)
                faqs = [FAQ.from_dict(faq_dict) for faq_dict in cached_data["faqs"]]
                scores = cached_data["scores"]
                return list(zip(faqs, scores))
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
    
    # Generate embedding for query
    query_embedding = generate_embedding(query)
    
    # Get all FAQs from database
    all_faqs = FAQ.find_all()
    
    if not all_faqs:
        logger.warning("No FAQs found in database")
        return []
    
    # Calculate similarity scores
    faq_scores: List[Tuple[FAQ, float]] = []
    for faq in all_faqs:
        if not faq.embedding:
            continue
        
        similarity = cosine_similarity(query_embedding, faq.embedding)
        faq_scores.append((faq, similarity))
    
    # Sort by similarity (descending) and take top_k
    faq_scores.sort(key=lambda x: x[1], reverse=True)
    top_faqs = faq_scores[:top_k]
    
    # Cache the result
    if redis_client:
        try:
            cache_data = {
                "faqs": [faq.to_dict() for faq, _ in top_faqs],
                "scores": [score for _, score in top_faqs]
            }
            redis_client.setex(
                cache_key,
                FAQ_CACHE_TTL,
                json.dumps(cache_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")
    
    return top_faqs


def format_faq_context(faqs: List[Tuple[FAQ, float]]) -> str:
    """
    Format FAQs into a context string for LLM prompt.
    
    Args:
        faqs: List of (FAQ, similarity_score) tuples
        
    Returns:
        Formatted context string
    """
    if not faqs:
        return ""
    
    context_parts = ["Relevant FAQ Knowledge:"]
    for i, (faq, score) in enumerate(faqs, 1):
        context_parts.append(
            f"{i}. Q: {faq.question}\n   A: {faq.answer}"
        )
    
    return "\n\n".join(context_parts)

