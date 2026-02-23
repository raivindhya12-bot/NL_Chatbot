"""
Text processing utilities for chunking and cleaning text.
"""

import re
from typing import List


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def extract_metadata_from_url(url: str) -> dict:
    """
    Extract metadata from URL.
    
    Args:
        url: URL string
        
    Returns:
        Dictionary with metadata
    """
    metadata = {
        "source_url": url,
        "content_type": "page"
    }
    
    if "/blog/" in url:
        metadata["content_type"] = "blog"
    elif "/reviews" in url:
        metadata["content_type"] = "reviews"
    elif "/for-companies" in url:
        metadata["content_type"] = "companies"
    
    return metadata
