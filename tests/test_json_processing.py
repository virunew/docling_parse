#!/usr/bin/env python3
"""
Test script for validating the element_map_builder fixes with both dictionary
and TextItem style objects.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the parent directory to path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.element_map_builder import ElementMapBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleTextItem:
    """A simple class that simulates a TextItem without recursion issues."""
    def __init__(self, self_ref=None, content=None, type_name=None, elements=None):
        self.self_ref = self_ref
        self.content = content
        self.type_name = type_name
        self.elements = elements or []
        
    def to_dict(self):
        """Convert to dictionary for serialization"""
        result = {}
        if self.self_ref is not None:
            result["self_ref"] = self.self_ref
        if self.content is not None:
            result["content"] = self.content
        if self.type_name is not None:
            result["type_name"] = self.type_name
        if self.elements:
            result["elements"] = self.elements
        return result
        
    def __str__(self):
        return f"SimpleTextItem(self_ref={self.self_ref}, type={self.type_name})"

def create_mock_docling_document():
    """
    Create a mock DoclingDocument with SimpleTextItem objects for testing
    """
    # Create text items
    title = SimpleTextItem(
        self_ref="text1", 
        content="Sample Document Title",
        type_name="text"
    )
    
    paragraph = SimpleTextItem(
        self_ref="text2",
        content="This is a sample paragraph of text.",
        type_name="text"
    )
    
    # Create a table
    table = SimpleTextItem(
        self_ref="table1",
        content={"headers": ["Column 1", "Column 2"], "rows": [["Data 1", "Data 2"]]},
        type_name="table"
    )
    
    # Create an image
    image = SimpleTextItem(
        self_ref="image1",
        content="[Image data would be here]",
        type_name="picture"
    )
    
    # Create the document body with references to elements
    doc_body = SimpleTextItem(
        self_ref="body",
        type_name="body",
        elements=["text1", "text2", "table1", "image1"]
    )
    
    # Create document dictionary with all elements
    document = {
        "elements": {
            "text1": title,
            "text2": paragraph,
            "table1": table,
            "image1": image,
            "body": doc_body
        },
        "body_ref": "body"
    }
    
    return document

def main():
    """Main test function to verify element_map_builder fixes"""
    logger.info("Starting element_map_builder test with TextItem objects")
    
    # Create mock document
    mock_document = create_mock_docling_document()
    
    # Test with TextItem objects
    logger.info("Building element map from mock DoclingDocument with TextItem objects")
    builder = ElementMapBuilder()
    
    # Try to build the element map
    try:
        element_map = builder.build_element_map(mock_document)
        
        # Check if elements were correctly added to the element map
        logger.info(f"Element map built with {len(element_map.get('elements', {}))} elements")
        logger.info(f"Flattened sequence contains {len(element_map.get('flattened_sequence', []))} elements")
        
        # Verify we have the expected number of elements
        expected_map_elements = 5  # 2 texts, 1 table, 1 image, 1 body
        expected_seq_elements = 4  # 2 texts, 1 table, 1 image
        if (len(element_map.get('elements', {})) == expected_map_elements and 
            len(element_map.get('flattened_sequence', [])) == expected_seq_elements):
            logger.info(f"SUCCESS: Found expected {expected_seq_elements} elements in sequence")
        else:
            logger.error(f"FAILURE: Expected {expected_map_elements} elements in map and {expected_seq_elements} in sequence but got "
                        f"{len(element_map.get('elements', {}))} in map and "
                        f"{len(element_map.get('flattened_sequence', []))} in sequence")
        
        # Save the result for inspection
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Convert elements to dictionaries
        serializable_map = {
            "elements": {},
            "flattened_sequence": element_map.get('flattened_sequence', []),
            "document_info": element_map.get('document_info', {})
        }
        
        for k, v in element_map.get('elements', {}).items():
            if hasattr(v, 'to_dict'):
                serializable_map["elements"][k] = v.to_dict()
            else:
                serializable_map["elements"][k] = v
        
        with open(output_dir / "element_map_test.json", "w") as f:
            json.dump(serializable_map, f, indent=2)
            logger.info(f"Saved element map to {output_dir / 'element_map_test.json'}")
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 