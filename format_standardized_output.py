"""
Format Standardized Output Module

This module contains functions to transform the raw docling output into
the standardized JSON format required by the PRD with top-level chunks,
furniture, and source_metadata.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_standardized_output(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw docling document output into the standardized format
    with chunks, furniture, and source_metadata.
    
    Args:
        document_data: The raw document data from docling
        
    Returns:
        Dict containing the standardized format with chunks, furniture, and source_metadata
    """
    # Initialize the standardized output structure
    standardized_output = {
        "chunks": [],
        "furniture": [],
        "source_metadata": {}
    }
    
    # Extract source metadata
    if "metadata" in document_data:
        standardized_output["source_metadata"] = document_data["metadata"]
    elif "origin" in document_data:
        standardized_output["source_metadata"] = document_data["origin"]
    
    # Handle content in different formats
    
    # Check if there's a content field with pictures
    if "content" in document_data and "pictures" in document_data["content"]:
        process_pictures(document_data["content"]["pictures"], standardized_output)
    
    # Check if there's a content field with paragraphs
    if "content" in document_data and "paragraphs" in document_data["content"]:
        process_paragraphs(document_data["content"]["paragraphs"], standardized_output)
    
    # Check if there's a content field with text
    if "content" in document_data and "text" in document_data["content"]:
        process_text(document_data["content"]["text"], standardized_output)
    
    # Handle direct fields at the top level (for different schema versions)
    
    # Check if pictures exists directly at top level
    if "pictures" in document_data:
        process_pictures(document_data["pictures"], standardized_output)
    
    # Check if texts exists directly at top level (equivalent to paragraphs)
    if "texts" in document_data:
        process_texts(document_data["texts"], standardized_output)
    
    # Handle furniture section if it exists
    if "furniture" in document_data:
        process_furniture(document_data["furniture"], standardized_output)
    
    return standardized_output

def process_pictures(pictures: List[Dict[str, Any]], output: Dict[str, Any]) -> None:
    """
    Process picture items and add them to the output
    
    Args:
        pictures: List of picture items
        output: Output dictionary to add chunks to
    """
    for image_item in pictures:
        # Initialize image_content as empty
        image_content = ""
        
        # Check for external file path first (prioritize it over embedded data)
        if "external_path" in image_item:
            # Use the external file path directly
            image_content = image_item["external_path"]
            logger.debug(f"Using external file path: {image_content}")
        # Check if data_uri exists directly in the image_item
        elif "data_uri" in image_item:
            image_content = image_item["data_uri"]
        # Check if image field exists and contains uri with base64 data
        elif "image" in image_item and isinstance(image_item["image"], dict):
            if "uri" in image_item["image"]:
                image_content = image_item["image"]["uri"]
            elif "mimetype" in image_item["image"] and "data" in image_item["image"]:
                # Construct data URI from mimetype and data
                image_content = f"data:{image_item['image']['mimetype']};base64,{image_item['image']['data']}"
        # Check if file_path exists in metadata (added by process_extracted_images)
        elif "metadata" in image_item and "file_path" in image_item["metadata"]:
            image_content = image_item["metadata"]["file_path"]
            logger.debug(f"Using file path from metadata: {image_content}")
                
        # Create chunk for the image
        chunk = {
            "content": image_content,
            "page_number": image_item.get("page_number", 0),
            "bounds": image_item.get("bounds", {}),
            "id": image_item.get("id", ""),
            "format": "image",
            "metadata": {
                "caption": image_item.get("caption", ""),
                "description": image_item.get("description", ""),
                "references": image_item.get("references", []),
                "is_external": "external_path" in image_item or ("metadata" in image_item and "file_path" in image_item["metadata"]),
                "mimetype": (image_item.get("image", {}).get("mimetype", "") 
                            if isinstance(image_item.get("image", {}), dict) else "")
            }
        }
        output["chunks"].append(chunk)

def process_paragraphs(paragraphs: List[Dict[str, Any]], output: Dict[str, Any]) -> None:
    """
    Process paragraph items and add them to the output
    
    Args:
        paragraphs: List of paragraph items
        output: Output dictionary to add chunks/furniture to
    """
    for text_item in paragraphs:
        # Check if it's a furniture item
        if text_item.get("is_furniture", False):
            furniture_item = {
                "content": text_item.get("text", ""),
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "type": text_item.get("furniture_type", ""),
                    "references": text_item.get("references", [])
                }
            }
            output["furniture"].append(furniture_item)
        else:
            # It's a regular text chunk
            chunk = {
                "content": text_item.get("text", ""),
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "references": text_item.get("references", [])
                }
            }
            output["chunks"].append(chunk)

