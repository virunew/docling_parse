"""
Element Map Builder for DoclingDocument

This module provides functionality to build a complete element map
from a DoclingDocument JSON by resolving all $ref pointers.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_elements(docling_document: dict) -> dict:
    """
    Extract all elements from the DoclingDocument JSON and store them in a dictionary.
    
    Args:
        docling_document: The DoclingDocument JSON
        
    Returns:
        A dictionary mapping self_ref values to their corresponding element objects
    """
    element_map = {}
    
    def extract_from_dict(obj: dict, path: str = ""):
        """Recursively extract elements with self_ref from a dictionary."""
        if not isinstance(obj, dict):
            return
            
        # Check if this object has a self_ref property
        if "self_ref" in obj:
            element_map[obj["self_ref"]] = obj
            
        # Recursively process all dict values
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                extract_from_dict(value, new_path)
            elif isinstance(value, list):
                extract_from_list(value, new_path)
    
    def extract_from_list(obj_list: list, path: str):
        """Recursively extract elements with self_ref from a list."""
        for i, item in enumerate(obj_list):
            item_path = f"{path}[{i}]"
            
            if isinstance(item, dict):
                extract_from_dict(item, item_path)
            elif isinstance(item, list):
                extract_from_list(item, item_path)
    
    # Start extraction from the root
    extract_from_dict(docling_document)
    
    logger.info(f"Extracted {len(element_map)} elements with self_ref values")
    return element_map

def find_ref_pointers(element_map: dict) -> List[Tuple[str, List[str], str]]:
    """
    Scan through all elements and identify properties containing $ref pointers.
    
    Args:
        element_map: Dictionary mapping self_ref values to element objects
        
    Returns:
        List of tuples: (element_id, property_path, ref_value)
    """
    ref_pointers = []
    
    def scan_for_refs(obj: Any, element_id: str, path: List[str] = None):
        """Recursively scan for $ref pointers in an object."""
        if path is None:
            path = []
            
        if isinstance(obj, dict):
            # Check if this is a $ref pointer
            if len(obj) == 1 and "$ref" in obj:
                ref_value = obj["$ref"]
                ref_pointers.append((element_id, path.copy(), ref_value))
            else:
                # Recursively scan all dict values
                for key, value in obj.items():
                    new_path = path + [key]
                    scan_for_refs(value, element_id, new_path)
        elif isinstance(obj, list):
            # Recursively scan all list items
            for i, item in enumerate(obj):
                new_path = path + [i]
                scan_for_refs(item, element_id, new_path)
    
    # Scan each element in the map
    for element_id, element in element_map.items():
        scan_for_refs(element, element_id)
    
    logger.info(f"Found {len(ref_pointers)} $ref pointers in the document")
    return ref_pointers

def resolve_references(element_map: dict, ref_pointers: List[Tuple[str, List[str], str]]) -> dict:
    """
    Resolve all $ref pointers and create a complete element map.
    
    Args:
        element_map: Dictionary mapping self_ref values to element objects
        ref_pointers: List of tuples (element_id, property_path, ref_value)
        
    Returns:
        Updated element map with all references resolved
    """
    def update_property(obj: dict, path: List, value: Any) -> None:
        """
        Update a nested property in an object based on the property path.
        
        Args:
            obj: The object to update
            path: List representing the path to the property
            value: The new value to set
        """
        if not path:
            return
            
        current = obj
        
        # Navigate to the parent object
        for i, key in enumerate(path[:-1]):
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                current = current[key]
            else:
                logger.warning(f"Invalid path: {path}")
                return
                
        # Update the final property
        last_key = path[-1]
        if isinstance(current, dict) and last_key in current:
            current[last_key] = value
        elif isinstance(current, list) and isinstance(last_key, int) and last_key < len(current):
            current[last_key] = value
        else:
            logger.warning(f"Invalid path: {path}")
    
    # Process all reference pointers
    resolved_count = 0
    missing_count = 0
    
    # Create a deep copy of the element map to avoid modifying it during iteration
    resolved_map = {k: v.copy() if isinstance(v, dict) else v for k, v in element_map.items()}
    
    for element_id, property_path, ref_value in ref_pointers:
        # Ensure the element still exists (might have been removed due to circular refs)
        if element_id not in resolved_map:
            continue
            
        element = resolved_map[element_id]
        
        # Look up the referenced element
        if ref_value in resolved_map:
            referenced_element = resolved_map[ref_value]
            
            # Update the reference
            try:
                # Get the current value at the property path
                current = element
                for p in property_path[:-1]:
                    if isinstance(p, int):
                        current = current[p]
                    else:
                        current = current[p]
                
                # Replace the $ref object with the actual element
                if isinstance(property_path[-1], int):
                    current[property_path[-1]] = referenced_element
                else:
                    current[property_path[-1]] = referenced_element
                    
                resolved_count += 1
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Error resolving reference at {property_path} in element {element_id}: {e}")
        else:
            logger.warning(f"Reference not found: {ref_value}")
            missing_count += 1
    
    logger.info(f"Resolved {resolved_count} references, {missing_count} references not found")
    return resolved_map

def build_element_map(docling_document: dict) -> dict:
    """
    Build a complete element map by resolving all $ref pointers in the DoclingDocument JSON.
    
    Args:
        docling_document: The DoclingDocument JSON
        
    Returns:
        A dictionary mapping self_ref values to their corresponding element objects
        with all references resolved
    """
    # Step 1: Extract all elements with self_ref
    logger.info("Step 1: Extracting elements with self_ref values")
    element_map = extract_elements(docling_document)
    
    # Step 2: Find all $ref pointers
    logger.info("Step 2: Finding all $ref pointers")
    ref_pointers = find_ref_pointers(element_map)
    
    # Step 3: Resolve references
    logger.info("Step 3: Resolving references")
    resolved_map = resolve_references(element_map, ref_pointers)
    
    logger.info(f"Built element map with {len(resolved_map)} elements")
    return resolved_map

# Example usage
if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python element_map_builder.py <path_to_docling_document.json>")
        sys.exit(1)
        
    # Load the DoclingDocument JSON
    with open(sys.argv[1], 'r') as f:
        docling_document = json.load(f)
        
    # Build the element map
    element_map = build_element_map(docling_document)
    
    # Optionally output the element map
    # with open('element_map.json', 'w') as f:
    #     json.dump(element_map, f, indent=2) 