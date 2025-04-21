"""
Content Type Identification and Extraction

This module provides functions to identify and extract different types of content
from document elements, including text, tables, and images. It also provides utility
functions to find contextual information for elements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_content(element: Dict[str, Any]) -> str:
    """
    Extract text content from a text element.
    
    Args:
        element: The document element containing text
        
    Returns:
        The extracted text content as a string
    """
    # Try different fields where text might be stored
    text = element.get('text', '')
    
    # If no text field, try content or value fields
    if not text:
        text = element.get('content', element.get('value', ''))
    
    return text.strip() if text else ''

def extract_table_content(element: Dict[str, Any]) -> List[List[str]]:
    """
    Extract table content as a grid structure.
    
    Args:
        element: The document element containing a table
        
    Returns:
        A list of rows, where each row is a list of cell text values
    """
    # Get cells from the element
    cells = element.get('cells', [])
    
    if not cells:
        logger.warning(f"No cells found in table element: {element.get('id', 'unknown')}")
        return []
    
    # Find the dimensions of the table
    max_row = 0
    max_col = 0
    
    for cell in cells:
        row = cell.get('row', 0)
        col = cell.get('col', 0)
        rowspan = cell.get('rowspan', 1)
        colspan = cell.get('colspan', 1)
        
        max_row = max(max_row, row + rowspan)
        max_col = max(max_col, col + colspan)
    
    # Initialize the table grid
    table_grid = [[''] * max_col for _ in range(max_row)]
    
    # Fill in the table with cell values
    for cell in cells:
        row = cell.get('row', 0)
        col = cell.get('col', 0)
        rowspan = cell.get('rowspan', 1)
        colspan = cell.get('colspan', 1)
        text = cell.get('text', '').strip()
        
        # Fill in the cell and any spanned cells
        for r in range(row, min(row + rowspan, max_row)):
            for c in range(col, min(col + colspan, max_col)):
                table_grid[r][c] = text
    
    return table_grid

def extract_image_content(element: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract image data and metadata from an image element.
    
    Args:
        element: The document element containing an image
        
    Returns:
        A dictionary with image information including path and metadata
    """
    image_data = {
        'image_path': element.get('image_path', None),
        'bounds': element.get('bounds', None),
        'description': element.get('description', ''),
        'metadata': element.get('metadata', {})
    }
    
    return image_data

def is_furniture(element: Dict[str, Any]) -> bool:
    """
    Determine if an element is document furniture (headers, footers, etc.).
    
    Args:
        element: The document element to check
        
    Returns:
        True if the element is furniture, False if it's main body content
    """
    # Check content_layer attribute if available
    content_layer = element.get('content_layer', None)
    if content_layer is not None:
        return content_layer.lower() == 'furniture'
    
    # Check metadata type for common furniture elements
    element_type = element.get('metadata', {}).get('type', '').lower()
    element_label = element.get('label', '').lower()
    
    furniture_types = [
        'header', 'footer', 'page_header', 'page_footer',
        'footnote', 'page_number', 'running_header', 'running_footer',
        'watermark', 'background'
    ]
    
    for furniture_type in furniture_types:
        if furniture_type in element_type or furniture_type in element_label:
            return True
    
    return False

def find_sibling_text_in_sequence(
    element: Dict[str, Any], 
    flattened_sequence: List[Dict[str, Any]],
    context_chars: int = 50
) -> Tuple[str, str]:
    """
    Find text before and after the element in the document sequence.
    
    Args:
        element: The document element to find context for
        flattened_sequence: The flattened document sequence in reading order
        context_chars: Number of characters to include before and after
        
    Returns:
        A tuple of (text_before, text_after) with the context snippets
    """
    # Find the element's position in the sequence
    element_id = element.get('id', element.get('self_ref', None))
    
    if not element_id or not flattened_sequence:
        return ('', '')
    
    # Find the index of the element in the sequence
    element_index = -1
    for i, seq_element in enumerate(flattened_sequence):
        seq_id = seq_element.get('id', seq_element.get('self_ref', None))
        if seq_id == element_id:
            element_index = i
            break
    
    if element_index == -1:
        logger.warning(f"Element {element_id} not found in sequence")
        return ('', '')
    
    # Initialize text before and after
    text_before = ''
    text_after = ''
    
    # Get text before the element
    i = element_index - 1
    while i >= 0 and len(text_before) < context_chars:
        curr_element = flattened_sequence[i]
        curr_text = extract_text_content(curr_element)
        if curr_text:
            text_before = curr_text + ' ' + text_before
        i -= 1
    
    # Get text after the element
    i = element_index + 1
    while i < len(flattened_sequence) and len(text_after) < context_chars:
        curr_element = flattened_sequence[i]
        curr_text = extract_text_content(curr_element)
        if curr_text:
            text_after = text_after + ' ' + curr_text
        i += 1
    
    # Trim to the specified character count, but preserve complete words
    if len(text_before) > context_chars:
        # Find the first space after context_chars characters from the end
        truncate_pos = max(len(text_before) - context_chars, 0)
        space_pos = text_before.find(' ', truncate_pos)
        if space_pos != -1:
            text_before = '...' + text_before[space_pos:]
        else:
            text_before = '...' + text_before[-context_chars:]
    
    if len(text_after) > context_chars:
        # Find the last space before context_chars
        space_pos = text_after.rfind(' ', 0, context_chars)
        if space_pos != -1:
            text_after = text_after[:space_pos] + '...'
        else:
            text_after = text_after[:context_chars] + '...'
    
    return (text_before.strip(), text_after.strip())

