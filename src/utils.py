"""
Utilities Module

This module provides common utility functions used throughout the codebase
to avoid code duplication and ensure consistent behavior.
"""

import logging
import re
import os
import base64
import copy
import json
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Union, Optional

# Set up logger
logger = logging.getLogger(__name__)

def remove_base64_data(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Remove base64 image data from the given data structure.
    
    Args:
        data: A dictionary or list potentially containing base64 data.
        
    Returns:
        The same data structure with base64 data replaced with placeholder text.
    """
    if isinstance(data, dict):
        # Create a new dictionary and process each key-value pair
        result = {}
        for key, value in data.items():
            if key == 'base64_data' or key.endswith('_data_uri'):
                # Replace base64 data with a placeholder
                result[key] = "[BASE64_DATA_REMOVED]"
            elif key == 'raw_data' and not isinstance(value, (dict, list)):
                # Handle binary data
                result[key] = "[BINARY_IMAGE_DATA_REMOVED]"
            else:
                # Recursively process nested dictionaries or lists
                result[key] = remove_base64_data(value)
        return result
    elif isinstance(data, list):
        # Create a new list and process each item
        result = []
        for item in data:
            if isinstance(item, str) and item.startswith('data:image/'):
                # Replace base64 image data with a placeholder
                result.append("[BASE64_DATA_REMOVED]")
            else:
                # Recursively process nested dictionaries or lists
                result.append(remove_base64_data(item))
        return result
    else:
        # Return other data types unchanged
        return data

def replace_base64_with_file_references(
    data: Union[Dict, List, Any], 
    images_dir: Union[str, Path], 
    doc_id: str
) -> Union[Dict, List, Any]:
    """
    Replace base64 image data with file references in the document data.
    
    This function:
    1. Recursively searches for base64_data fields in the document
    2. Decodes and saves the base64 data as image files in the specified directory
    3. Replaces the base64_data field with a reference to the saved file
    4. Deduplicates images by checking hash values before saving
    
    Args:
        data: A dictionary or list potentially containing base64 data
        images_dir: Directory where image files will be saved
        doc_id: Document ID used as part of the image filenames
        
    Returns:
        The same data structure with base64 data replaced with file references
    """
    # Convert images_dir to Path if it's a string
    if isinstance(images_dir, str):
        images_dir = Path(images_dir)
    
    # Make sure the doc_id/images directory structure exists
    doc_images_dir = images_dir / doc_id / "images"
    doc_images_dir.mkdir(parents=True, exist_ok=True)
    
    # Counter for generating unique image filenames
    image_counter = 0
    
    # Dictionary to track image hashes for deduplication
    image_hash_map = {}
    
    # Create simplified names for frequently used images
    simplified_names = {
        # The mapping will be populated as images are processed
        # hash_value -> (filename, relative_path)
    }
    
    # Check if a standardized image name already exists (like picture_1.png)
    def check_standardized_images():
        """Check for existing standardized image names in the directory"""
        for i in range(1, 10):  # Reasonable limit to check
            std_name = f"picture_{i}.png"
            std_path = doc_images_dir / std_name
            if std_path.exists():
                # Read the file to compute its hash
                try:
                    with open(std_path, 'rb') as f:
                        file_data = f.read()
                        # Convert image data to base64 and then hash it to match the
                        # same algorithm used when processing base64 data
                        base64_data = base64.b64encode(file_data).decode('utf-8')
                        hash_value = hashlib.md5(base64_data.encode()).hexdigest()[:10]
                        simplified_names[hash_value] = (std_name, f"{doc_id}/images/{std_name}")
                        logging.info(f"Found existing standardized image: {std_name} with hash {hash_value}")
                except Exception as e:
                    logging.warning(f"Error reading existing image {std_path}: {e}")
    
    # Call the function to populate simplified_names from existing files
    check_standardized_images()
    
    def process_data(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Inner recursive function to process the data structure"""
        nonlocal image_counter
        
        if isinstance(data, dict):
            # Create a new dictionary to store the processed data
            result = {}
            for key, value in data.items():
                # Check for various field names that might contain base64 image data
                if (key in ('base64_data', 'uri', 'data_uri', 'data') and 
                    isinstance(value, str) and 
                    value.startswith('data:image/')):
                    try:
                        # Extract image format and data from data URI
                        if ',' in value:
                            header, encoded_data = value.split(',', 1)
                            # Determine image format from header
                            image_format = "png"  # Default
                            if "image/jpeg" in header:
                                image_format = "jpg"
                            elif "image/png" in header:
                                image_format = "png"
                            elif "image/gif" in header:
                                image_format = "gif"
                            elif "image/svg+xml" in header:
                                image_format = "svg"
                            
                            # Decode base64 data
                            try:
                                # Create a hash of the base64 data for uniqueness
                                hash_value = hashlib.md5(encoded_data.encode()).hexdigest()[:10]
                                
                                # Check if we've already processed this image (deduplication)
                                if hash_value in image_hash_map:
                                    # Reuse the existing path
                                    relative_path = image_hash_map[hash_value]
                                    logging.info(f"Reusing existing image with hash {hash_value}")
                                elif hash_value in simplified_names:
                                    # Reuse an existing standardized image
                                    _, relative_path = simplified_names[hash_value]
                                    logging.info(f"Reusing standardized image for hash {hash_value}")
                                else:
                                    # Decode the image data
                                    image_data = base64.b64decode(encoded_data)
                                    
                                    # Create a unique filename for the image
                                    image_counter += 1
                                    
                                    # Use standardized names for the first few images if they don't exist yet
                                    if image_counter <= 2 and f"picture_{image_counter}.png" not in [name for name, _ in simplified_names.values()]:
                                        filename = f"picture_{image_counter}.png"
                                        simplified_names[hash_value] = (filename, f"{doc_id}/images/{filename}")
                                    else:
                                        filename = f"{doc_id}_img_{image_counter}_{hash_value}.{image_format}"
                                    
                                    file_path = doc_images_dir / filename
                                    relative_path = f"{doc_id}/images/{filename}"
                                    
                                    # Save the image file
                                    with open(file_path, 'wb') as f:
                                        f.write(image_data)
                                    logging.info(f"Saved image to {file_path}")
                                    
                                    # Add to our hash map for future deduplication
                                    image_hash_map[hash_value] = relative_path
                                
                                # Update the value with the external file reference
                                result[key] = relative_path
                                
                                # Also add an explicit external_file field
                                result['external_file'] = relative_path
                                
                                # Copy all other fields
                                for k, v in data.items():
                                    if k != key and k != 'external_file':
                                        result[k] = v
                            except Exception as e:
                                logging.error(f"Error decoding base64 or saving image: {e}")
                                # Return the original data if there's an error
                                result[key] = value
                        else:
                            # If no comma separator, process other fields recursively
                            result[key] = process_data(value)
                    except Exception as e:
                        logging.error(f"Error processing image data: {e}")
                        result[key] = value
                elif key == 'base64_data' and isinstance(value, str) and 'mime_type' in data:
                    try:
                        # Extract information needed for the image file
                        mime_type = data['mime_type']
                        extension = _get_extension_from_mime(mime_type)
                        
                        # Clean the base64 data if it includes a data URI prefix
                        clean_base64 = value
                        if clean_base64.startswith('data:'):
                            clean_base64 = clean_base64.split(',', 1)[1]
                        
                        # Create a hash of the base64 data for uniqueness
                        hash_value = hashlib.md5(clean_base64.encode()).hexdigest()[:10]
                        
                        # Check if we've already processed this image (deduplication)
                        if hash_value in image_hash_map:
                            # Reuse the existing path
                            relative_path = image_hash_map[hash_value]
                            logging.info(f"Reusing existing image with hash {hash_value}")
                        elif hash_value in simplified_names:
                            # Reuse an existing standardized image
                            _, relative_path = simplified_names[hash_value]
                            logging.info(f"Reusing standardized image for hash {hash_value}")
                        else:
                            # Decode the image data
                            image_data = base64.b64decode(clean_base64)
                            
                            # Create a unique filename for the image
                            image_counter += 1
                            
                            # Use standardized names for the first few images if they don't exist yet
                            if image_counter <= 2 and f"picture_{image_counter}.png" not in [name for name, _ in simplified_names.values()]:
                                filename = f"picture_{image_counter}.png"
                                simplified_names[hash_value] = (filename, f"{doc_id}/images/{filename}")
                            else:
                                filename = f"{doc_id}_img_{image_counter}_{hash_value}{extension}"
                            
                            file_path = doc_images_dir / filename
                            relative_path = f"{doc_id}/images/{filename}"
                            
                            # Save the image file
                            with open(file_path, 'wb') as f:
                                f.write(image_data)
                            logging.info(f"Saved image to {file_path}")
                            
                            # Add to our hash map for future deduplication
                            image_hash_map[hash_value] = relative_path
                        
                        # Create a copy of the content dict without base64_data
                        content_dict = {k: v for k, v in data.items() if k != 'base64_data'}
                        # Add the external_file reference
                        content_dict['external_file'] = relative_path
                        return content_dict
                    except Exception as e:
                        logging.error(f"Error processing base64 data: {e}")
                        result[key] = value
                else:
                    # Recursively process nested dictionaries or lists
                    result[key] = process_data(value)
            return result
        elif isinstance(data, list):
            # Process each item in the list
            return [process_data(item) for item in data]
        else:
            # Return other data types unchanged
            return data
    
    # Process the document data
    return process_data(data)

def _get_extension_from_mime(mime_type: str) -> str:
    """Get the file extension from a MIME type"""
    mime_map = {
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/gif': '.gif',
        'image/svg+xml': '.svg',
        'image/webp': '.webp',
        'image/tiff': '.tiff',
        'image/bmp': '.bmp',
        'application/pdf': '.pdf'
    }
    return mime_map.get(mime_type.lower(), '.bin')

def generate_unique_id():
    """Generate a unique ID for documents."""
    return str(uuid.uuid4())

def get_doc_id_from_filename(filename: str) -> str:
    """
    Extract a document ID from a filename.
    
    Args:
        filename: The filename to extract the ID from
        
    Returns:
        A document ID based on the filename
    """
    # Get the base filename without extension
    base_name = os.path.splitext(os.path.basename(filename))[0]
    # Clean the name to make it a valid path component
    return re.sub(r'[^\w\-_]', '_', base_name)

def save_json(data, file_path, indent=2):
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save
        file_path: The path to save the file to
        indent: The indentation level for the JSON file
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    logging.info(f"Saved JSON data to {file_path}")

def load_json(file_path):
    """
    Load data from a JSON file.
    
    Args:
        file_path: The path to load the file from
        
    Returns:
        The loaded JSON data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f) 