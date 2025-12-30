"""Service for generating embeddings using sentence-transformers."""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
import os

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    """Get or load the embedding model with memory optimizations."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model with memory optimizations...")
        # Use CPU-only and memory-efficient settings
        # Set environment variables to reduce memory usage
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")  # Disable tokenizer parallelism
        os.environ.setdefault("OMP_NUM_THREADS", "1")  # Limit OpenMP threads
        
        # Load model with device='cpu' explicitly
        # Note: sentence-transformers automatically uses CPU if CUDA is not available
        _model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        logger.info("Model loaded successfully with memory optimizations")
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a given text with memory optimizations.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    model = get_embedding_model()
    # Use smaller batch size and convert to numpy immediately to free memory
    embedding = model.encode(
        text,
        convert_to_numpy=True,
        batch_size=1,  # Process one at a time to reduce memory
        show_progress_bar=False  # Disable progress bar to save memory
    )
    return embedding.tolist()


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

