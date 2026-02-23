"""
Data preprocessing module for cleaning and chunking scraped data.
"""

import yaml
import json
import sys
from pathlib import Path
from typing import List, Dict

# Ensure project root is on sys.path when running as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from utils.text_utils import chunk_text, extract_metadata_from_url
from utils.db_utils import load_json, save_json, ensure_dir


class DataPreprocessor:
    """Preprocess scraped data into chunks ready for embedding."""
    
    def __init__(self, config_path: str = "config/scraping_config.yaml"):
        """Initialize preprocessor with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.chunk_size = self.config['chunking']['chunk_size']
        self.chunk_overlap = self.config['chunking']['chunk_overlap']
        self.min_chunk_size = self.config['chunking'].get('min_chunk_size', 100)
    
    def process_data(self, raw_data: List[Dict]) -> List[Dict]:
        """
        Process raw scraped data into chunks.
        
        Args:
            raw_data: List of raw scraped page data
            
        Returns:
            List of processed chunks with metadata
        """
        processed_chunks = []
        chunk_id = 0
        
        for page in raw_data:
            if page.get('status') != 'success' or not page.get('content'):
                continue
            
            url = page['url']
            title = page['title']
            content = page['content']
            
            # Extract metadata
            metadata = extract_metadata_from_url(url)
            metadata['title'] = title
            
            # Chunk the content
            chunks = chunk_text(content, self.chunk_size, self.chunk_overlap)
            
            # Create chunk records
            for idx, chunk in enumerate(chunks):
                if len(chunk) < self.min_chunk_size:
                    continue
                
                chunk_record = {
                    'chunk_id': f"{url}_{chunk_id}",
                    'source_url': url,
                    'title': title,
                    'content': chunk,
                    'content_type': metadata['content_type'],
                    'chunk_index': idx,
                    'metadata': metadata
                }
                
                processed_chunks.append(chunk_record)
                chunk_id += 1
        
        return processed_chunks
    
    def load_and_process(self, input_path: str) -> List[Dict]:
        """Load raw data and process it."""
        raw_data = load_json(input_path)
        return self.process_data(raw_data)
    
    def save_processed_data(self, processed_data: List[Dict], output_dir: str = None):
        """Save processed chunks to JSON."""
        if output_dir is None:
            output_dir = self.config['output']['processed_data_dir']
        
        ensure_dir(output_dir)
        output_path = Path(output_dir) / "processed_chunks.json"
        save_json(processed_data, str(output_path))
        print(f"Saved {len(processed_data)} processed chunks to {output_path}")


if __name__ == "__main__":
    preprocessor = DataPreprocessor()
    
    # Load raw data
    raw_data_path = "data/raw/raw_scraped_data.json"
    if Path(raw_data_path).exists():
        processed_chunks = preprocessor.load_and_process(raw_data_path)
        preprocessor.save_processed_data(processed_chunks)
    else:
        print(f"Raw data file not found: {raw_data_path}")
        print("Please run scraper.py first")
