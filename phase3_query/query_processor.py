"""
Process user queries and retrieve relevant context from vector store.
"""

import yaml
from sentence_transformers import SentenceTransformer
from phase2_embeddings.vector_store import VectorStore


class QueryProcessor:
    """Process queries and retrieve relevant context."""
    
    def __init__(self, 
                 embedding_config_path: str = "config/embedding_config.yaml",
                 llm_config_path: str = "config/llm_config.yaml"):
        """Initialize query processor."""
        # Load embedding model (same as used for indexing)
        with open(embedding_config_path, 'r') as f:
            embedding_config = yaml.safe_load(f)
        
        model_name = embedding_config['model_name']
        device = embedding_config['device']
        self.embedding_model = SentenceTransformer(model_name, device=device)
        
        # Load LLM config for retrieval settings
        with open(llm_config_path, 'r') as f:
            llm_config = yaml.safe_load(f)
        
        self.top_k = llm_config['retrieval']['top_k']
        self.similarity_threshold = llm_config['retrieval']['similarity_threshold']
        
        # Initialize vector store
        self.vector_store = VectorStore(embedding_config_path)
    
    def process_query(self, query: str) -> list:
        """
        Process a user query and retrieve relevant chunks.
        
        Args:
            query: User query string
            
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=self.top_k)
        
        # Filter by similarity threshold (if distance is available)
        filtered_results = []
        for result in results:
            if result['distance'] is not None:
                # ChromaDB uses distance, lower is better
                # Convert to similarity score (1 - normalized distance)
                similarity = 1 - result['distance']
                if similarity >= self.similarity_threshold:
                    result['similarity'] = similarity
                    filtered_results.append(result)
            else:
                filtered_results.append(result)
        
        return filtered_results
