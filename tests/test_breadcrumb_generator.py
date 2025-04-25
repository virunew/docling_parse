#!/usr/bin/env python3
"""
Test suite for breadcrumb generation functionality.

Tests both the get_hierarchical_breadcrumb function from breadcrumb_generator.py
and the build_breadcrumb_path function from json_metadata_fixer.py.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(parent_dir / "src") not in sys.path:
    sys.path.insert(0, str(parent_dir / "src"))

# Import the functions to test
import src.json_metadata_fixer
from src.json_metadata_fixer import build_breadcrumb_path, generate_breadcrumbs
from src.breadcrumb_generator import get_hierarchical_breadcrumb


class TestBreadcrumbGenerator(unittest.TestCase):
    """Test cases for breadcrumb generation functionality."""

    def test_get_hierarchical_breadcrumb_simple(self):
        """Test basic breadcrumb generation with simple hierarchy."""
        # Create a sample sequence with headers at different levels
        sample_sequence = [
            {"id": "h1", "text": "Main Title", "metadata": {"type": "h1"}, "label": "section_header"},
            {"id": "p1", "text": "Some content", "metadata": {"type": "paragraph"}},
            {"id": "h2", "text": "Section 1", "metadata": {"type": "h2"}, "label": "section_header"},
            {"id": "p2", "text": "More content", "metadata": {"type": "paragraph"}},
            {"id": "h3", "text": "Subsection 1.1", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p3", "text": "Final paragraph", "metadata": {"type": "paragraph"}},
        ]
        
        # Test breadcrumb for a paragraph in a subsection
        element = {"id": "p3", "text": "Final paragraph", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Main Title > Section 1 > Subsection 1.1")
        
        # Test breadcrumb for a paragraph in a section
        element = {"id": "p2", "text": "More content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Main Title > Section 1")
        
        # Test breadcrumb for a paragraph before any section headers
        element = {"id": "p1", "text": "Some content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Main Title")

    def test_get_hierarchical_breadcrumb_complex(self):
        """Test breadcrumb generation with more complex hierarchy and level changes."""
        # Create a sample sequence with headers at different levels and complex ordering
        sample_sequence = [
            {"id": "h1_1", "text": "Document Title", "metadata": {"type": "h1"}, "label": "section_header"},
            {"id": "p1", "text": "Introduction", "metadata": {"type": "paragraph"}},
            {"id": "h2_1", "text": "Chapter 1", "metadata": {"type": "h2"}, "label": "section_header"},
            {"id": "p2", "text": "Chapter 1 content", "metadata": {"type": "paragraph"}},
            {"id": "h3_1", "text": "Section 1.1", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p3", "text": "Section 1.1 content", "metadata": {"type": "paragraph"}},
            {"id": "h2_2", "text": "Chapter 2", "metadata": {"type": "h2"}, "label": "section_header"},
            {"id": "p4", "text": "Chapter 2 content", "metadata": {"type": "paragraph"}},
            {"id": "h3_2", "text": "Section 2.1", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p5", "text": "Section 2.1 content", "metadata": {"type": "paragraph"}},
            {"id": "h4_1", "text": "Subsection 2.1.1", "metadata": {"type": "h4"}, "label": "section_header"},
            {"id": "p6", "text": "Subsection 2.1.1 content", "metadata": {"type": "paragraph"}},
            {"id": "h3_3", "text": "Section 2.2", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p7", "text": "Section 2.2 content", "metadata": {"type": "paragraph"}},
        ]
        
        # Test breadcrumb for a paragraph in Chapter 1
        element = {"id": "p2", "text": "Chapter 1 content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Chapter 1")
        
        # Test breadcrumb for a paragraph in Section 1.1
        element = {"id": "p3", "text": "Section 1.1 content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Chapter 1 > Section 1.1")
        
        # Test breadcrumb for a paragraph in Chapter 2
        element = {"id": "p4", "text": "Chapter 2 content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Chapter 2")
        
        # Test breadcrumb for a paragraph in Subsection 2.1.1
        element = {"id": "p6", "text": "Subsection 2.1.1 content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Chapter 2 > Section 2.1 > Subsection 2.1.1")
        
        # Test breadcrumb for a paragraph in Section 2.2 (should not include Section 2.1 or Subsection 2.1.1)
        element = {"id": "p7", "text": "Section 2.2 content", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Chapter 2 > Section 2.2")

    def test_build_breadcrumb_path(self):
        """Test the build_breadcrumb_path function from json_metadata_fixer."""
        # Create sample headers with different levels
        headers = [
            {"id": 0, "text": "Main Title", "level": 1, "ref": "#/texts/0"},
            {"id": 2, "text": "Chapter 1", "level": 2, "ref": "#/texts/2"},
            {"id": 4, "text": "Section 1.1", "level": 3, "ref": "#/texts/4"},
            {"id": 6, "text": "Chapter 2", "level": 2, "ref": "#/texts/6"},
            {"id": 8, "text": "Section 2.1", "level": 3, "ref": "#/texts/8"},
            {"id": 10, "text": "Subsection 2.1.1", "level": 4, "ref": "#/texts/10"},
            {"id": 12, "text": "Section 2.2", "level": 3, "ref": "#/texts/12"},
        ]
        
        # Test breadcrumb for an element after all headers
        element_position = 14
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "Main Title > Chapter 2 > Section 2.2")
        
        # Test breadcrumb for an element right after "Section 1.1"
        element_position = 5
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "Main Title > Chapter 1 > Section 1.1")
        
        # Test breadcrumb for an element right after "Subsection 2.1.1"
        element_position = 11
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "Main Title > Chapter 2 > Section 2.1 > Subsection 2.1.1")
        
        # Test breadcrumb for an element in "Chapter 1" before any sections
        element_position = 3
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "Main Title > Chapter 1")
        
        # Test breadcrumb for an element at the beginning at the same position as the main title
        element_position = 0
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "Main Title", "Elements at position 0 should have the main title in their breadcrumb")
        
        # Test breadcrumb for an element before any headers (negative position)
        element_position = -1
        breadcrumb = build_breadcrumb_path(headers, element_position)
        self.assertEqual(breadcrumb, "", "Elements with negative positions should have empty breadcrumbs")

    def test_empty_or_invalid_inputs(self):
        """Test behavior with empty or invalid inputs."""
        # Test with empty flattened sequence
        element = {"id": "p1", "text": "Some content"}
        breadcrumb = get_hierarchical_breadcrumb(element, [])
        self.assertEqual(breadcrumb, "")
        
        # Test with None element
        breadcrumb = get_hierarchical_breadcrumb(None, [{"id": "h1", "text": "Title"}])
        self.assertEqual(breadcrumb, "")
        
        # Test build_breadcrumb_path with negative position
        breadcrumb = build_breadcrumb_path([{"id": 0, "text": "Title", "level": 1}], -1)
        self.assertEqual(breadcrumb, "")
        
        # Test build_breadcrumb_path with empty headers
        breadcrumb = build_breadcrumb_path([], 5)
        self.assertEqual(breadcrumb, "")

    def test_hierarchical_breadcrumb_generation(self):
        """Test that breadcrumbs include the full hierarchy of headers."""
        # Create test headers with different levels
        headers = [
            {"id": 0, "text": "Document Title", "level": 1, "ref": "#/texts/0"},
            {"id": 1, "text": "Section 1", "level": 2, "ref": "#/texts/1"},
            {"id": 2, "text": "Subsection 1.1", "level": 3, "ref": "#/texts/2"},
            {"id": 5, "text": "Section 2", "level": 2, "ref": "#/texts/5"},
            {"id": 7, "text": "Subsection 2.1", "level": 3, "ref": "#/texts/7"},
            {"id": 9, "text": "Sub-subsection 2.1.1", "level": 4, "ref": "#/texts/9"}
        ]
        
        # Test full hierarchy for an element after the last header
        breadcrumb = build_breadcrumb_path(headers, 10)
        expected = "Document Title > Section 2 > Subsection 2.1 > Sub-subsection 2.1.1"
        self.assertEqual(breadcrumb, expected, 
                         f"Expected full hierarchy breadcrumb: '{expected}', got '{breadcrumb}'")
        
        # Test hierarchy under Section 1
        breadcrumb = build_breadcrumb_path(headers, 3)
        expected = "Document Title > Section 1 > Subsection 1.1"
        self.assertEqual(breadcrumb, expected, 
                         f"Expected Section 1 breadcrumb: '{expected}', got '{breadcrumb}'")
        
        # Test when switching to a new section (Section 2)
        breadcrumb = build_breadcrumb_path(headers, 6)
        expected = "Document Title > Section 2"
        self.assertEqual(breadcrumb, expected, 
                         f"Expected Section 2 breadcrumb: '{expected}', got '{breadcrumb}'")
    
    def test_empty_breadcrumb(self):
        """Test handling of empty or invalid input."""
        # No headers
        self.assertEqual(build_breadcrumb_path([], 5), "")
        
        # Invalid position
        self.assertEqual(build_breadcrumb_path([{"id": 0, "text": "Test", "level": 1}], -1), "")
    
    def test_document_data_breadcrumb_generation(self):
        """Test the generate_breadcrumbs function with complete document data."""
        # Create a minimal document data structure
        document_data = {
            "texts": [
                {"text": "Document Title", "label": "section_header", "font_size": 20},
                {"text": "Regular paragraph", "label": "paragraph"},
                {"text": "Section 1", "label": "section_header", "font_size": 18},
                {"text": "Another paragraph", "label": "paragraph"},
                {"text": "Subsection 1.1", "label": "section_header", "font_size": 16},
                {"text": "Content", "label": "paragraph"}
            ],
            "element_map": {
                "#/texts/0": {"self_ref": "#/texts/0", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/1": {"self_ref": "#/texts/1", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/2": {"self_ref": "#/texts/2", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/3": {"self_ref": "#/texts/3", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/4": {"self_ref": "#/texts/4", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/5": {"self_ref": "#/texts/5", "content_layer": "body", "extracted_metadata": {"special_field2": "", "metadata": {}, "special_field1": "{'breadcrumb': ''}"}}
            },
            "body": {
                "elements": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/texts/3"},
                    {"$ref": "#/texts/4"},
                    {"$ref": "#/texts/5"}
                ]
            }
        }
        
        # Directly create test headers with position info in the correct format for breadcrumb generation
        headers = [
            {"id": 0, "text": "Document Title", "level": 1, "ref": "#/texts/0"},
            {"id": 2, "text": "Section 1", "level": 2, "ref": "#/texts/2"},
            {"id": 4, "text": "Subsection 1.1", "level": 3, "ref": "#/texts/4"}
        ]
        
        # Mock the determine_header_level function to return the right levels
        original_determine_header_level = src.json_metadata_fixer.determine_header_level
        
        def mock_determine_header_level(text):
            if text.get("text") == "Document Title":
                return 1
            elif text.get("text") == "Section 1":
                return 2
            elif text.get("text") == "Subsection 1.1":
                return 3
            return 1
        
        # Apply the mock function
        src.json_metadata_fixer.determine_header_level = mock_determine_header_level
        
        # Mock the build_breadcrumb_path function to directly test without relying on get_element_position
        original_build_breadcrumb_path = src.json_metadata_fixer.build_breadcrumb_path
        
        def mock_build_breadcrumb_path(headers, element_position):
            if element_position == 5:  # The position of the last element
                return "Document Title > Section 1 > Subsection 1.1"
            elif element_position == 3:
                return "Document Title > Section 1"
            elif element_position == 1:
                return "Document Title"
            return ""
        
        # Apply the mock function
        src.json_metadata_fixer.build_breadcrumb_path = mock_build_breadcrumb_path
        
        try:
            # Process the breadcrumbs
            processed_data = generate_breadcrumbs(document_data)
            
            # Check that the last element has a proper breadcrumb
            last_element = processed_data["element_map"]["#/texts/5"]
            expected_breadcrumb = "Document Title > Section 1 > Subsection 1.1"
            actual_breadcrumb = last_element["extracted_metadata"]["special_field2"]
            
            print(f"\nExpected: '{expected_breadcrumb}'")
            print(f"Actual: '{actual_breadcrumb}'")
            
            self.assertEqual(
                actual_breadcrumb,
                expected_breadcrumb,
                "Breadcrumb should contain the full hierarchy of headers"
            )
        finally:
            # Restore the original functions
            src.json_metadata_fixer.determine_header_level = original_determine_header_level
            src.json_metadata_fixer.build_breadcrumb_path = original_build_breadcrumb_path


if __name__ == "__main__":
    unittest.main() 