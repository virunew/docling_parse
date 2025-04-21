"""
Breadcrumb Generator for DoclingDocument

This module provides functionality to generate hierarchical breadcrumbs for document
elements based on their section headers in the document structure.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_hierarchical_breadcrumb(
    element: Dict[str, Any], 
    flattened_sequence: List[Dict[str, Any]]
) -> str:
    """
    Generate a hierarchical breadcrumb for an element based on preceding section headers.
    
    Scans backward through the document sequence to find section headers at each level,
    and builds a complete breadcrumb path using full header text (not truncated).
    
    Args:
        element: The document element needing a breadcrumb
        flattened_sequence: The flattened document sequence in reading order
        
    Returns:
        A string representing the hierarchical breadcrumb path with '>' as separator
    """
    # Validate inputs
    if not element or not flattened_sequence:
        logger.warning("Invalid input provided to get_hierarchical_breadcrumb")
        return ""
    
    # Find the element's position in the sequence
    element_id = element.get('id', None)
    if not element_id:
        # Try to get self_ref if id is not available
        element_id = element.get('self_ref', None)
        
    if not element_id:
        logger.warning("Element has no id or self_ref, cannot determine position")
        return ""
    
    # Find the index of the element in the sequence
    element_index = -1
    for i, seq_element in enumerate(flattened_sequence):
        seq_id = seq_element.get('id', seq_element.get('self_ref', None))
        if seq_id == element_id:
            element_index = i
            break
    
    if element_index == -1:
        logger.warning(f"Element {element_id} not found in sequence")
        return ""
    
    # Initialize breadcrumb components for different heading levels
    # We'll store heading text at different levels (h1, h2, h3, etc.)
    breadcrumb_levels = {}
    
    # Scan backward to find section headers
    for i in range(element_index - 1, -1, -1):
        curr_element = flattened_sequence[i]
        
        # Check if the element is a section header
        element_type = curr_element.get('metadata', {}).get('type', '').lower()
        # Also check label if available
        element_label = curr_element.get('label', '')
        
        # Determine if this is a heading and at which level
        heading_level = None
        
        # First check if it's directly a heading element (h1-h6)
        for level in range(1, 7):
            if f"h{level}" == element_type:
                heading_level = level
                break
                
        # If not a direct heading, check for section_header with level attribute
        if heading_level is None and ('section_header' in element_type or 'section_header' in element_label):
            # Try to extract the level from metadata or attributes
            level_attr = curr_element.get('metadata', {}).get('level', 
                          curr_element.get('level', None))
            
            # Handle string or int level values
            if isinstance(level_attr, str) and level_attr.isdigit():
                heading_level = int(level_attr)
            elif isinstance(level_attr, int):
                heading_level = level_attr
            # If no level found, try to infer from the heading style or position
            elif element_type == 'section_header':
                # Look for additional indicators of the heading level
                font_size = curr_element.get('metadata', {}).get('font_size', 
                           curr_element.get('font_size', 0))
                font_weight = curr_element.get('metadata', {}).get('font_weight', 
                            curr_element.get('font_weight', ''))
                
                # Simple heuristic: assign level based on font attributes if available
                if font_size > 18 or font_weight == 'bold':
                    heading_level = 1
                elif font_size > 16:
                    heading_level = 2
                else:
                    heading_level = 3
            else:
                # Default to level 1 if we can't determine
                heading_level = 1
        
        # If we found a heading and haven't recorded one at this level yet
        if heading_level is not None and heading_level not in breadcrumb_levels:
            # Get the heading text
            heading_text = curr_element.get('text', '')
            if not heading_text:
                # Try alternative ways to get text
                heading_text = curr_element.get('content', 
                               curr_element.get('value', ''))
            
            if heading_text:
                # Store the first heading we find at each level (scanning backwards)
                breadcrumb_levels[heading_level] = heading_text.strip()
    
    # Build the breadcrumb string, ordered by heading level
    breadcrumb_parts = []
    for level in sorted(breadcrumb_levels.keys()):
        breadcrumb_parts.append(breadcrumb_levels[level])
    
    # Join with the separator and return
    breadcrumb = " > ".join(breadcrumb_parts)
    
    logger.debug(f"Generated breadcrumb: {breadcrumb}")
    return breadcrumb

def get_breadcrumb_with_fallback(
    element: Dict[str, Any], 
    flattened_sequence: List[Dict[str, Any]],
    document_title: str = ""
) -> str:
    """
    Get a breadcrumb with fallback to document title if no headers are found.
    
    Args:
        element: The document element needing a breadcrumb
        flattened_sequence: The flattened document sequence in reading order
        document_title: An optional document title to use as fallback
        
    Returns:
        A breadcrumb string, falling back to document title if no headers found
    """
    breadcrumb = get_hierarchical_breadcrumb(element, flattened_sequence)
    
    # If no breadcrumb was generated but we have a document title, use that
    if not breadcrumb and document_title:
        breadcrumb = document_title
        
    return breadcrumb

# Example usage
if __name__ == "__main__":
    # Sample elements and sequence for testing
    sample_sequence = [
        {"id": "h1_1", "text": "Document Title", "metadata": {"type": "h1"}, "label": "section_header"},
        {"id": "p1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}},
        {"id": "h2_1", "text": "Section 1", "metadata": {"type": "h2"}, "label": "section_header"},
        {"id": "p2", "text": "Paragraph 2", "metadata": {"type": "paragraph"}},
        {"id": "h3_1", "text": "Subsection 1.1", "metadata": {"type": "h3"}, "label": "section_header"},
        {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}},
    ]
    
    # Test for a paragraph in a subsection
    test_element = {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}}
    breadcrumb = get_hierarchical_breadcrumb(test_element, sample_sequence)
    print(f"Breadcrumb for paragraph in subsection: {breadcrumb}") 