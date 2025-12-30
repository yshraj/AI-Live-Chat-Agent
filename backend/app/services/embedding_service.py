"""Service for generating embeddings using free API services."""
from typing import List
import numpy as np
import httpx
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env file if it exists (before reading environment variables)
try:
    from dotenv import load_dotenv
    # Try multiple locations for .env file
    # 1. backend/.env (relative to this file)
    # 2. .env in project root (relative to backend/)
    # 3. .env in current working directory
    env_paths = [
        Path(__file__).parent.parent.parent / ".env",  # backend/.env
        Path(__file__).parent.parent.parent.parent / ".env",  # project root/.env
        Path.cwd() / ".env",  # current directory/.env
        Path.cwd() / "backend" / ".env",  # backend/.env from project root
    ]
    
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            logger.info(f"✅ Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        logger.warning("⚠️ No .env file found in common locations")
except ImportError:
    # python-dotenv not installed, rely on environment variables or pydantic settings
    logger.warning("⚠️ python-dotenv not installed, cannot load .env file")
except Exception as e:
    logger.warning(f"⚠️ Error loading .env file: {e}")

# Model configuration - read from environment (loaded from .env by dotenv or pydantic)
# Cohere models: embed-english-v3.0, embed-english-light-v3.0, embed-multilingual-v3.0, embed-multilingual-light-v3.0, embed-v4.0
COHERE_MODEL = os.getenv("COHERE_EMBEDDING_MODEL", "embed-english-v3.0")  # Default to v3.0 for better quality
COHERE_API_KEY = os.getenv("COHERE_API_KEY", None)

# Hugging Face (fallback)
MODEL_NAME = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", None)

# Debug: Log which API keys are found (without exposing the keys)
if COHERE_API_KEY:
    logger.info(f"✅ COHERE_API_KEY loaded successfully (model: {COHERE_MODEL})")
else:
    logger.warning("⚠️ COHERE_API_KEY not found in environment variables")

if HF_API_KEY:
    logger.info("✅ HUGGINGFACE_API_KEY loaded successfully")
else:
    logger.warning("⚠️ HUGGINGFACE_API_KEY not found in environment variables")

# Hugging Face Inference API endpoints
# The router API uses a different format - try inference API endpoint directly
HF_INFERENCE_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_NAME}"

# Alternative: Use Hugging Face Spaces API (free, no auth needed)
# Using a public space that provides embeddings
HF_SPACE_URL = "https://sentence-transformers-all-MiniLM-L6-v2.hf.space/api/predict"


def _call_huggingface_inference(text: str) -> List[float]:
    """Call Hugging Face Inference API (works with API key)."""
    if not HF_API_KEY:
        raise Exception("HUGGINGFACE_API_KEY is required. Get a free token at https://huggingface.co/settings/tokens")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_API_KEY}"
    }
    
    # Try multiple endpoint formats
    endpoints_to_try = [
        f"https://api-inference.huggingface.co/pipeline/feature-extraction/{MODEL_NAME}",
        f"https://api-inference.huggingface.co/models/{MODEL_NAME}",
    ]
    
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for endpoint_url in endpoints_to_try:
            try:
                response = client.post(
                    endpoint_url,
                    headers=headers,
                    json={"inputs": text}
                )
                
                # Handle model loading (503) - wait and retry
                if response.status_code == 503:
                    import time
                    logger.warning(f"Model loading on {endpoint_url}, waiting 10 seconds...")
                    time.sleep(10)
                    response = client.post(endpoint_url, headers=headers, json={"inputs": text})
                elif response.status_code == 429:
                    import time
                    logger.warning("Rate limit exceeded, waiting 15 seconds...")
                    time.sleep(15)
                    response = client.post(endpoint_url, headers=headers, json={"inputs": text})
                elif response.status_code == 410:
                    # Endpoint deprecated, try next
                    logger.debug(f"Endpoint {endpoint_url} returned 410 Gone, trying next...")
                    continue
                elif response.status_code == 401:
                    raise Exception("Authentication failed. Please check your HUGGINGFACE_API_KEY.")
                elif response.status_code == 404:
                    # Try next endpoint
                    logger.debug(f"Endpoint {endpoint_url} returned 404, trying next...")
                    continue
                
                # Success!
                if response.is_success:
                    embedding = response.json()
                    
                    # Parse response - API returns list of floats or list of lists
                    if isinstance(embedding, list) and len(embedding) > 0:
                        if isinstance(embedding[0], list):
                            return embedding[0]  # Batch response, take first
                        return embedding  # Single response
                    elif isinstance(embedding, dict):
                        if "embeddings" in embedding:
                            emb = embedding["embeddings"]
                            return emb[0] if isinstance(emb[0], list) else emb
                        if "output" in embedding:
                            return embedding["output"]
                    
                    raise Exception(f"Unexpected API response format: {type(embedding)}")
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [404, 410]:
                    continue  # Try next endpoint
                raise
        
        # All endpoints failed
        raise Exception("All Hugging Face API endpoints failed. The API format may have changed. Please check https://huggingface.co/docs/api-inference")


