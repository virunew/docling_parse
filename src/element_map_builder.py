"""
Element Map Builder for DoclingDocument

This module provides functionality to build a complete element map
from a DoclingDocument object by extracting content elements.
"""

import logging
import json
from typing import Dict, List, Tuple, Any, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_elements(docling_document: Any) -> dict:
    """
    Extract all elements from the DoclingDocument object and store them in a dictionary.
    
    Args:
        docling_document: The DoclingDocument object
        
    Returns:
        A dictionary mapping element IDs to their corresponding element objects
    """
    element_map = {}
    
    # Log document metadata
    logger.info(f"Document name: {getattr(docling_document, 'name', 'Unknown')}")
    logger.info(f"Document pages: {len(getattr(docling_document, 'pages', []))}")
    
    # Process all pages in the document
    for i, page in enumerate(getattr(docling_document, 'pages', [])):
        page_number = i + 1
        page_id = f"page_{page_number}"
        
        # Add the page itself to the element map
        page_dict = {
            "id": page_id,
            "metadata": {
                "type": "page",
                "page_number": page_number
            },
            "size": getattr(page, 'size', None)
        }
        element_map[page_id] = page_dict
        
        # Process text segments
        segments = getattr(page, 'segments', [])
        if segments:
            logger.info(f"Processing {len(segments)} segments on page {page_number}")
            for j, segment in enumerate(segments):
                segment_id = f"{page_id}_segment_{j+1}"
                segment_dict = {
                    "id": segment_id,
                    "metadata": {
                        "type": "paragraph",
                        "page_number": page_number
                    },
                    "text": getattr(segment, 'text', ''),
                    "bounds": getattr(segment, 'bounds', None),
                    "parent_id": page_id
                }
                element_map[segment_id] = segment_dict
        
        # Process tables
        tables = getattr(page, 'tables', [])
        if tables:
            logger.info(f"Processing {len(tables)} tables on page {page_number}")
            for j, table in enumerate(tables):
                table_id = f"{page_id}_table_{j+1}"
                # Convert table to dictionary with relevant properties
                table_dict = {
                    "id": table_id,
                    "metadata": {
                        "type": "table",
                        "page_number": page_number
                    },
                    "bounds": getattr(table, 'bounds', None),
                    "cells": [],
                    "parent_id": page_id
                }
                
                # Process cells if available
                cells = getattr(table, 'cells', [])
                for k, cell in enumerate(cells):
                    cell_dict = {
                        "row": getattr(cell, 'row', 0),
                        "col": getattr(cell, 'col', 0),
                        "rowspan": getattr(cell, 'rowspan', 1),
                        "colspan": getattr(cell, 'colspan', 1),
                        "text": getattr(cell, 'text', ''),
                        "bounds": getattr(cell, 'bounds', None)
                    }
                    table_dict["cells"].append(cell_dict)
                
                element_map[table_id] = table_dict
        
        # Process pictures
        pictures = getattr(page, 'pictures', [])
        if pictures:
            logger.info(f"Processing {len(pictures)} pictures on page {page_number}")
            for j, picture in enumerate(pictures):
                picture_id = f"{page_id}_picture_{j+1}"
                picture_dict = {
                    "id": picture_id,
                    "metadata": {
                        "type": "picture",
                        "page_number": page_number
                    },
                    "bounds": getattr(picture, 'bounds', None),
                    "image_path": getattr(picture, 'image_path', None),
                    "parent_id": page_id
                }
                element_map[picture_id] = picture_dict
    
    logger.info(f"Extracted {len(element_map)} elements from document structure")
    return element_map

def build_element_map(docling_document: Any) -> dict:
    """
    Build a complete element map from a DoclingDocument object.
    
    Args:
        docling_document: The DoclingDocument object
        
    Returns:
        A dictionary mapping element IDs to their corresponding element objects
    """
    # Extract all elements from the document
    logger.info("Step 1: Extracting elements from DoclingDocument")
    element_map = extract_elements(docling_document)
    
    logger.info(f"Built element map with {len(element_map)} elements")
    return element_map

# Example usage
if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python element_map_builder.py <path_to_docling_document.json>")
        sys.exit(1)
        
    # For standalone testing, we'd need to load a DoclingDocument from file
    # This would require the docling library
    try:
        from docling_core.types.doc import DoclingDocument
        
        # Load the DoclingDocument
        docling_document = DoclingDocument.from_file(sys.argv[1])
        
        # Build the element map
        element_map = build_element_map(docling_document)
        
        # Output the element map
        output_file = 'element_map_debug.json'
        with open(output_file, 'w') as f:
            json.dump(element_map, f, indent=2)
        print(f"Element map saved to {output_file}")
        
    except ImportError:
        print("Could not import docling library. This script requires docling to be installed.")
        sys.exit(1) 