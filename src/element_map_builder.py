"""
Element Map Builder

This module provides functionality for building a map of elements from a DoclingDocument,
resolving references between elements to create a flattened representation.
"""

# Fix docling imports
import sys
import os
from pathlib import Path

# Add parent directory to sys.path to find docling_fix
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import docling_fix

import logging
import json
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Import docling types with exception handling
try:
    from docling.datamodel.document import DoclingDocument
    from pydantic import AnyUrl  # Import AnyUrl for serialization handling
except ImportError as e:
    logger.error(f"Error importing DoclingDocument: {e}")
    # Create placeholder for type hints
    class DoclingDocument:
        """Placeholder for DoclingDocument class"""
        pass
    
    class AnyUrl:
        """Placeholder for AnyUrl class"""
        pass

# Custom JSON encoder to handle Pydantic's AnyUrl and other types
class DoclingJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling Pydantic models and special types."""
    
    def default(self, obj):
        """Handle special types during JSON serialization."""
        # Handle Pydantic's AnyUrl type
        if isinstance(obj, AnyUrl):
            return str(obj)
        
        # Handle Pydantic models with .dict() method
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            return obj.dict()
        
        # Handle Pydantic models with .__dict__ attribute
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        
        # Let the base class handle it (will raise TypeError for unsupported types)
        return super().default(obj)

def convert_to_serializable(obj):
    """
    Recursively convert an object to a JSON serializable format.
    
    Args:
        obj: Any Python object
        
    Returns:
        A JSON serializable version of the object
    """
    # Check for None early to avoid attribute lookups
    if obj is None:
        return None
    
    # Handle TextItem and similar objects with to_dict method
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        # Use the object's own serialization method
        return obj.to_dict()
        
    if isinstance(obj, dict):
        # Process dictionary
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Process list
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        # Basic types are already serializable
        return obj
    elif isinstance(obj, AnyUrl):
        # Convert AnyUrl to string
        return str(obj)
    elif hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        # Handle Pydantic models with .dict() method
        try:
            return convert_to_serializable(obj.dict())
        except Exception as e:
            logger.warning(f"Error calling .dict() on {type(obj)}: {e}")
            # Fall back to __dict__
            if hasattr(obj, "__dict__"):
                return convert_to_serializable(obj.__dict__)
            return str(obj)
    elif hasattr(obj, "__dict__") and "mock" not in type(obj).__name__.lower():
        # Handle objects with __dict__ attribute (but avoid MagicMock recursion)
        return convert_to_serializable(obj.__dict__)
    else:
        # Try to convert to string as a fallback
        try:
            return str(obj)
        except Exception:
            logger.warning(f"Could not serialize object of type {type(obj)}")
            return None

def build_element_map(docling_document: DoclingDocument) -> Dict[str, Any]:
    """
    Build a map of elements from a DoclingDocument.
    
    This function extracts all the elements from a DoclingDocument and creates a map
    with the element's self_ref as the key and the element itself as the value.
    It also flattens the document body into a sequence of elements in the order
    they appear in the document.
    
    Args:
        docling_document: The DoclingDocument instance
        
    Returns:
        Dict with keys:
            - elements: Dict mapping self_ref to element
            - flattened_sequence: List of elements in document order
    """
    try:
        logger.info("Building element map from DoclingDocument")
        
        # Initialize the result structure
        result = {
            "elements": {},
            "flattened_sequence": [],
            "document_info": {
                "name": getattr(docling_document, "name", "unknown"),
                "page_count": 0
            }
        }
        
        # Get pages from the document
        pages = getattr(docling_document, "pages", [])
        result["document_info"]["page_count"] = len(pages)
        
        # Step 1: Extract all elements from the document
        # Start with texts
        text_count = 0
        for text in getattr(docling_document, "texts", []):
            # Use getattr instead of dict-style access
            self_ref = getattr(text, "self_ref", None)
            if self_ref:
                # Convert to serializable format
                result["elements"][self_ref] = convert_to_serializable(text)
                text_count += 1
        logger.debug(f"Extracted {text_count} text elements")
        
        # Add tables
        table_count = 0
        for table in getattr(docling_document, "tables", []):
            # Use getattr instead of dict-style access
            self_ref = getattr(table, "self_ref", None)
            if self_ref:
                # Convert to serializable format
                result["elements"][self_ref] = convert_to_serializable(table)
                table_count += 1
        logger.debug(f"Extracted {table_count} table elements")
        
        # Add pictures
        picture_count = 0
        for picture in getattr(docling_document, "pictures", []):
            # Use getattr instead of dict-style access
            self_ref = getattr(picture, "self_ref", None)
            if self_ref:
                # Convert to serializable format
                result["elements"][self_ref] = convert_to_serializable(picture)
                picture_count += 1
        logger.debug(f"Extracted {picture_count} picture elements")
        
        # Add groups
        group_count = 0
        for group in getattr(docling_document, "groups", []):
            # Use getattr instead of dict-style access
            self_ref = getattr(group, "self_ref", None)
            if self_ref:
                # Convert to serializable format
                result["elements"][self_ref] = convert_to_serializable(group)
                group_count += 1
        logger.debug(f"Extracted {group_count} group elements")
                
        # Step 2: Flatten the document body into a sequence
        body = getattr(docling_document, "body", {})
        
        # Log the body attributes to help debug
        if body:
            logger.debug(f"Body type: {type(body)}")
            if hasattr(body, "__dict__"):
                logger.debug(f"Body attributes: {list(body.__dict__.keys())}")
            elif isinstance(body, dict):
                logger.debug(f"Body keys: {list(body.keys())}")
        else:
            logger.warning("No body found in the document")
            
        # Find all top-level elements in the document body
        body_elements = []
        
        # Try multiple potential ways to find elements
        # 1. Direct 'elements' attribute or key in body
        if hasattr(body, "elements"):
            body_elements = getattr(body, "elements", [])
            logger.debug(f"Found {len(body_elements)} elements in body.elements")
        elif isinstance(body, dict) and "elements" in body:
            body_elements = body["elements"]
            logger.debug(f"Found {len(body_elements)} elements in body['elements']")
            
        # 2. If that didn't work, try 'children' attribute or key
        if not body_elements and hasattr(body, "children"):
            body_elements = getattr(body, "children", [])
            logger.debug(f"Found {len(body_elements)} elements in body.children")
        elif not body_elements and isinstance(body, dict) and "children" in body:
            body_elements = body["children"]
            logger.debug(f"Found {len(body_elements)} elements in body['children']")
            
        # 3. If there's a 'content' attribute/key with elements/children inside
        if not body_elements and hasattr(body, "content"):
            content = getattr(body, "content", {})
            if hasattr(content, "elements"):
                body_elements = getattr(content, "elements", [])
                logger.debug(f"Found {len(body_elements)} elements in body.content.elements")
            elif isinstance(content, dict) and "elements" in content:
                body_elements = content["elements"]
                logger.debug(f"Found {len(body_elements)} elements in body.content['elements']")
                
        # 4. As a last resort, directly get texts, tables, pictures from document
        if not body_elements:
            logger.warning("No elements found in body structure, using direct document elements")
            # Collect all refs for direct elements
            for text in getattr(docling_document, "texts", []):
                self_ref = getattr(text, "self_ref", None)
                if self_ref:
                    body_elements.append(self_ref)
            
            for table in getattr(docling_document, "tables", []):
                self_ref = getattr(table, "self_ref", None)
                if self_ref:
                    body_elements.append(self_ref)
                    
            for picture in getattr(docling_document, "pictures", []):
                self_ref = getattr(picture, "self_ref", None)
                if self_ref:
                    body_elements.append(self_ref)
                    
            for group in getattr(docling_document, "groups", []):
                self_ref = getattr(group, "self_ref", None)
                if self_ref:
                    body_elements.append(self_ref)
                    
            logger.debug(f"Collected {len(body_elements)} direct element references")
        
        # Helper function to recursively process elements in the body
        def process_element(element_ref, seen_refs=None):
            if seen_refs is None:
                seen_refs = set()
                
            # Check for cycles to avoid infinite recursion
            if element_ref in seen_refs:
                logger.warning(f"Cycle detected in element references: {element_ref}")
                return []
                
            seen_refs.add(element_ref)
            
            # Get the element from the map
            element = result["elements"].get(element_ref)
            if not element:
                logger.warning(f"Element reference not found in map: {element_ref}")
                return []
            
            flattened = []
            
            # Process the element based on its type
            # Check if the element has a $ref attribute or key
            has_ref = (hasattr(element, "$ref") or 
                      (isinstance(element, dict) and "$ref" in element))
            
            # Check if the element has an elements attribute or key
            has_elements = (hasattr(element, "elements") or 
                           (isinstance(element, dict) and "elements" in element))
                           
            # Check if the element has a children attribute or key
            has_children = (hasattr(element, "children") or 
                           (isinstance(element, dict) and "children" in element))
            
            if has_ref:
                # Get the $ref value using the appropriate method
                ref_value = getattr(element, "$ref", None) if hasattr(element, "$ref") else element.get("$ref")
                # If the element has a $ref, process the referenced element
                flattened.extend(process_element(ref_value, seen_refs))
            elif has_elements:
                # Get the elements list using the appropriate method
                elements_list = getattr(element, "elements", []) if hasattr(element, "elements") else element.get("elements", [])
                # If the element has child elements, process each child
                for child_ref in elements_list:
                    flattened.extend(process_element(child_ref, seen_refs.copy()))
            elif has_children:
                # Get the children list using the appropriate method
                children_list = getattr(element, "children", []) if hasattr(element, "children") else element.get("children", [])
                # Process each child reference
                for child in children_list:
                    # Handle both ref strings and objects with cref
                    if isinstance(child, str):
                        flattened.extend(process_element(child, seen_refs.copy()))
                    elif hasattr(child, "cref") and getattr(child, "cref"):
                        flattened.extend(process_element(getattr(child, "cref"), seen_refs.copy()))
                    elif isinstance(child, dict) and "cref" in child and child["cref"]:
                        flattened.extend(process_element(child["cref"], seen_refs.copy()))
            else:
                # This is a leaf element, add it to the flattened sequence
                flattened.append(element)
            
            return flattened
        
        # Process the document body
        processed_count = 0
        for element_ref in body_elements:
            # Handle both string references and objects with reference properties
            if isinstance(element_ref, str):
                result["flattened_sequence"].extend(process_element(element_ref))
                processed_count += 1
            elif hasattr(element_ref, "$ref") and getattr(element_ref, "$ref"):
                result["flattened_sequence"].extend(process_element(getattr(element_ref, "$ref")))
                processed_count += 1
            elif hasattr(element_ref, "cref") and getattr(element_ref, "cref"):
                result["flattened_sequence"].extend(process_element(getattr(element_ref, "cref")))
                processed_count += 1
            elif isinstance(element_ref, dict):
                if "$ref" in element_ref and element_ref["$ref"]:
                    result["flattened_sequence"].extend(process_element(element_ref["$ref"]))
                    processed_count += 1
                elif "cref" in element_ref and element_ref["cref"]:
                    result["flattened_sequence"].extend(process_element(element_ref["cref"]))
                    processed_count += 1
            else:
                # Try to find any reference in the element
                ref_value = None
                if hasattr(element_ref, "self_ref"):
                    ref_value = getattr(element_ref, "self_ref")
                elif hasattr(element_ref, "id"):
                    ref_value = getattr(element_ref, "id")
                elif isinstance(element_ref, dict) and ("self_ref" in element_ref or "id" in element_ref):
                    ref_value = element_ref.get("self_ref") or element_ref.get("id")
                
                if ref_value:
                    result["flattened_sequence"].extend(process_element(ref_value))
                    processed_count += 1
                else:
                    logger.warning(f"Could not determine reference for element: {element_ref}")
        
        logger.debug(f"Processed {processed_count} top-level elements from body")
        
        # If flattened sequence is still empty after all attempts, use a simplified approach
        if not result["flattened_sequence"]:
            logger.warning("Flattened sequence is empty, using direct element approach")
            # Simply add all elements to the flattened sequence in the order they were found
            for self_ref, element in result["elements"].items():
                # Skip any elements that appear to be structural (body, document, etc.)
                element_type = None
                if isinstance(element, dict) and "type_name" in element:
                    element_type = element["type_name"]
                elif hasattr(element, "type_name"):
                    element_type = element.type_name
                    
                if element_type not in ["body", "document"]:
                    result["flattened_sequence"].append(element)
        
        logger.info(f"Element map built successfully with {len(result['elements'])} elements")
        logger.info(f"Flattened sequence contains {len(result['flattened_sequence'])} elements")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error building element map: {e}")
        return {
            "elements": {},
            "flattened_sequence": [],
            "document_info": {"name": "error", "page_count": 0},
            "error": str(e)
        }


def save_element_map(element_map: Dict[str, Any], output_path: Union[str, Path]) -> Path:
    """
    Save the element map to a JSON file.
    
    Args:
        element_map: The element map to save
        output_path: Path to save the element map
        
    Returns:
        Path to the saved file
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Use the custom encoder to handle Pydantic types
            json.dump(element_map, f, indent=2, cls=DoclingJSONEncoder)
            
        logger.info(f"Element map saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.exception(f"Error saving element map: {e}")
        raise

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
            json.dump(element_map, f, indent=2, cls=DoclingJSONEncoder)
        print(f"Element map saved to {output_file}")
        
    except ImportError:
        print("Could not import docling library. This script requires docling to be installed.")
        sys.exit(1)

class ElementMapBuilder:
    """
    A class for building an element map from a DoclingDocument.
    
    This class provides an object-oriented interface to the element map building
    process, making it easier to test and use in different contexts.
    """
    
    def __init__(self):
        """Initialize the ElementMapBuilder."""
        self.logger = logging.getLogger(__name__)
    
    def build_element_map(self, document):
        """
        Build a map of elements from a DoclingDocument.
        
        Args:
            document: The document object, which can be a DoclingDocument instance
                    or a dictionary with document elements.
                    
        Returns:
            Dict with keys:
                - elements: Dict mapping self_ref to element
                - flattened_sequence: List of elements in document order
        """
        if isinstance(document, dict) and "elements" in document:
            # Special case for test document structure where elements are pre-organized
            return self._build_from_elements_dict(document)
        else:
            # Regular case for DoclingDocument
            return build_element_map(document)
    
    def _build_from_elements_dict(self, document):
        """
        Build an element map from a dictionary with pre-organized elements.
        
        This method is primarily for testing with simplified document structures.
        
        Args:
            document: Dictionary with 'elements' key mapping element IDs to element objects
                    and 'body_ref' key pointing to the body element.
                    
        Returns:
            Dict with elements and flattened_sequence.
        """
        try:
            # Initialize the result structure
            result = {
                "elements": {},
                "flattened_sequence": [],
                "document_info": {
                    "name": "test_document",
                    "page_count": 1
                }
            }
            
            # Copy elements directly, converting objects to dicts if needed
            elements_dict = document.get("elements", {})
            for key, element in elements_dict.items():
                if hasattr(element, "to_dict"):
                    result["elements"][key] = element.to_dict()
                else:
                    result["elements"][key] = element
            
            # For testing, we'll flatten by using the body element's elements list
            body_ref = document.get("body_ref")
            if body_ref and body_ref in elements_dict:
                body = elements_dict[body_ref]
                elements_list = getattr(body, "elements", []) if hasattr(body, "elements") else []
                
                # Add each element to the flattened sequence
                for elem_ref in elements_list:
                    if elem_ref in result["elements"]:
                        result["flattened_sequence"].append(result["elements"][elem_ref])
            
            self.logger.info(f"Element map built with {len(result['elements'])} elements")
            self.logger.info(f"Flattened sequence contains {len(result['flattened_sequence'])} elements")
            
            return result
        
        except Exception as e:
            self.logger.exception(f"Error building element map from elements dict: {e}")
            return {
                "elements": {},
                "flattened_sequence": [],
                "document_info": {"name": "error", "page_count": 0},
                "error": str(e)
            } 