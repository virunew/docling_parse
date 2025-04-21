"""
Integration tests for the sequence_flattener module.

These tests verify that the document sequence flattener works correctly
with actual document data from parse_main.py.
"""

import os
import sys
import unittest
import tempfile
import json
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

# Import sequence flattener functions
from src.sequence_flattener import (
    get_flattened_body_sequence,
    get_element_by_reference,
    sort_sequence_by_position
)

# Try to import process_pdf_document, but don't fail if docling is not available
try:
    from src.parse_main import process_pdf_document
    DOCLING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import parse_main.process_pdf_document: {e}")
    logging.warning("Skipping tests that require docling library")
    DOCLING_AVAILABLE = False


class TestSequenceFlattenerIntegration(unittest.TestCase):
    """Integration tests for the sequence_flattener module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save original environment variables
        self.original_environ = os.environ.copy()
        
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Find a test PDF file
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_pdf_path = self.test_data_dir / "sample.pdf"
        
        # If the test PDF doesn't exist or is empty, create a more realistic sample
        # using the test PDF in the project root if it exists
        if not self.test_pdf_path.exists() or self.test_pdf_path.stat().st_size == 0:
            project_test_pdf = Path(__file__).parent.parent / "test.pdf"
            if project_test_pdf.exists() and project_test_pdf.stat().st_size > 0:
                self.test_pdf_path = project_test_pdf
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    @unittest.skipIf(not DOCLING_AVAILABLE, "Docling library not available")
    def test_sequence_flattener_with_actual_document(self):
        """Test sequence flattener with an actual document processed by parse_main."""
        # Check if we have a valid test PDF
        if not self.test_pdf_path.exists() or self.test_pdf_path.stat().st_size == 0:
            self.skipTest("No valid test PDF available")
        
        try:
            # Process the PDF document to get an element map
            element_map = process_pdf_document(
                str(self.test_pdf_path), 
                str(self.output_dir)
            )
            
            # Check that we got a valid element map
            self.assertIsNotNone(element_map)
            self.assertIsInstance(element_map, dict)
            self.assertGreater(len(element_map), 0)
            
            # Extract the document body
            # In a real document, the body would be in a specific format
            # For this test, we'll create a simple body from the element map
            document_body = []
            
            # Find elements that look like they could be part of the body 
            # (typically text, pictures, tables)
            for ref, element in element_map.items():
                element_type = element.get("metadata", {}).get("type")
                # Only include relevant element types
                if element_type in ("paragraph", "page", "picture", "table"):
                    document_body.append({"$ref": ref})
            
            # Check that we have a non-empty document body
            self.assertGreater(len(document_body), 0)
            
            # Flatten the document body
            flattened_sequence = get_flattened_body_sequence(element_map, document_body)
            
            # Check that the flattened sequence is valid
            self.assertIsNotNone(flattened_sequence)
            self.assertIsInstance(flattened_sequence, list)
            
            # The flattened sequence should contain all the elements from the document body
            self.assertEqual(len(flattened_sequence), len(document_body))
            
            # Try sorting the sequence by position
            sorted_sequence = sort_sequence_by_position(flattened_sequence)
            
            # Check that sorting didn't change the number of elements
            self.assertEqual(len(sorted_sequence), len(flattened_sequence))
            
            # Verify that elements have the expected properties
            for element in sorted_sequence:
                # Each element should have an id
                self.assertIn("id", element)
                
                # Each element should have metadata
                self.assertIn("metadata", element)
                
                # Each element should have a type in its metadata
                self.assertIn("type", element["metadata"])
                
                # The type should be one of the expected types
                self.assertIn(
                    element["metadata"]["type"], 
                    ("paragraph", "page", "picture", "table")
                )
        
        except Exception as e:
            self.fail(f"Exception occurred during test: {e}")
    
    def test_sequence_flattener_with_nested_document(self):
        """Test sequence flattener with a document that has nested elements."""
        # Create a mock element map with nested elements
        element_map = {
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
        
        # Create a document body with the top-level element
        document_body = [{"$ref": "page_1"}]
        
        # Flatten the document body
        flattened_sequence = get_flattened_body_sequence(element_map, document_body)
        
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
    
    def test_sort_sequence_with_missing_positions(self):
        """Test sorting a sequence with elements that have missing position information."""
        # Create a sequence with some elements missing position information
        sequence = [
            {
                "id": "element_1",
                "metadata": {"type": "paragraph"},
                "bounds": {"t": 30, "l": 20, "r": 120, "b": 50}
            },
            {
                "id": "element_2",
                "metadata": {"type": "paragraph"},
                # No bounds property
            },
            {
                "id": "element_3",
                "metadata": {"type": "paragraph", "bounds": {"t": 10, "l": 20, "r": 120, "b": 30}},
                # Bounds in metadata instead of at top level
            },
            {
                "id": "element_4",
                "metadata": {"type": "paragraph"},
                "bounds": {"t": 20, "l": 20, "r": 120, "b": 40}
            },
            {
                "id": "element_5",
                "metadata": {"type": "paragraph"}
                # No bounds property at all
            }
        ]
        
        # Sort the sequence
        sorted_sequence = sort_sequence_by_position(sequence)
        
        # Verify that the sequence was sorted correctly
        # Elements with a defined position should be in the correct order
        # Elements with missing position info will be at the end (with float('inf') position)
        self.assertEqual(sorted_sequence[0]["id"], "element_3")  # t=10
        self.assertEqual(sorted_sequence[1]["id"], "element_4")  # t=20
        self.assertEqual(sorted_sequence[2]["id"], "element_1")  # t=30
        
        # The remaining elements should be the ones without position info
        remaining_ids = [element["id"] for element in sorted_sequence[3:]]
        self.assertIn("element_2", remaining_ids)
        self.assertIn("element_5", remaining_ids)


if __name__ == "__main__":
    unittest.main() 