def _call_cohere_api(text: str, input_type: str = "auto") -> List[float]:
    """
    Call Cohere Embed API (requires API key).
    
    Args:
        text: Text to embed
        input_type: "auto" (detects), "search_document" (for FAQs/content), or "search_query" (for user queries)
    """
    if not COHERE_API_KEY:
        raise Exception("COHERE_API_KEY not set")
    
    # Auto-detect input type based on text length (longer = document, shorter = query)
    if input_type == "auto":
        input_type = "search_document" if len(text) > 50 else "search_query"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COHERE_API_KEY}"
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.cohere.ai/v1/embed",
            headers=headers,
            json={
                "texts": [text],
                "model": COHERE_MODEL,
                "input_type": input_type  # Optimize for search
            }
        )
        
        if response.status_code == 429:
            import time
            logger.warning("Cohere rate limit exceeded, waiting 10 seconds...")
            time.sleep(10)
            response = client.post(
                "https://api.cohere.ai/v1/embed",
                headers=headers,
                json={
                    "texts": [text],
                    "model": COHERE_MODEL,
                    "input_type": input_type
                }
            )
        
        response.raise_for_status()
        result = response.json()
        
        if "embeddings" in result and len(result["embeddings"]) > 0:
            return result["embeddings"][0]
        
        raise Exception(f"Unexpected Cohere API response format: {result}")


def generate_embedding(text: str, input_type: str = "auto") -> List[float]:
    """
    Generate embedding using Cohere API (primary) or Hugging Face (fallback).
    
    Priority:
    1. Cohere Embed API (if COHERE_API_KEY is set) - RECOMMENDED
    2. Hugging Face Inference API (if HUGGINGFACE_API_KEY is set)
    
    Args:
        text: Input text to embed
        input_type: "auto" (detects based on length), "search_document", or "search_query"
                   Only used for Cohere API
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        Exception: If all API calls fail
    """
    errors = []
    
    # Try Cohere API first (recommended - better quality and consistency)
    if COHERE_API_KEY:
        try:
            logger.debug(f"Using Cohere API with model: {COHERE_MODEL}, input_type: {input_type}")
            return _call_cohere_api(text, input_type)
        except Exception as e:
            errors.append(f"Cohere ({COHERE_MODEL}): {str(e)}")
            logger.warning(f"Cohere API failed: {e}")
    
    # Fallback to Hugging Face if Cohere fails or not configured
    if HF_API_KEY:
        try:
            logger.debug("Falling back to Hugging Face Inference API...")
            return _call_huggingface_inference(text)
        except Exception as e:
            errors.append(f"Hugging Face: {str(e)}")
            logger.warning(f"Hugging Face API failed: {e}")
    
    # If no API keys or all failed, provide helpful error message
    if not COHERE_API_KEY and not HF_API_KEY:
        error_msg = (
            "No embedding API key configured. Please set one of:\n"
            "1. COHERE_API_KEY (recommended - free tier at https://cohere.com)\n"
            "2. HUGGINGFACE_API_KEY (free at https://huggingface.co/settings/tokens)\n\n"
            f"Current model setting: {COHERE_MODEL if COHERE_API_KEY else 'None'}"
        )
    else:
        error_msg = (
            f"All embedding APIs failed.\n"
            f"Current model: {COHERE_MODEL if COHERE_API_KEY else 'Hugging Face'}\n"
            f"Errors: {'; '.join(errors)}"
        )
    
    logger.error(error_msg)
    raise Exception(error_msg)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))

