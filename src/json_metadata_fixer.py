#!/usr/bin/env python3
"""
JSON Metadata Fixer

This module fixes metadata issues in the parsed document JSON:
1. Ensures images are saved as external files and properly referenced
2. Generates proper hierarchical breadcrumbs based on section headers
3. Filters out furniture elements from context text
4. Ensures all element types are properly represented in the element map
"""

import json
import os
import base64
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import common utilities
from src.utils import remove_base64_data

# Set up logger
logger = logging.getLogger(__name__)

def fix_metadata(document_data: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Fix metadata issues in the parsed document.
    
    Args:
        document_data: The parsed document data
        output_dir: Output directory for saving external files
        
    Returns:
        Dict: The fixed document data
    """
    logger.info("Fixing metadata in parsed document...")
    
    # Create images directory if it doesn't exist
    images_dir = Path(output_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Fix image references and save as external files
    document_data = fix_image_references(document_data, images_dir)
    
    # Generate proper breadcrumbs based on section headers
    document_data = generate_breadcrumbs(document_data)
    
    # Filter furniture elements from context
    document_data = filter_furniture_from_context(document_data)
    
    # Save a copy of the fixed document with base64 data removed
    try:
        fixed_doc_path = Path(output_dir) / "fixed_metadata.json"
        # Create a copy with base64 data removed to reduce file size
        document_data_for_storage = remove_base64_data(document_data)
        with open(fixed_doc_path, 'w', encoding='utf-8') as f:
            json.dump(document_data_for_storage, f, indent=2)
        logger.info(f"Saved fixed metadata document to {fixed_doc_path}")
    except Exception as e:
        logger.warning(f"Failed to save fixed metadata JSON: {e}")
    
    return document_data

def fix_image_references(document_data: Dict[str, Any], images_dir: Path) -> Dict[str, Any]:
    """
    Ensure images are saved as external files and properly referenced.
    
    Args:
        document_data: The parsed document data
        images_dir: Directory to save image files
        
    Returns:
        Dict: The document data with fixed image references
    """
    logger.info("Fixing image references...")
    
    # Get document filename for use in image filenames
    doc_filename = os.path.basename(document_data.get("source_metadata", {}).get("filename", "document"))
    doc_id = Path(doc_filename).stem
    
    # Process pictures elements
    if "pictures" in document_data:
        for i, picture in enumerate(document_data["pictures"]):
            # Check if picture has data URI
            if "data" in picture:
                # Extract image data
                image_data_uri = picture["data"]
                
                # Extract image format and data
                if "," in image_data_uri:
                    header, encoded_data = image_data_uri.split(",", 1)
                    # Determine image format from header
                    image_format = "png"  # Default
                    if "image/jpeg" in header:
                        image_format = "jpg"
                    elif "image/png" in header:
                        image_format = "png"
                    elif "image/gif" in header:
                        image_format = "gif"
                    
                    # Decode base64 data
                    try:
                        image_data = base64.b64decode(encoded_data)
                        
                        # Generate unique filename
                        image_filename = f"{doc_id}_image_{i}.{image_format}"
                        image_path = images_dir / image_filename
                        
                        # Save image file
                        with open(image_path, "wb") as f:
                            f.write(image_data)
                        
                        # Update picture with external file reference
                        picture["external_file"] = str(image_path.relative_to(Path(images_dir).parent))
                        
                        # Remove inline data to save space
                        del picture["data"]
                        
                        logger.debug(f"Saved image to {image_path}")
                    except Exception as e:
                        logger.error(f"Error processing image data: {e}")
    
    # Update references in element map
    if "element_map" in document_data:
        for element_id, element in document_data["element_map"].items():
            if element.get("self_ref", "").startswith("#/pictures/"):
                picture_index = int(element["self_ref"].split("/")[-1])
                if "pictures" in document_data and picture_index < len(document_data["pictures"]):
                    picture = document_data["pictures"][picture_index]
                    if "external_file" in picture:
                        element["external_file"] = picture["external_file"]
                        
                        # Add to metadata if present
                        if "extracted_metadata" in element:
                            element["extracted_metadata"]["external_files"] = picture["external_file"]
    
    return document_data

def generate_breadcrumbs(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate proper hierarchical breadcrumbs based on section headers.
    
    Args:
        document_data: The parsed document data
        
    Returns:
        Dict: The document data with fixed breadcrumbs
    """
    logger.info("Generating hierarchical breadcrumbs...")
    
    # Extract section headers and their hierarchy levels
    headers = []
    
    # Process texts elements to find section headers
    if "texts" in document_data:
        for i, text in enumerate(document_data["texts"]):
            # Check if text is a section header
            if text.get("label") in ["section_header", "header", "heading", "section_title"]:
                # Determine level from font size or other attributes
                level = determine_header_level(text)
                text_content = text.get("text", "").strip()
                if text_content:
                    headers.append({
                        "id": i,
                        "text": text_content,
                        "level": level,
                        "ref": f"#/texts/{i}"
                    })
    
    # Build breadcrumb paths for each element
    if "element_map" in document_data:
        for element_id, element in document_data["element_map"].items():
            # Skip furniture elements for breadcrumbs
            if element.get("content_layer") == "furniture":
                continue
                
            # Find preceding headers for this element
            element_position = get_element_position(element, document_data)
            breadcrumb_path = build_breadcrumb_path(headers, element_position)
            
            # Update breadcrumb in element and metadata
            if breadcrumb_path and "extracted_metadata" in element:
                # Update the breadcrumb in special_field2
                element["extracted_metadata"]["special_field2"] = breadcrumb_path
                
                # Update the breadcrumb in metadata if it exists
                if "metadata" in element["extracted_metadata"]:
                    element["extracted_metadata"]["metadata"]["breadcrumb"] = breadcrumb_path
                
                # Update the breadcrumb in special_field1 if it exists and contains breadcrumb info
                if "special_field1" in element["extracted_metadata"]:
                    # Check if special_field1 contains a breadcrumb entry
                    special_field1 = element["extracted_metadata"]["special_field1"]
                    if "'breadcrumb':" in special_field1:
                        # Extract the current breadcrumb value
                        current_breadcrumb = element["extracted_metadata"].get("special_field2", "")
                        # Replace the breadcrumb value with the new one
                        element["extracted_metadata"]["special_field1"] = special_field1.replace(
                            f"'breadcrumb': '{current_breadcrumb}'",
                            f"'breadcrumb': '{breadcrumb_path}'"
                        )
    
    return document_data

def determine_header_level(text: Dict[str, Any]) -> int:
    """
    Determine the header level based on text attributes.
    
    Args:
        text: The text element
        
    Returns:
        int: Header level (1 for highest, increasing for sub-levels)
    """
    # Default level
    level = 1
    
    # Check for explicit level in text label
    label = text.get("label", "")
    if re.match(r"h\d", label, re.IGNORECASE):
        try:
            level = int(label[1:])
            return level
        except ValueError:
            pass
    
    # Check font size if available (larger = higher level)
    if "font_size" in text:
        font_size = float(text["font_size"])
        # Map font sizes to levels (adjust thresholds as needed)
        if font_size >= 20:  # Main title / document title - keep at level 1
            level = 1
        elif font_size >= 18:  # Major section headers
            level = 2
        elif font_size >= 16:  # Subsections
            level = 3
        elif font_size >= 14:  # Sub-subsections
            level = 4
        else:  # Even smaller headers
            level = 5
    
    # Check if bold
    is_bold = text.get("is_bold", False) or text.get("bold", False)
    if is_bold and level > 1:
        level -= 1  # Bold text is likely a higher level
    
    return level

def get_element_position(element: Dict[str, Any], document_data: Dict[str, Any]) -> int:
    """
    Determine the position of an element in the document sequence.
    
    Args:
        element: The element to find
        document_data: The document data
        
    Returns:
        int: Position index, or -1 if not found
    """
    # Get the element's self_ref
    element_ref = element.get("self_ref")
    
    if not element_ref:
        return -1
    
    # Check if element has a position in body.elements
    if "body" in document_data and "elements" in document_data["body"]:
        for i, body_element in enumerate(document_data["body"]["elements"]):
            if body_element.get("$ref") == element_ref:
                return i
    
    # If not found in body elements, try to determine position from the reference number
    if element_ref and element_ref.startswith("#/texts/"):
        try:
            # Extract the index from the ref, e.g., "#/texts/5" -> 5
            element_index = int(element_ref.split("/")[-1])
            return element_index
        except (ValueError, IndexError):
            pass
            
    return -1

def build_breadcrumb_path(headers: List[Dict[str, Any]], element_position: int) -> str:
    """
    Build a hierarchical breadcrumb path for an element based on preceding headers.
    
    Args:
        headers: List of section headers
        element_position: Position of the element in the document
        
    Returns:
        str: Hierarchical breadcrumb path
    """
    if element_position < 0:
        return ""
    
    # Filter headers that precede this element
    preceding_headers = [h for h in headers if h["id"] <= element_position]
    
    if not preceding_headers:
        return ""
    
    # Create a dictionary to store the most recent header at each level
    header_levels = {}
    
    # Sort headers by position (to process them in document order)
    preceding_headers.sort(key=lambda h: h["id"])
    
    # Process headers in order of appearance in the document
    for header in preceding_headers:
        level = header["level"]
        # Store the header text at its level
        header_levels[level] = header["text"]
        
        # Remove any headers at deeper levels since they now belong to a new section
        deeper_levels = [l for l in header_levels.keys() if l > level]
        for deeper_level in deeper_levels:
            del header_levels[deeper_level]
    
    # Build breadcrumb by joining headers in order of increasing level
    breadcrumb_sections = []
    for level in sorted(header_levels.keys()):
        breadcrumb_sections.append(header_levels[level])
    
    # Join with the separator
    return " > ".join(breadcrumb_sections)

def filter_furniture_from_context(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter out furniture elements from context text.
    
    Args:
        document_data: The parsed document data
        
    Returns:
        Dict: The document data with filtered context
    """
    logger.info("Filtering furniture elements from context...")
    
    # Identify furniture elements
    furniture_texts = set()
    
    # Find furniture elements
    if "furniture" in document_data:
        for i, furniture in enumerate(document_data["furniture"]):
            if "text" in furniture:
                furniture_texts.add(furniture["text"].strip())
    
    # Process elements to filter furniture from context
    if "element_map" in document_data:
        for element_id, element in document_data["element_map"].items():
            if "extracted_metadata" in element and "metadata" in element["extracted_metadata"]:
                metadata = element["extracted_metadata"]["metadata"]
                
                # Filter context_before
                if "context_before" in metadata:
                    metadata["context_before"] = filter_context(metadata["context_before"], furniture_texts)
                    # Update special_field1 to match the filtered context
                    if "special_field1" in element["extracted_metadata"]:
                        element["extracted_metadata"]["special_field1"] = element["extracted_metadata"]["special_field1"].replace(
                            f"'context_before': '{metadata.get('context_before', '')}'",
                            f"'context_before': '{metadata['context_before']}'"
                        )
                
                # Filter context_after
                if "context_after" in metadata:
                    metadata["context_after"] = filter_context(metadata["context_after"], furniture_texts)
                    # Update special_field1 to match the filtered context
                    if "special_field1" in element["extracted_metadata"]:
                        element["extracted_metadata"]["special_field1"] = element["extracted_metadata"]["special_field1"].replace(
                            f"'context_after': '{metadata.get('context_after', '')}'",
                            f"'context_after': '{metadata['context_after']}'"
                        )
    
    return document_data

def filter_context(context: str, furniture_texts: set) -> str:
    """
    Filter furniture text from context string.
    
    Args:
        context: The context text
        furniture_texts: Set of furniture text strings to filter out
        
    Returns:
        str: Filtered context text
    """
    if not context:
        return context
    
    filtered_context = context
    
    # Remove each furniture text from context
    for furniture in furniture_texts:
        if furniture and len(furniture) > 3:  # Avoid filtering very short strings
            filtered_context = filtered_context.replace(furniture, "")
    
    # Clean up any artifacts from removal
    filtered_context = re.sub(r'\s+', ' ', filtered_context).strip()
    
    return filtered_context 