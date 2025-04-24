"""
Metadata Extraction Module

This module provides functions to extract and process metadata from document elements,
including page numbers, bounding box coordinates, and other provenance information.
It also contains utilities for transforming and formatting metadata for database storage.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Import helper functions
from breadcrumb_generator import get_hierarchical_breadcrumb
from content_extractor import find_sibling_text_in_sequence, get_captions, extract_text_content

# Configure logging
logger = logging.getLogger(__name__)

def convert_bbox(bbox: Dict[str, Any], to_integers: bool = True) -> Dict[str, Any]:
    """
    Convert bounding box coordinates to the required format for database storage.
    
    Args:
        bbox: Dictionary with bounding box coordinates (expected keys: l, t, r, b)
        to_integers: Whether to convert the coordinates to integers
        
    Returns:
        Dictionary with standardized keys and optionally converted values:
        - coords_x: left (x) coordinate
        - coords_y: top (y) coordinate
        - coords_cx: width
        - coords_cy: height
    """
    if not bbox:
        logger.warning("Empty bounding box provided to convert_bbox")
        return {
            "coords_x": 0,
            "coords_y": 0,
            "coords_cx": 0,
            "coords_cy": 0
        }
    
    # Extract values with default fallbacks
    left = bbox.get('l', 0)
    top = bbox.get('t', 0)
    right = bbox.get('r', 0)
    bottom = bbox.get('b', 0)
    
    # Calculate width and height
    width = right - left
    height = bottom - top
    
    # Convert to integers if required
    if to_integers:
        left = int(left)
        top = int(top)
        width = int(width)
        height = int(height)
    
    # Create standardized dictionary
    converted_bbox = {
        "coords_x": left,
        "coords_y": top,
        "coords_cx": width,
        "coords_cy": height
    }
    
    return converted_bbox

def extract_page_number(element: Dict[str, Any]) -> Optional[int]:
    """
    Extract the page number from an element's provenance information.
    
    Args:
        element: The document element
        
    Returns:
        Page number as an integer, or None if not found
    """
    # Try different paths to find page number
    
    # First check in prov field if it exists
    prov = element.get('prov', {})
    if prov:
        page_num = prov.get('page_no', prov.get('page', None))
        if page_num is not None:
            try:
                return int(page_num)
            except (ValueError, TypeError):
                logger.warning(f"Invalid page number format: {page_num}")
    
    # Alternative: check in metadata
    metadata = element.get('metadata', {})
    page_num = metadata.get('page_no', metadata.get('page', None))
    if page_num is not None:
        try:
            return int(page_num)
        except (ValueError, TypeError):
            logger.warning(f"Invalid page number format in metadata: {page_num}")
    
    # If still not found, check top level element attributes
    page_num = element.get('page_no', element.get('page', None))
    if page_num is not None:
        try:
            return int(page_num)
        except (ValueError, TypeError):
            logger.warning(f"Invalid page number format in element: {page_num}")
    
    return None

def extract_image_metadata(element: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata specific to image elements.
    
    Args:
        element: The document element containing an image
        
    Returns:
        Dictionary with image-specific metadata
    """
    image_metadata = {}
    
    # Extract mimetype
    metadata = element.get('metadata', {})
    mimetype = metadata.get('mimetype', metadata.get('mime_type', 'image/png'))
    image_metadata['image_mimetype'] = mimetype
    
    # Extract dimensions
    bounds = element.get('bounds', {})
    if bounds:
        width = bounds.get('r', 0) - bounds.get('l', 0)
        height = bounds.get('b', 0) - bounds.get('t', 0)
    else:
        width = metadata.get('width', 0)
        height = metadata.get('height', 0)
    
    image_metadata['image_width'] = int(width) if width else 0
    image_metadata['image_height'] = int(height) if height else 0
    
    # Extract OCR text if available
    ocr_text = metadata.get('ocr_text', '')
    if ocr_text:
        image_metadata['image_ocr_text'] = ocr_text
    
    return image_metadata

