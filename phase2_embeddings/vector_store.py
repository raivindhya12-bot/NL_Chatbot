"""
Store embeddings in ChromaDB vector database.
"""

import sys
import yaml
import chromadb
from pathlib import Path
from typing import List, Dict, Optional

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from chromadb.config import Settings
from utils.db_utils import load_json


class VectorStore:
    """Manage vector storage in ChromaDB."""
    
    def __init__(self, config_path: str = "config/embedding_config.yaml"):
        """Initialize vector store."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        db_config = self.config['vector_db']
        self.persist_directory = db_config['persist_directory']
        self.collection_name = db_config['collection_name']
        
        # Initialize ChromaDB client
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    def add_chunks(self, chunks: List[Dict]):
        """
        Add chunks with embeddings to vector store.
        
        Args:
            chunks: List of chunk dictionaries with 'embedding' field
        """
        ids = [chunk['chunk_id'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        documents = [chunk['content'] for chunk in chunks]
        
        # Extract metadata (exclude embedding and content)
        metadatas = []
        for chunk in chunks:
            metadata = {
                'source_url': chunk['source_url'],
                'title': chunk['title'],
                'content_type': chunk['content_type'],
                'chunk_index': chunk['chunk_index']
            }
            # Add any additional metadata
            if 'metadata' in chunk:
                metadata.update(chunk['metadata'])
            metadatas.append(metadata)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Added {len(chunks)} chunks to vector store")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of similar chunks with scores
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'chunk_id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_collection_info(self):
        """Get information about the collection."""
        count = self.collection.count()
        print(f"Collection '{self.collection_name}' contains {count} chunks")


if __name__ == "__main__":
    # Load chunks with embeddings
    chunks_path = "data/processed/chunks_with_embeddings.json"
    if Path(chunks_path).exists():
        chunks = load_json(chunks_path)
        
        store = VectorStore()
        store.add_chunks(chunks)
        store.get_collection_info()
    else:
        print(f"Chunks with embeddings file not found: {chunks_path}")
        print("Please run phase2_embeddings/embedding_generator.py first")
