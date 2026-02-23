"""
Format LLM responses with source citations.
"""

import yaml
from typing import List, Dict


class ResponseFormatter:
    """Format responses with source citations."""
    
    def __init__(self, config_path: str = "config/llm_config.yaml"):
        """Initialize response formatter."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.include_sources = self.config['prompt'].get('include_sources', True)
    
    def format_response(self, response_text: str, context_chunks: List[Dict]) -> Dict:
        """
        Format response with source citations.
        
        Args:
            response_text: Raw LLM response
            context_chunks: Context chunks used for generation
            
        Returns:
            Formatted response dictionary
        """
        # Extract unique sources
        sources = []
        seen_urls = set()
        
        for chunk in context_chunks:
            url = chunk['metadata'].get('source_url', '')
            title = chunk['metadata'].get('title', 'Unknown')
            
            if url and url not in seen_urls:
                sources.append({
                    'url': url,
                    'title': title,
                    'content_type': chunk['metadata'].get('content_type', 'page')
                })
                seen_urls.add(url)
        
        return {
            'response': response_text,
            'sources': sources if self.include_sources else []
        }