def build_metadata_object(
    element: Dict[str, Any],
    flattened_sequence: List[Dict[str, Any]],
    context_chars: int = 100
) -> Dict[str, Any]:
    """
    Build a comprehensive metadata object for a document element.
    
    Args:
        element: The document element
        flattened_sequence: The flattened document sequence in reading order
        context_chars: Number of characters to include in context snippets
        
    Returns:
        Dictionary with complete metadata including:
        - breadcrumb: Hierarchical path to the element
        - page_no: Page number
        - bbox_raw: Original bounding box coordinates
        - caption: Caption text (for tables and images)
        - context_before/after: Text before and after the element
        - docling_label: Element type label
        - docling_ref: Element reference in the document
        - For images: mimetype, width, height, and OCR text
    """
    # Check if element is a dictionary
    if not isinstance(element, dict):
        logger.warning(f"Non-dictionary element received in build_metadata_object: {type(element)}")
        # Create a minimal metadata object
        return {
            'docling_label': 'unknown',
            'breadcrumb': 'unknown'
        }
    
    metadata = {}
    
    # Filter the flattened sequence to ensure only dictionary elements are processed
    filtered_sequence = [elem for elem in flattened_sequence if isinstance(elem, dict)]
    
    # Get hierarchical breadcrumb
    try:
        breadcrumb = get_hierarchical_breadcrumb(element, filtered_sequence)
        metadata['breadcrumb'] = breadcrumb
    except Exception as e:
        logger.warning(f"Error generating breadcrumb: {e}")
        metadata['breadcrumb'] = "unknown"
    
    # Get page number
    try:
        page_no = extract_page_number(element)
        if page_no is not None:
            metadata['page_no'] = page_no
    except Exception as e:
        logger.warning(f"Error extracting page number: {e}")
    
    # Get bounding box (raw format)
    try:
        bbox = element.get('bounds', {})
        if not bbox:
            # Try to get from metadata or prov
            element_metadata = element.get('metadata', {})
            bbox = element_metadata.get('bounds', {})
            
            if not bbox:
                prov = element.get('prov', {})
                bbox = prov.get('bbox', {})
        
        if bbox:
            metadata['bbox_raw'] = {
                'l': bbox.get('l', 0),
                't': bbox.get('t', 0),
                'r': bbox.get('r', 0),
                'b': bbox.get('b', 0)
            }
    except Exception as e:
        logger.warning(f"Error extracting bounding box: {e}")
    
    # Get caption for tables and images
    try:
        element_type = element.get('metadata', {}).get('type', '').lower()
        if 'table' in element_type or 'image' in element_type or 'picture' in element_type:
            caption = get_captions(element, filtered_sequence)
            if caption:
                metadata['caption'] = caption
    except Exception as e:
        logger.warning(f"Error extracting caption: {e}")
    
    # Get context snippets (before and after)
    try:
        context_before, context_after = find_sibling_text_in_sequence(
            element, filtered_sequence, context_chars=context_chars
        )
        
        if context_before:
            metadata['context_before'] = context_before
        
        if context_after:
            metadata['context_after'] = context_after
    except Exception as e:
        logger.warning(f"Error extracting context: {e}")
    
    # Get docling label and reference
    element_label = element.get('label', '')
    if element_label:
        metadata['docling_label'] = element_label
    
    element_ref = element.get('self_ref', element.get('id', ''))
    if element_ref:
        metadata['docling_ref'] = element_ref
    
    # Add image-specific metadata if this is an image
    try:
        if 'image' in element_type or 'picture' in element_type:
            image_metadata = extract_image_metadata(element)
            metadata.update(image_metadata)
    except Exception as e:
        logger.warning(f"Error extracting image metadata: {e}")
    
    return metadata

