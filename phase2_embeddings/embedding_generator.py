"""
Generate embeddings for text chunks using sentence-transformers.
"""

import yaml
import sys
from pathlib import Path
from typing import List, Dict

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from utils.db_utils import load_json


class EmbeddingGenerator:
    """Generate embeddings for text chunks."""
    
    def __init__(self, config_path: str = "config/embedding_config.yaml"):
        """Initialize embedding generator."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        model_name = self.config['model_name']
        device = self.config['device']
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = self.config['batch_size']
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'content' field
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk['content'] for chunk in chunks]
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=self.config.get('processing', {}).get('show_progress', True),
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def process_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with embeddings added
        """
        embeddings = self.generate_embeddings(chunks)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks


if __name__ == "__main__":
    # Load processed chunks
    chunks_path = "data/processed/processed_chunks.json"
    if Path(chunks_path).exists():
        chunks = load_json(chunks_path)
        
        generator = EmbeddingGenerator()
        chunks_with_embeddings = generator.process_chunks(chunks)
        
        # Save chunks with embeddings (temporary, before storing in vector DB)
        from utils.db_utils import save_json
        save_json(chunks_with_embeddings, "data/processed/chunks_with_embeddings.json")
        print(f"Generated embeddings for {len(chunks_with_embeddings)} chunks")
    else:
        print(f"Processed chunks file not found: {chunks_path}")
        print("Please run phase1_scraping/preprocessor.py first")
