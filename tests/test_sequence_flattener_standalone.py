"""
Standalone tests for the sequence_flattener module.

These tests verify that the document sequence flattener correctly 
processes document structures into linear sequences without requiring the docling library.
"""

import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.sequence_flattener import (
    get_flattened_body_sequence,
    get_element_by_reference,
    sort_sequence_by_position
)


class TestSequenceFlattenerStandalone(unittest.TestCase):
    """Standalone tests for the sequence_flattener module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock element map with nested elements
        self.element_map = {
            "page_1": {
                "id": "page_1",
                "metadata": {"type": "page", "page_number": 1},
                "children": [
                    {"$ref": "page_1_section_1"},
                    {"$ref": "page_1_section_2"}
                ]
            },
            "page_1_section_1": {
                "id": "page_1_section_1",
                "metadata": {"type": "section", "page_number": 1},
                "children": [
                    {"$ref": "page_1_section_1_para_1"},
                    {"$ref": "page_1_section_1_para_2"}
                ]
            },
            "page_1_section_2": {
                "id": "page_1_section_2",
                "metadata": {"type": "section", "page_number": 1},
                "children": [
                    {"$ref": "page_1_section_2_para_1"},
                    {"$ref": "page_1_section_2_image_1"}
                ]
            },
            "page_1_section_1_para_1": {
                "id": "page_1_section_1_para_1",
                "metadata": {"type": "paragraph", "page_number": 1},
                "text": "This is paragraph 1 in section 1",
                "children": []
            },
            "page_1_section_1_para_2": {
                "id": "page_1_section_1_para_2",
                "metadata": {"type": "paragraph", "page_number": 1},
                "text": "This is paragraph 2 in section 1",
                "children": []
            },
            "page_1_section_2_para_1": {
                "id": "page_1_section_2_para_1",
                "metadata": {"type": "paragraph", "page_number": 1},
                "text": "This is paragraph 1 in section 2",
                "children": []
            },
            "page_1_section_2_image_1": {
                "id": "page_1_section_2_image_1",
                "metadata": {"type": "picture", "page_number": 1},
                "image_path": "sample_image.png",
                "children": []
            }
        }
        
        # Create a mock document body with just the top-level element
        self.document_body = [{"$ref": "page_1"}]
        
        # Create a mock body with all elements at the same level
        self.flat_document_body = [
            {"$ref": "page_1_section_1_para_1"},
            {"$ref": "page_1_section_1_para_2"},
            {"$ref": "page_1_section_2_para_1"},
            {"$ref": "page_1_section_2_image_1"}
        ]
        
        # Create an element map with elements that have position information
        self.positioned_elements = {
            "element_1": {
                "id": "element_1",
                "metadata": {"type": "paragraph"},
                "bounds": {"t": 30, "l": 20, "r": 120, "b": 50}
            },
            "element_2": {
                "id": "element_2",
                "metadata": {"type": "paragraph"},
                # No bounds property
            },
            "element_3": {
                "id": "element_3",
                "metadata": {"type": "paragraph", "bounds": {"t": 10, "l": 20, "r": 120, "b": 30}},
                # Bounds in metadata instead of at top level
            },
            "element_4": {
                "id": "element_4",
                "metadata": {"type": "paragraph"},
                "bounds": {"t": 20, "l": 20, "r": 120, "b": 40}
            },
            "element_5": {
                "id": "element_5",
                "metadata": {"type": "paragraph"}
                # No bounds property at all
            }
        }
        
        self.positioned_body = [
            {"$ref": "element_1"},
            {"$ref": "element_2"},
            {"$ref": "element_3"},
            {"$ref": "element_4"},
            {"$ref": "element_5"}
        ]
    
    def test_get_element_by_reference(self):
        """Test getting elements by reference."""
        # Test with a valid reference
        element = get_element_by_reference(self.element_map, "page_1")
        self.assertIsNotNone(element)
        self.assertEqual(element["id"], "page_1")
        
        # Test with a reference that doesn't exist
        element = get_element_by_reference(self.element_map, "nonexistent")
        self.assertIsNone(element)
    
    def test_sort_sequence_by_position(self):
        """Test sorting sequences by position."""
        # Create a list of elements in random order
        unsorted_sequence = [
            self.positioned_elements["element_1"],
            self.positioned_elements["element_3"],
            self.positioned_elements["element_4"],
            self.positioned_elements["element_2"],
            self.positioned_elements["element_5"]
        ]
        
        # Sort the sequence
        sorted_sequence = sort_sequence_by_position(unsorted_sequence)
        
        # Verify the correct order (by top position, then left)
        self.assertEqual(sorted_sequence[0]["id"], "element_3")  # t=10
        self.assertEqual(sorted_sequence[1]["id"], "element_4")  # t=20
        self.assertEqual(sorted_sequence[2]["id"], "element_1")  # t=30
        
        # The remaining elements should be the ones without position info
        remaining_ids = [element["id"] for element in sorted_sequence[3:]]
        self.assertIn("element_2", remaining_ids)
        self.assertIn("element_5", remaining_ids)
    
    def test_get_flattened_body_sequence_with_nested_structure(self):
        """Test flattening a document body with nested elements."""
        # Flatten the sequence
        flattened_sequence = get_flattened_body_sequence(self.element_map, self.document_body)
        
        # Check that the flattened sequence contains all elements
        # 1 page + 2 sections + 3 paragraphs + 1 image = 7 elements
        self.assertEqual(len(flattened_sequence), 7)
        
        # Verify that all element IDs are in the flattened sequence
        element_ids = [element["id"] for element in flattened_sequence]
        expected_ids = [
            "page_1",
            "page_1_section_1",
            "page_1_section_1_para_1",
            "page_1_section_1_para_2",
            "page_1_section_2",
            "page_1_section_2_para_1",
            "page_1_section_2_image_1"
        ]
        
        # Check that all expected IDs are present
        for expected_id in expected_ids:
            self.assertIn(expected_id, element_ids)
    
    def test_get_flattened_body_sequence_with_flat_structure(self):
        """Test flattening a document body with a flat structure."""
        # Flatten the sequence
        flattened_sequence = get_flattened_body_sequence(self.element_map, self.flat_document_body)
        
        # Check that the flattened sequence contains all elements (4 elements with no nesting)
        self.assertEqual(len(flattened_sequence), 4)
        
        # Verify that all element IDs are in the flattened sequence
        element_ids = [element["id"] for element in flattened_sequence]
        expected_ids = [
            "page_1_section_1_para_1",
            "page_1_section_1_para_2",
            "page_1_section_2_para_1",
            "page_1_section_2_image_1"
        ]
        
        # Check that all expected IDs are present
        for expected_id in expected_ids:
            self.assertIn(expected_id, element_ids)
    
    def test_get_flattened_body_sequence_with_positioned_elements(self):
        """Test flattening a document body with elements that have position information."""
        # Flatten the sequence
        flattened_sequence = get_flattened_body_sequence(self.positioned_elements, self.positioned_body)
        
        # Check that the flattened sequence contains all elements
        self.assertEqual(len(flattened_sequence), 5)
        
        # Sort the flattened sequence by position
        sorted_sequence = sort_sequence_by_position(flattened_sequence)
        
        # Verify the correct order (by top position, then left)
        self.assertEqual(sorted_sequence[0]["id"], "element_3")  # t=10
        self.assertEqual(sorted_sequence[1]["id"], "element_4")  # t=20
        self.assertEqual(sorted_sequence[2]["id"], "element_1")  # t=30
        
        # The remaining elements should be the ones without position info
        remaining_ids = [element["id"] for element in sorted_sequence[3:]]
        self.assertIn("element_2", remaining_ids)
        self.assertIn("element_5", remaining_ids)
    
    def test_get_flattened_body_sequence_empty_inputs(self):
        """Test flattening with empty inputs."""
        # Test with empty element map
        flattened = get_flattened_body_sequence({}, self.document_body)
        self.assertEqual(flattened, [])
        
        # Test with empty body
        flattened = get_flattened_body_sequence(self.element_map, [])
        self.assertEqual(flattened, [])
    
    def test_get_flattened_body_sequence_invalid_references(self):
        """Test flattening with invalid references."""
        # Create a body with nonexistent references
        invalid_body = [
            {"$ref": "page_1_section_1_para_1"},
            {"$ref": "nonexistent"},
            {"$ref": "page_1_section_2_image_1"}
        ]
        
        # Flatten the sequence (should skip the invalid reference)
        flattened = get_flattened_body_sequence(self.element_map, invalid_body)
        
        # Check the result (only 2 valid references should be processed)
        self.assertEqual(len(flattened), 2)
        
        # Verify that the valid elements are in the flattened sequence
        element_ids = [element["id"] for element in flattened]
        self.assertIn("page_1_section_1_para_1", element_ids)
        self.assertIn("page_1_section_2_image_1", element_ids)
        
        # Verify that the invalid reference is not in the flattened sequence
        self.assertNotIn("nonexistent", element_ids)


if __name__ == "__main__":
    unittest.main() 