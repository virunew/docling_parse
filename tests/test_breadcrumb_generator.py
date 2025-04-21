"""
Tests for the breadcrumb generator functionality.

This module contains tests to verify that breadcrumb generation works correctly
across various document structures and heading configurations.
"""

import unittest
import sys
import os
from pathlib import Path

# Add the src directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import the breadcrumb generator functions
from breadcrumb_generator import get_hierarchical_breadcrumb, get_breadcrumb_with_fallback


class TestBreadcrumbGenerator(unittest.TestCase):
    """Test cases for the breadcrumb generator functions."""
    
    def setUp(self):
        """Set up test data with sample document structures."""
        # Sample document sequence with various heading levels
        self.sample_sequence = [
            {"id": "h1_1", "text": "Document Title", "metadata": {"type": "h1"}, "label": "section_header"},
            {"id": "p1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}},
            {"id": "h2_1", "text": "Section 1", "metadata": {"type": "h2"}, "label": "section_header"},
            {"id": "p2", "text": "Paragraph 2", "metadata": {"type": "paragraph"}},
            {"id": "h3_1", "text": "Subsection 1.1", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}},
            {"id": "h2_2", "text": "Section 2", "metadata": {"type": "h2"}, "label": "section_header"},
            {"id": "p4", "text": "Paragraph 4", "metadata": {"type": "paragraph"}},
            {"id": "h3_2", "text": "Subsection 2.1", "metadata": {"type": "h3"}, "label": "section_header"},
            {"id": "p5", "text": "Paragraph 5", "metadata": {"type": "paragraph"}},
            {"id": "table1", "metadata": {"type": "table"}, "label": "table"},
        ]
        
        # Document with alternative heading formats
        self.alt_heading_sequence = [
            {"id": "title", "text": "Main Title", "metadata": {"type": "section_header", "level": "1"}},
            {"id": "intro", "text": "Introduction", "metadata": {"type": "paragraph"}},
            {"id": "section1", "text": "First Section", "metadata": {"type": "section_header", "level": "2"}},
            {"id": "content1", "text": "Content 1", "metadata": {"type": "paragraph"}},
            {"id": "subsection1", "text": "First Subsection", "metadata": {"type": "section_header", "level": "3"}},
            {"id": "content2", "text": "Content 2", "metadata": {"type": "paragraph"}},
        ]
        
        # Document with no headings
        self.no_headings_sequence = [
            {"id": "p1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}},
            {"id": "p2", "text": "Paragraph 2", "metadata": {"type": "paragraph"}},
            {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}},
        ]
        
        # Document with self_ref instead of id
        self.self_ref_sequence = [
            {"self_ref": "#/texts/0", "text": "Document Title", "metadata": {"type": "h1"}, "label": "section_header"},
            {"self_ref": "#/texts/1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}},
            {"self_ref": "#/texts/2", "text": "Section 1", "metadata": {"type": "h2"}, "label": "section_header"},
            {"self_ref": "#/texts/3", "text": "Paragraph 2", "metadata": {"type": "paragraph"}},
        ]

    def test_basic_breadcrumb(self):
        """Test basic breadcrumb generation for a paragraph in a section."""
        element = {"id": "p2", "text": "Paragraph 2", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Section 1")
    
    def test_deeper_breadcrumb(self):
        """Test breadcrumb generation for a paragraph in a subsection."""
        element = {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Section 1 > Subsection 1.1")
    
    def test_different_section_breadcrumb(self):
        """Test breadcrumb generation for a paragraph in a different section."""
        element = {"id": "p5", "text": "Paragraph 5", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Section 2 > Subsection 2.1")
    
    def test_table_breadcrumb(self):
        """Test breadcrumb generation for a table element."""
        element = {"id": "table1", "metadata": {"type": "table"}, "label": "table"}
        breadcrumb = get_hierarchical_breadcrumb(element, self.sample_sequence)
        self.assertEqual(breadcrumb, "Document Title > Section 2 > Subsection 2.1")
    
    def test_alternative_heading_format(self):
        """Test breadcrumb generation with alternative heading format."""
        element = {"id": "content2", "text": "Content 2", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.alt_heading_sequence)
        self.assertEqual(breadcrumb, "Main Title > First Section > First Subsection")
    
    def test_no_headings(self):
        """Test breadcrumb generation when no headings are present."""
        element = {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.no_headings_sequence)
        self.assertEqual(breadcrumb, "")
    
    def test_fallback_to_document_title(self):
        """Test breadcrumb fallback to document title when no headings found."""
        element = {"id": "p3", "text": "Paragraph 3", "metadata": {"type": "paragraph"}}
        breadcrumb = get_breadcrumb_with_fallback(element, self.no_headings_sequence, "Test Document")
        self.assertEqual(breadcrumb, "Test Document")
    
    def test_self_ref_sequence(self):
        """Test breadcrumb generation with self_ref instead of id."""
        element = {"self_ref": "#/texts/3", "text": "Paragraph 2", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.self_ref_sequence)
        self.assertEqual(breadcrumb, "Document Title > Section 1")
    
    def test_element_not_in_sequence(self):
        """Test breadcrumb generation when element is not in sequence."""
        element = {"id": "not_in_sequence", "text": "Missing Element", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, self.sample_sequence)
        self.assertEqual(breadcrumb, "")
    
    def test_empty_inputs(self):
        """Test breadcrumb generation with empty inputs."""
        # Empty element
        breadcrumb = get_hierarchical_breadcrumb({}, self.sample_sequence)
        self.assertEqual(breadcrumb, "")
        
        # Empty sequence
        element = {"id": "p1", "text": "Paragraph 1", "metadata": {"type": "paragraph"}}
        breadcrumb = get_hierarchical_breadcrumb(element, [])
        self.assertEqual(breadcrumb, "")
        
        # Both empty
        breadcrumb = get_hierarchical_breadcrumb({}, [])
        self.assertEqual(breadcrumb, "")


if __name__ == "__main__":
    unittest.main() 