"""
Document Sequence Flattener for DoclingDocument

This module provides functionality to flatten a document structure into a 
linear sequence while preserving the correct reading order of elements.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

def get_flattened_body_sequence(element_map: Dict[str, Any], document_body: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten the document body into a linear sequence preserving the correct reading order.
    
    Args:
        element_map: A dictionary mapping element IDs to their corresponding element objects
        document_body: The document body structure containing ordered element references
        
    Returns:
        A list of elements in the correct reading sequence
    """
    # Validate inputs
    if not element_map:
        logger.warning("Empty element map provided to get_flattened_body_sequence")
        return []
    
    if not document_body:
        logger.warning("Empty document body provided to get_flattened_body_sequence")
        return []
    
    logger.info(f"Flattening document sequence with {len(document_body)} body elements")
    
    # Create a list to store the flattened sequence
    flattened_sequence = []
    
    # Helper function to recursively process elements and their children
    def process_element(element_ref: Dict[str, Any]) -> None:
        # Handle case where element reference might be None or invalid
        if not element_ref:
            return
        
        # Get the reference path
        ref_path = element_ref.get('$ref', None)
        
        # Skip if there's no reference
        if not ref_path:
            return
        
        # Try to find the actual element in the element map
        # Remove the prefix '#/' if it exists
        clean_ref = ref_path[2:] if ref_path.startswith('#/') else ref_path
        
        # Handle potential path format variations (convert to path parts)
        path_parts = clean_ref.split('/')
        
        # Try direct lookup first
        element = element_map.get(ref_path, None)
        
        # If direct lookup failed, try with the clean reference
        if element is None:
            element = element_map.get(clean_ref, None)
        
        # If still not found, log warning and return
        if element is None:
            logger.warning(f"Could not resolve reference: {ref_path}")
            return
        
        # Add the element to the flattened sequence
        flattened_sequence.append(element)
        
        # Process children if they exist
        children = element.get('children', [])
        if children:
            logger.debug(f"Processing {len(children)} children of element {ref_path}")
            for child in children:
                process_element(child)
    
    # Process each element in the document body
    for body_element in document_body:
        process_element(body_element)
    
    logger.info(f"Flattened sequence created with {len(flattened_sequence)} elements")
    
    return flattened_sequence

def get_element_by_reference(element_map: Dict[str, Any], ref_path: str) -> Optional[Dict[str, Any]]:
    """
    Get an element from the element map using its reference path.
    
    Args:
        element_map: A dictionary mapping element IDs to their corresponding element objects
        ref_path: The reference path to lookup
        
    Returns:
        The element object if found, None otherwise
    """
    # Remove the prefix '#/' if it exists
    clean_ref = ref_path[2:] if ref_path.startswith('#/') else ref_path
    
    # Try direct lookup first
    element = element_map.get(ref_path, None)
    
    # If direct lookup failed, try with the clean reference
    if element is None:
        element = element_map.get(clean_ref, None)
    
    return element

def sort_sequence_by_position(sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort a sequence of elements by their position in the document (top to bottom, left to right).
    
    Args:
        sequence: A list of element objects
        
    Returns:
        The sorted list of elements
    """
    def get_position(element):
        # Extract the position from the element's metadata or bounds
        bounds = element.get('bounds', None)
        if not bounds:
            metadata = element.get('metadata', {})
            bounds = metadata.get('bounds', {'t': float('inf'), 'l': float('inf')})
        
        # Use top (t) as primary sort key and left (l) as secondary
        return (bounds.get('t', float('inf')), bounds.get('l', float('inf')))
    
    # Sort the sequence by position
    sorted_sequence = sorted(sequence, key=get_position)
    
    return sorted_sequence

# Example usage
if __name__ == "__main__":
    # Just an example - this would be run as part of a larger application
    sample_element_map = {
        "texts/0": {"id": "text_1", "text": "Header", "children": []},
        "texts/1": {"id": "text_2", "text": "Paragraph 1", "children": []},
        "pictures/0": {"id": "pic_1", "image_data": "...", "children": []}
    }
    
    sample_body = [
        {"$ref": "texts/0"},
        {"$ref": "texts/1"},
        {"$ref": "pictures/0"}
    ]
    
    flattened = get_flattened_body_sequence(sample_element_map, sample_body)
    print(f"Flattened sequence has {len(flattened)} elements") 