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
    Retrieve relevant FAQs using semantic search with caching.
    
    Args:
        query: User query text
        top_k: Number of top FAQs to return
        
    Returns:
        List of tuples (FAQ, similarity_score) sorted by relevance
    """
    redis_client = get_redis_client()
    cache_key = _get_cache_key(query, top_k)
    
    # Try to get from cache first
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"✅ CACHE HIT - Query: '{query[:50]}...' (key: {cache_key[:16]}...)")
                try:
                    cached_data = json.loads(cached_result)
                    faqs = [FAQ.from_dict(faq_dict) for faq_dict in cached_data["faqs"]]
                    scores = cached_data["scores"]
                    return list(zip(faqs, scores))
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse cached result: {e}. Clearing cache and recomputing.")
                    try:
                        redis_client.delete(cache_key)
                    except Exception:
                        pass
            else:
                logger.info(f"❌ CACHE MISS - Query: '{query[:50]}...' (key: {cache_key[:16]}...)")
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}. Continuing without cache.")
    
    # Cache miss or Redis unavailable - compute results
    logger.info(f"🔄 Computing FAQ search for: '{query[:50]}...'")
    
    # Generate embedding for query (with error handling)
    # Use "search_query" input type for user queries (optimized for search)
    try:
        query_embedding = generate_embedding(query, input_type="search_query")
    except Exception as e:
        logger.error(f"Failed to generate embedding for FAQ search: {e}")
        logger.warning("Continuing without FAQ context - chat will still work")
        return []  # Return empty list so chat can continue without FAQ context
    
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
        
        try:
            similarity = cosine_similarity(query_embedding, faq.embedding)
            faq_scores.append((faq, similarity))
        except Exception as e:
            logger.warning(f"Failed to calculate similarity for FAQ {faq.id}: {e}")
            continue
    
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
            cache_json = json.dumps(cache_data, default=str)
            logger.info(f"💾 Attempting to cache results for query: '{query[:50]}...' (key: {cache_key[:16]}...)")
            cache_success = redis_client.setex(
                cache_key,
                FAQ_CACHE_TTL,
                cache_json
            )
            if cache_success:
                logger.info(f"✅ CACHED - Query: '{query[:50]}...' (TTL: {FAQ_CACHE_TTL}s, key: {cache_key[:16]}...)")
            else:
                logger.warning(f"⚠️  Failed to cache FAQ results (setex returned False) for query: '{query[:50]}...'")
        except Exception as e:
            logger.error(f"❌ Redis cache write failed: {e}. Continuing without caching.", exc_info=True)
    
    return top_faqs


def format_faq_context(faqs: List[Tuple[FAQ, float]]) -> str:
    """
    Format FAQs into a concise context string for LLM prompt.
    
    Args:
        faqs: List of (FAQ, similarity_score) tuples
        
    Returns:
        Formatted context string (concise format to save tokens)
    """
    if not faqs:
        return ""
    
    # Use compact format to save tokens (but don't truncate - send full answers)
    context_parts = []
    for i, (faq, score) in enumerate(faqs, 1):
        # Send full FAQ answer (no truncation) so LLM has complete information
        context_parts.append(f"{i}. {faq.question} → {faq.answer}")
    
    return "\n".join(context_parts)