def process_text(text_items: List[Dict[str, Any]], output: Dict[str, Any]) -> None:
    """
    Process text items and add them to the output
    
    Args:
        text_items: List of text items
        output: Output dictionary to add chunks/furniture to
    """
    for text_item in text_items:
        # Check if it's a furniture item
        if text_item.get("is_furniture", False):
            furniture_item = {
                "content": text_item.get("text", ""),
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "type": text_item.get("furniture_type", ""),
                    "references": text_item.get("references", [])
                }
            }
            output["furniture"].append(furniture_item)
        else:
            # It's a regular text chunk
            chunk = {
                "content": text_item.get("text", ""),
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "references": text_item.get("references", [])
                }
            }
            output["chunks"].append(chunk)

def process_texts(texts: List[Dict[str, Any]], output: Dict[str, Any]) -> None:
    """
    Process texts items (top-level) and add them to the output
    
    Args:
        texts: List of text items
        output: Output dictionary to add chunks/furniture to
    """
    for text_item in texts:
        # Check content_layer to determine if it's furniture
        is_furniture = text_item.get("content_layer") == "furniture"
        
        # Get text content from appropriate field
        text_content = text_item.get("text", "")
        
        # If no text field, try looking in content field
        if not text_content and "content" in text_item:
            text_content = text_item["content"]
        
        if is_furniture:
            furniture_item = {
                "content": text_content,
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "type": text_item.get("label", ""),
                    "references": []
                }
            }
            output["furniture"].append(furniture_item)
        else:
            # It's a regular text chunk
            chunk = {
                "content": text_content,
                "page_number": text_item.get("page_number", 0),
                "bounds": text_item.get("bounds", {}),
                "id": text_item.get("id", ""),
                "format": "text",
                "metadata": {
                    "references": []
                }
            }
            output["chunks"].append(chunk)

def process_furniture(furniture: Dict[str, Any], output: Dict[str, Any]) -> None:
    """
    Process furniture items and add them to the output
    
    Args:
        furniture: Furniture data
        output: Output dictionary to add furniture to
    """
    # If furniture has children, process them
    if "children" in furniture and isinstance(furniture["children"], list):
        for item in furniture["children"]:
            if "content" in item:
                furniture_item = {
                    "content": item["content"],
                    "page_number": item.get("page_number", 0),
                    "bounds": item.get("bounds", {}),
                    "id": item.get("id", ""),
                    "format": "text",
                    "metadata": {
                        "type": item.get("label", ""),
                        "references": []
                    }
                }
                output["furniture"].append(furniture_item)
    # If it's a simple furniture item with content
    elif "content" in furniture:
        furniture_item = {
            "content": furniture["content"],
            "page_number": furniture.get("page_number", 0),
            "bounds": furniture.get("bounds", {}),
            "id": furniture.get("id", ""),
            "format": "text",
            "metadata": {
                "type": furniture.get("label", ""),
                "references": []
            }
        }
        output["furniture"].append(furniture_item)

def save_standardized_output(document_data: Dict[str, Any], output_dir: str, 
                            input_filename: str) -> str:
    """
    Create and save the standardized output file.
    
    Args:
        document_data: The raw document data from docling
        output_dir: Directory to save the output
        input_filename: Original input filename
        
    Returns:
        Path to the saved standardized output file
    """
    # Create the standardized output
    standardized_output = create_standardized_output(document_data)
    
    # Generate output filename
    output_filename = os.path.splitext(os.path.basename(input_filename))[0] + "_formatted.json"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save the standardized output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(standardized_output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Standardized output saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    # Simple test to try the formatting with the sample file
    import os
    sample_file = os.path.join("output_main", "SBW_AI sample page10-11.json")
    output_dir = "output_main"
    
    if os.path.exists(sample_file):
        print(f"Processing {sample_file}")
        with open(sample_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        # Create standardized output
        output_path = save_standardized_output(document_data, output_dir, sample_file)
        print(f"Standardized output saved to: {output_path}")
        
        # Show some stats
        with open(output_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
            print(f"Chunks: {len(result['chunks'])}")
            print(f"Furniture: {len(result['furniture'])}")
            chunk_types = {}
            for chunk in result['chunks']:
                chunk_type = chunk['format']
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            print(f"Found chunk types: {chunk_types}")
    else:
        print(f"Error: {sample_file} not found.") 