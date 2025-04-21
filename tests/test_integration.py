"""
Integration tests for docling_parse components.

This module tests the integration between different components of the docling_parse system,
including breadcrumb_generator.py and sequence_flattener.py.
"""

import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import modules to test
from breadcrumb_generator import get_hierarchical_breadcrumb


class TestBreadcrumbIntegration(unittest.TestCase):
    """Test the integration of breadcrumb generation with other components."""
    
    def setUp(self):
        """Set up test data with a mock document structure."""
        # Create a flattened document sequence that would result from processing
        # a document with element_map_builder and sequence_flattener
        self.flattened_sequence = [
            {
                "id": "texts/0",
                "self_ref": "texts/0",
                "text": "Document Title",
                "label": "section_header",
                "metadata": {"type": "h1", "level": 1}
            },
            {
                "id": "texts/1",
                "self_ref": "texts/1",
                "text": "Introduction",
                "label": "paragraph",
                "metadata": {"type": "paragraph"}
            },
            {
                "id": "texts/2",
                "self_ref": "texts/2",
                "text": "First Section",
                "label": "section_header",
                "metadata": {"type": "h2", "level": 2}
            },
            {
                "id": "texts/3",
                "self_ref": "texts/3",
                "text": "Content paragraph 1",
                "label": "paragraph",
                "metadata": {"type": "paragraph"}
            },
            {
                "id": "pictures/0",
                "self_ref": "pictures/0",
                "caption": "An example image",
                "image_data": "base64_encoded_data",
                "metadata": {"type": "picture"}
            },
            {
                "id": "texts/4",
                "self_ref": "texts/4",
                "text": "Subsection 1.1",
                "label": "section_header",
                "metadata": {"type": "h3", "level": 3}
            },
            {
                "id": "texts/5",
                "self_ref": "texts/5",
                "text": "Content paragraph 2",
                "label": "paragraph",
                "metadata": {"type": "paragraph"}
            },
            {
                "id": "tables/0",
                "self_ref": "tables/0",
                "caption": "Sample Table",
                "data": [["Header 1", "Header 2"], ["Row 1 Col 1", "Row 1 Col 2"]],
                "metadata": {"type": "table"}
            }
        ]
    
    def test_breadcrumb_with_flattened_sequence(self):
        """Test that breadcrumb generation works with the flattened sequence."""
        # Generate breadcrumb for the paragraph under the subsection
        paragraph_element = self.flattened_sequence[6]  # Content paragraph 2
        breadcrumb = get_hierarchical_breadcrumb(paragraph_element, self.flattened_sequence)
        
        # Check the breadcrumb is as expected
        self.assertEqual(breadcrumb, "Document Title > First Section > Subsection 1.1")
        
        # Generate breadcrumb for the table (should also include all header context)
        table_element = self.flattened_sequence[7]  # Sample Table
        table_breadcrumb = get_hierarchical_breadcrumb(table_element, self.flattened_sequence)
        self.assertEqual(table_breadcrumb, "Document Title > First Section > Subsection 1.1")
        
        # Generate breadcrumb for a paragraph under a section but not a subsection
        section_paragraph = self.flattened_sequence[3]  # Content paragraph 1
        section_breadcrumb = get_hierarchical_breadcrumb(section_paragraph, self.flattened_sequence)
        self.assertEqual(section_breadcrumb, "Document Title > First Section")
        
        # Test breadcrumb for an element at the start (should just have document title)
        intro_paragraph = self.flattened_sequence[1]  # Introduction
        intro_breadcrumb = get_hierarchical_breadcrumb(intro_paragraph, self.flattened_sequence)
        self.assertEqual(intro_breadcrumb, "Document Title")


if __name__ == "__main__":
    unittest.main() 