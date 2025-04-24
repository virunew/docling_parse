"""
Format Standardized Output Module

This module provides functionality to convert the document data into the standardized output
format required by the PRD, with chunks and furniture arrays mapping to the fusa_library schema.
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime
import hashlib

from logger_config import logger

def is_furniture(element):
    """
    Determine if an element is furniture based on its content_layer attribute.
    
    Args:
        element: Document element to check
        
    Returns:
        bool: True if the element is furniture, False otherwise
    """
    # Furniture elements typically have a content_layer attribute of "furniture"
    return element.get("content_layer") == "furniture" or element.get("layer") == "furniture"

def extract_content_type(element):
    """
    Determine the content type of an element.
    
    Args:
        element: Document element
        
    Returns:
        str: "text", "table", "image", or "unknown"
    """
    element_type = element.get("type", "").lower()
    
    if element_type == "text":
        return "text"
    elif element_type == "table":
        return "table"
    elif element_type == "picture" or element_type == "image":
        return "image"
    
    # Try to infer from other attributes
    if "text_content" in element or "text" in element:
        return "text"
    elif "table_content" in element or "cells" in element:
        return "table"
    elif "image_content" in element or "data_uri" in element:
        return "image"
    
    return "unknown"

def format_text_block(element, breadcrumb=""):
    """
    Format the text block with breadcrumb and content.
    
    Args:
        element: Document element
        breadcrumb: Hierarchical breadcrumb string
        
    Returns:
        str: Formatted text block
    """
    # Extract the text content from the element
    text_content = element.get("text_content", element.get("text", ""))
    
    # For images, include preceding text, image text, and succeeding text
    if extract_content_type(element) == "image":
        preceding_text = element.get("context_before", "")
        image_text = element.get("ocr_text", element.get("extracted_metadata", {}).get("image_ocr_text", ""))
        succeeding_text = element.get("context_after", "")
        
        text_block = f"{breadcrumb}\n\n{preceding_text}\n\n[Image Text: {image_text}]\n\n{succeeding_text}"
    else:
        text_block = f"{breadcrumb}\n\n{text_content}"
    
    return text_block

def format_table_block(element):
    """
    Format the table content as a JSON string.
    
    Args:
        element: Table element
        
    Returns:
        str: JSON string of table grid or None
    """
    if extract_content_type(element) != "table":
        return None
    
    # Extract table content - this will depend on how tables are represented in your data
    table_content = element.get("table_content", element.get("cells", []))
    
    # If we have structured table data, convert it to a JSON string
    if table_content:
        return json.dumps(table_content)
    
    return None

def build_chunk(element, block_id, doc_id, source_metadata):
    """
    Build a chunk object mapping to the fusa_library schema.
    
    Args:
        element: Document element
        block_id: Sequential ID within document's body chunks
        doc_id: Document ID (can be None)
        source_metadata: Source document metadata
        
    Returns:
        dict: Chunk object with all required fields
    """
    metadata = element.get("extracted_metadata", {})
    content_type = extract_content_type(element)
    breadcrumb = metadata.get("breadcrumb", "")
    
    # Get bounding box coordinates
    bbox = metadata.get("bbox_raw", metadata.get("bbox", {}))
    coords_x = int(bbox.get("l", 0)) if bbox else 0
    coords_y = int(bbox.get("t", 0)) if bbox else 0
    coords_cx = int(bbox.get("r", 0) - bbox.get("l", 0)) if bbox else 0
    coords_cy = int(bbox.get("b", 0) - bbox.get("t", 0)) if bbox else 0
    
    # Get page number
    page_no = metadata.get("page_no", 1)
    
    # Prepare external_files path for images
    external_files = None
    if content_type == "image" and "external_path" in element:
        external_files = element.get("external_path")
    
    # Format text block
    text_block = format_text_block(element, breadcrumb)
    
    # Format table block
    table_block = format_table_block(element) if content_type == "table" else None
    
    # Get text for search indexing
    text_search = element.get("text_content", element.get("text", ""))
    if not text_search and content_type == "image":
        text_search = metadata.get("caption", "")
    
    # Build chunk object
    return {
        "_id": None,
        "block_id": block_id,
        "doc_id": doc_id,
        "content_type": content_type,
        "file_type": source_metadata.get("mimetype", "application/pdf"),
        "master_index": page_no,
        "master_index2": None,
        "coords_x": coords_x,
        "coords_y": coords_y,
        "coords_cx": coords_cx,
        "coords_cy": coords_cy,
        "author_or_speaker": None,
        "added_to_collection": None,
        "file_source": source_metadata.get("filename", ""),
        "table_block": table_block,
        "modified_date": None,
        "created_date": None,
        "creator_tool": "DoclingToJsonScript_V1.1",
        "external_files": external_files,
        "text_block": text_block,
        "header_text": breadcrumb,
        "text_search": text_search,
        "user_tags": None,
        "special_field1": json.dumps(metadata) if metadata else None,
        "special_field2": breadcrumb,
        "special_field3": None,
        "graph_status": None,
        "dialog": None,
        "embedding_flags": None,
        "metadata": metadata
    }

def save_standardized_output(document_data, output_dir, pdf_path):
    """
    Create and save the standardized output file required by the PRD.
    
    Args:
        document_data: The document data dictionary
        output_dir: Directory to save the standardized output
        pdf_path: Path to the original PDF file
        
    Returns:
        str: Path to the saved standardized output file
    """
    logger.info("Creating standardized output format")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get document name
    pdf_filename = Path(pdf_path).name
    doc_name = document_data.get("name", Path(pdf_path).stem)
    
    # Create source metadata
    source_metadata = {
        "filename": pdf_filename,
        "mimetype": "application/pdf",
        "binary_hash": hashlib.md5(pdf_filename.encode()).hexdigest() # Simple placeholder hash
    }
    
    # Initialize chunks and furniture arrays
    chunks = []
    furniture = []
    
    # Process the flattened sequence if available
    if "element_map" in document_data:
        element_map = document_data["element_map"]
        
        if "flattened_sequence" in element_map:
            flattened_sequence = element_map["flattened_sequence"]
            
            # Process each element in the sequence
            block_id = 1
            for element in flattened_sequence:
                if is_furniture(element):
                    # Add to furniture array if it's a furniture element
                    if "text_content" in element or "text" in element:
                        furniture_text = element.get("text_content", element.get("text", ""))
                        furniture.append(furniture_text)
                else:
                    # Add to chunks array if it's a content element
                    chunk = build_chunk(element, block_id, None, source_metadata)
                    chunks.append(chunk)
                    block_id += 1
    
    # Alternative: try to find elements directly in the document
    elif "texts" in document_data or "pictures" in document_data or "tables" in document_data:
        # Process text elements
        block_id = 1
        
        for text in document_data.get("texts", []):
            if is_furniture(text):
                furniture_text = text.get("text_content", text.get("text", ""))
                furniture.append(furniture_text)
            else:
                chunk = build_chunk(text, block_id, None, source_metadata)
                chunks.append(chunk)
                block_id += 1
        
        # Process picture elements
        for picture in document_data.get("pictures", []):
            if not is_furniture(picture):
                chunk = build_chunk(picture, block_id, None, source_metadata)
                chunks.append(chunk)
                block_id += 1
        
        # Process table elements
        for table in document_data.get("tables", []):
            if not is_furniture(table):
                chunk = build_chunk(table, block_id, None, source_metadata)
                chunks.append(chunk)
                block_id += 1
    
    # Build the standardized output structure
    standardized_output = {
        "chunks": chunks,
        "furniture": furniture,
        "source_metadata": source_metadata
    }
    
    # Save the standardized output
    output_file = output_path / f"{doc_name}_standardized.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(standardized_output, f, indent=2)
    
    logger.info(f"Standardized output saved to {output_file} with {len(chunks)} chunks and {len(furniture)} furniture elements")
    
    return str(output_file) 