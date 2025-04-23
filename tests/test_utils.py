"""
Test Utilities Module

This module provides utility functions and mock setup for testing the docling_parse components.
"""

import sys
from unittest.mock import MagicMock
from pathlib import Path
import os
import tempfile
import json
import shutil
import unittest
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling fix helper
import docling_fix

def setup_mock_docling():
    """
    Creates mock functions and data for testing docling.
    
    Returns:
        tuple: (mock_process_func, mock_document_data, mock_sentences)
    """
    # Create mock document
    mock_document = MagicMock()
    
    # Set up metadata
    mock_document.metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "date": "2023-01-01",
        "language": "en",
        "pages": 2
    }
    
    # Create pages
    page1 = MagicMock()
    page1.page_number = 1
    page1.width = 612
    page1.height = 792
    
    page2 = MagicMock()
    page2.page_number = 2
    page2.width = 612
    page2.height = 792
    
    # Create segments for page 1
    segment1 = MagicMock()
    segment1.id = "seg1"
    segment1.text = "This is the first segment."
    segment1.page_number = 1
    segment1.bbox = (10, 10, 200, 40)
    segment1.type = "text"
    
    segment2 = MagicMock()
    segment2.id = "seg2"
    segment2.text = "This is the second segment."
    segment2.page_number = 1
    segment2.bbox = (10, 50, 200, 80)
    segment2.type = "text"
    
    # Create segments for page 2
    segment3 = MagicMock()
    segment3.id = "seg3"
    segment3.text = "This is a segment on page 2."
    segment3.page_number = 2
    segment3.bbox = (10, 10, 200, 40)
    segment3.type = "text"
    
    # Create images
    image1 = MagicMock()
    image1.id = "img1"
    image1.page_number = 1
    image1.bbox = (250, 10, 450, 200)
    image1.caption = "Test Image 1"
    image1.path = "images/test_image1.png"
    
    # Create tables
    table1 = MagicMock()
    table1.id = "table1"
    table1.page_number = 2
    table1.bbox = (50, 100, 400, 300)
    table1.data = [["Header 1", "Header 2"], ["Data 1", "Data 2"]]
    table1.caption = "Test Table 1"
    
    # Assign segments and images to pages
    page1.segments = [segment1, segment2]
    page1.images = [image1]
    page1.tables = []
    
    page2.segments = [segment3]
    page2.images = []
    page2.tables = [table1]
    
    # Add pages to document
    mock_document.pages = [page1, page2]
    
    # Add sentences
    mock_document.sentences = [
        MagicMock(id="sent1", text="This is the first segment.", segments=["seg1"]),
        MagicMock(id="sent2", text="This is the second segment.", segments=["seg2"]),
        MagicMock(id="sent3", text="This is a segment on page 2.", segments=["seg3"])
    ]
    
    # Create mock processor
    mock_processor = MagicMock()
    mock_processor.process.return_value = mock_document
    
    return mock_document, mock_processor

def setup_temp_dir():
    """
    Creates a temporary directory for testing.
    
    Returns:
        str: Path to the temporary directory
    """
    return Path(tempfile.mkdtemp())

def cleanup_temp_dir(temp_dir):
    """
    Cleans up the temporary directory.
    
    Args:
        temp_dir: Path to the temporary directory
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
def write_mock_config(config_path, output_format="json", output_file=None):
    """
    Write a mock configuration file.
    
    Args:
        config_path: Path to write the configuration file
        output_format: Format for output
        output_file: Output file path
        
    Returns:
        str: Path to the configuration file
    """
    config = {
        "input": {
            "files": ["test.pdf"]
        },
        "output": {
            "format": output_format
        }
    }
    
    if output_file:
        config["output"]["file"] = output_file
        
    with open(config_path, 'w') as f:
        json.dump(config, f)
        
    return config_path

# Automatically set up the mocks when the module is imported
setup_mock_docling() 