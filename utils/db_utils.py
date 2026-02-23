"""
Database and storage utilities.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


def save_json(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: List of dictionaries to save
        filepath: Path to save file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_dir(directory: str) -> None:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)