def extract_full_metadata(
    element: Dict[str, Any],
    flattened_sequence: List[Dict[str, Any]],
    doc_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract full metadata for a document element, combining all metadata sources.
    
    Args:
        element: The document element
        flattened_sequence: The flattened document sequence in reading order
        doc_info: Optional document-level information
        
    Returns:
        Dictionary with complete metadata ready for database storage
    """
    # Log the element type for debugging
    logger.debug(f"Extracting metadata for element type: {type(element)}")
    
    # Check if element is a dictionary
    if not isinstance(element, dict):
        logger.warning(f"Non-dictionary element received: {type(element)}")
        # Return minimal metadata to avoid errors
        return {
            "coords_x": 0, "coords_y": 0, "coords_cx": 0, "coords_cy": 0,
            "master_index": 0, "master_index2": None,
            "special_field1": "{}", "special_field2": "unknown",
            "text_search": "", "metadata": {}
        }
    
    # Log element keys for debugging
    if hasattr(element, "keys"):
        logger.debug(f"Element keys: {list(element.keys())}")
    
    # Filter the flattened sequence to ensure only dictionary elements are processed
    filtered_sequence = [elem for elem in flattened_sequence if isinstance(elem, dict)]
    logger.debug(f"Filtered sequence has {len(filtered_sequence)} elements")
    
    try:
        # Build the basic metadata object
        metadata = build_metadata_object(element, filtered_sequence)
        
        # Get the converted bounding box
        bbox_raw = metadata.get('bbox_raw', {})
        converted_bbox = convert_bbox(bbox_raw, to_integers=True)
        
        # Start with the converted bounding box
        result = converted_bbox.copy()
        
        # Add page number as master_index
        result['master_index'] = metadata.get('page_no', 0)
        result['master_index2'] = None
        
        # Add original metadata as special_field1 (as JSON string)
        # In a real implementation, this would be properly JSON serialized
        result['special_field1'] = str(metadata)
        
        # Add breadcrumb as special_field2
        result['special_field2'] = metadata.get('breadcrumb', '')
        
        # Set text_search to caption or actual text content for search indexing
        caption = metadata.get('caption', '')
        if caption:
            result['text_search'] = caption
        else:
            try:
                result['text_search'] = extract_text_content(element)
            except Exception as text_err:
                logger.warning(f"Error extracting text content: {text_err}")
                result['text_search'] = ""
        
        # Add document info if provided
        if doc_info:
            # Add file_type from doc mimetype
            result['file_type'] = doc_info.get('mimetype', 'application/pdf')
            # Add file_source from doc filename
            result['file_source'] = doc_info.get('filename', '')
        
        # Set the full metadata object
        result['metadata'] = metadata
        
        return result
        
    except Exception as e:
        logger.exception(f"Error in extract_full_metadata: {e}")
        # Return minimal metadata to avoid errors
        return {
            "coords_x": 0, "coords_y": 0, "coords_cx": 0, "coords_cy": 0,
            "master_index": 0, "master_index2": None,
            "special_field1": "{}", "special_field2": "error",
            "text_search": "", "metadata": {"error": str(e)}
        }

# Example usage
if __name__ == "__main__":
    # Sample elements for testing
    bbox_example = {'l': 56.7, 't': 115.2, 'r': 555.3, 'b': 309.8}
    converted = convert_bbox(bbox_example)
    print(f"Converted bbox: {converted}")
    
    # Example of how to use these functions in the actual application:
    """
    # Example flow in application:
    # 1. Get element from document
    element = document.get_element(element_id)
    
    # 2. Get flattened sequence for context
    flattened_sequence = get_flattened_body_sequence(element_map, document_body)
    
    # 3. Extract metadata
    metadata = extract_full_metadata(
        element, 
        flattened_sequence, 
        doc_info={
            'filename': 'example.pdf',
            'mimetype': 'application/pdf'
        }
    )
    
    # 4. Use the metadata in database record or JSON output
    """ 