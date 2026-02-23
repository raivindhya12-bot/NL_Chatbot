"""
RAG pipeline combining retrieval and generation using Groq LLM.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import os
import yaml
from groq import Groq
from dotenv import load_dotenv
from phase3_query.query_processor import QueryProcessor
from phase3_query.response_formatter import ResponseFormatter

# Load environment variables
load_dotenv()


class RAGPipeline:
    """Complete RAG pipeline for query answering."""
    
    def __init__(self, 
                 embedding_config_path: str = "config/embedding_config.yaml",
                 llm_config_path: str = "config/llm_config.yaml"):
        """Initialize RAG pipeline."""
        # Load LLM config
        with open(llm_config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Groq client
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = self.config['model']
        self.temperature = self.config['temperature']
        self.max_tokens = self.config['max_tokens']
        
        # Initialize query processor
        self.query_processor = QueryProcessor(embedding_config_path, llm_config_path)
        
        # Initialize response formatter
        self.formatter = ResponseFormatter(llm_config_path)
    
    def build_prompt(self, query: str, context_chunks: list) -> str:
        """
        Build prompt for LLM with context and query.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            
        Returns:
            Formatted prompt string
        """
        system_message = self.config['prompt']['system_message']
        
        # Format context
        context_text = "\n\n".join([
            f"[Source: {chunk['metadata'].get('title', 'Unknown')}]\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
        prompt = f"""System: {system_message}

Context:
{context_text}

User Question: {query}

Answer:"""
        
        return prompt
    
    def generate_response(self, query: str) -> dict:
        """
        Generate response for a user query.
        
        Args:
            query: User query string
            
        Returns:
            Dictionary with response and metadata
        """
        # Retrieve relevant context
        context_chunks = self.query_processor.process_query(query)
        
        if not context_chunks:
            return {
                'response': "Sorry, I can't help you with that",
                'sources': [],
                'error': None
            }
        
        # Build prompt
        prompt = self.build_prompt(query, context_chunks)
        
        # Generate response using Groq
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_text = chat_completion.choices[0].message.content
            
            # Detect strict out-of-context response
            is_out_of_context = "Sorry, I can't help you with that" in response_text
            
            # Format response with sources
            formatted_response = self.formatter.format_response(
                response_text,
                context_chunks if not is_out_of_context else []
            )
            
            return formatted_response
            
        except Exception as e:
            return {
                'response': f"Error generating response: {str(e)}",
                'sources': [],
                'error': str(e)
            }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG Chatbot for NextLeap.app')
    parser.add_argument('--query', type=str, required=True, help='User query')
    args = parser.parse_args()
    
    pipeline = RAGPipeline()
    result = pipeline.generate_response(args.query)
    
    print("\n" + "="*60)
    print("RESPONSE:")
    print("="*60)
    print(result['response'])
    
    if result.get('sources'):
        print("\n" + "="*60)
        print("SOURCES:")
        print("="*60)
        for source in result['sources']:
            print(f"- {source['title']}: {source['url']}")