def get_captions(
    element: Dict[str, Any], 
    flattened_sequence: List[Dict[str, Any]],
    max_distance: int = 2
) -> Optional[str]:
    """
    Find and extract caption text for tables and images.
    
    Args:
        element: The document element (table or image) to find caption for
        flattened_sequence: The flattened document sequence in reading order
        max_distance: Maximum number of elements to search before/after
        
    Returns:
        The caption text if found, None otherwise
    """
    # Check if this is a table or image element
    element_type = element.get('metadata', {}).get('type', '').lower()
    if not ('table' in element_type or 'picture' in element_type or 'image' in element_type):
        return None
    
    # Find the element's position in the sequence
    element_id = element.get('id', element.get('self_ref', None))
    
    if not element_id or not flattened_sequence:
        return None
    
    # Find the index of the element in the sequence
    element_index = -1
    for i, seq_element in enumerate(flattened_sequence):
        seq_id = seq_element.get('id', seq_element.get('self_ref', None))
        if seq_id == element_id:
            element_index = i
            break
    
    if element_index == -1:
        logger.warning(f"Element {element_id} not found in sequence")
        return None
    
    # Look for captions before and after the element
    caption_indicators = ['caption', 'figure', 'fig', 'table', 'tbl']
    
    # Check elements before
    start_idx = max(0, element_index - max_distance)
    for i in range(start_idx, element_index):
        curr_element = flattened_sequence[i]
        
        # Check if the element is explicitly marked as a caption
        curr_type = curr_element.get('metadata', {}).get('type', '').lower()
        curr_label = curr_element.get('label', '').lower()
        
        is_caption = 'caption' in curr_type or 'caption' in curr_label
        
        # Check text content for caption indicators
        if not is_caption:
            text = extract_text_content(curr_element).lower()
            for indicator in caption_indicators:
                if indicator in text and len(text) < 200:  # Captions are typically short
                    is_caption = True
                    break
        
        if is_caption:
            return extract_text_content(curr_element)
    
    # Check elements after
    end_idx = min(len(flattened_sequence), element_index + max_distance + 1)
    for i in range(element_index + 1, end_idx):
        curr_element = flattened_sequence[i]
        
        # Check if the element is explicitly marked as a caption
        curr_type = curr_element.get('metadata', {}).get('type', '').lower()
        curr_label = curr_element.get('label', '').lower()
        
        is_caption = 'caption' in curr_type or 'caption' in curr_label
        
        # Check text content for caption indicators
        if not is_caption:
            text = extract_text_content(curr_element).lower()
            for indicator in caption_indicators:
                if indicator in text and len(text) < 200:  # Captions are typically short
                    is_caption = True
                    break
        
        if is_caption:
            return extract_text_content(curr_element)
    
    return None

# Example usage
if __name__ == "__main__":
    # Sample elements for testing
    text_element = {
        "id": "text_1", 
        "text": "This is a sample text element.", 
        "metadata": {"type": "paragraph"}
    }
    
    table_element = {
        "id": "table_1",
        "metadata": {"type": "table"},
        "cells": [
            {"row": 0, "col": 0, "text": "Header 1", "rowspan": 1, "colspan": 1},
            {"row": 0, "col": 1, "text": "Header 2", "rowspan": 1, "colspan": 1},
            {"row": 1, "col": 0, "text": "Cell 1", "rowspan": 1, "colspan": 1},
            {"row": 1, "col": 1, "text": "Cell 2", "rowspan": 1, "colspan": 1}
        ]
    }
    
    image_element = {
        "id": "image_1",
        "metadata": {"type": "picture"},
        "image_path": "/path/to/image.jpg",
        "bounds": {"x": 0, "y": 0, "width": 100, "height": 100}
    }
    
    # Test the functions
    print(f"Text content: {extract_text_content(text_element)}")
    print(f"Table content: {extract_table_content(table_element)}")
    print(f"Image data: {extract_image_content(image_element)}") 