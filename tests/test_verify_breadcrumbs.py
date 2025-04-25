#!/usr/bin/env python3
"""
Test for verifying hierarchical breadcrumb generation.

This test creates a sample document with hierarchical headers and verifies that 
breadcrumbs are correctly generated in the output.
"""

import unittest
import sys
import os
import json
import shutil
import tempfile
from pathlib import Path

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the functions to test
from src.json_metadata_fixer import fix_metadata, generate_breadcrumbs


class TestHierarchicalBreadcrumbs(unittest.TestCase):
    """Test for hierarchical breadcrumb generation."""
    
    def setUp(self):
        """Set up a sample document with hierarchical headers."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a document with hierarchical headers
        self.document_data = {
            "schema_name": "DoclingDocument",
            "version": "1.3.0",
            "name": "test_breadcrumbs",
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "text": "Document Title",
                    "label": "section_header",
                    "font_size": 20
                },
                {
                    "self_ref": "#/texts/1",
                    "text": "Introduction text",
                    "label": "text"
                },
                {
                    "self_ref": "#/texts/2",
                    "text": "Chapter 1",
                    "label": "section_header",
                    "font_size": 18
                },
                {
                    "self_ref": "#/texts/3",
                    "text": "Chapter 1 content",
                    "label": "text"
                },
                {
                    "self_ref": "#/texts/4",
                    "text": "Section 1.1",
                    "label": "section_header",
                    "font_size": 16
                },
                {
                    "self_ref": "#/texts/5",
                    "text": "Section 1.1 content",
                    "label": "text"
                }
            ],
            "element_map": {
                "#/texts/0": {
                    "self_ref": "#/texts/0",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                },
                "#/texts/1": {
                    "self_ref": "#/texts/1",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                },
                "#/texts/2": {
                    "self_ref": "#/texts/2",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                },
                "#/texts/3": {
                    "self_ref": "#/texts/3",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                },
                "#/texts/4": {
                    "self_ref": "#/texts/4",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                },
                "#/texts/5": {
                    "self_ref": "#/texts/5",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field2": "",
                        "metadata": {}
                    }
                }
            },
            "body": {
                "self_ref": "#/body",
                "children": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/texts/3"},
                    {"$ref": "#/texts/4"},
                    {"$ref": "#/texts/5"}
                ],
                "content_layer": "body"
            }
        }
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_breadcrumbs(self):
        """Test that generate_breadcrumbs function builds the correct breadcrumb hierarchy."""
        # Apply the breadcrumb generation
        document_with_breadcrumbs = generate_breadcrumbs(self.document_data)
        
        # Verify breadcrumbs in the updated document
        # The introduction text should only have the document title as breadcrumb
        intro_content = document_with_breadcrumbs["element_map"]["#/texts/1"]
        expected_intro_breadcrumb = "Document Title"
        self.assertEqual(
            intro_content["extracted_metadata"]["special_field2"],
            expected_intro_breadcrumb,
            "Introduction text should have document title as breadcrumb"
        )
        
        # The Chapter 1 content should have Document Title > Chapter 1
        chapter_content = document_with_breadcrumbs["element_map"]["#/texts/3"]
        expected_chapter_breadcrumb = "Document Title > Chapter 1"
        self.assertEqual(
            chapter_content["extracted_metadata"]["special_field2"],
            expected_chapter_breadcrumb,
            "Chapter content should have document title and chapter as breadcrumb"
        )
        
        # The Section 1.1 content should have Document Title > Chapter 1 > Section 1.1
        section_content = document_with_breadcrumbs["element_map"]["#/texts/5"]
        expected_section_breadcrumb = "Document Title > Chapter 1 > Section 1.1"
        self.assertEqual(
            section_content["extracted_metadata"]["special_field2"],
            expected_section_breadcrumb,
            "Section content should have full hierarchy in breadcrumb"
        )
    
    def test_fix_metadata_with_breadcrumbs(self):
        """Test that fix_metadata applies breadcrumb generation correctly."""
        # Apply the full metadata fix
        document_with_fixes = fix_metadata(self.document_data, self.temp_dir)
        
        # Verify breadcrumbs in the final document
        # The introduction text should only have the document title as breadcrumb
        intro_content = document_with_fixes["element_map"]["#/texts/1"]
        expected_intro_breadcrumb = "Document Title"
        self.assertEqual(
            intro_content["extracted_metadata"]["special_field2"],
            expected_intro_breadcrumb,
            "Introduction text should have document title as breadcrumb"
        )
        
        # The Section 1.1 content should have the full hierarchy
        section_content = document_with_fixes["element_map"]["#/texts/5"]
        expected_section_breadcrumb = "Document Title > Chapter 1 > Section 1.1"
        self.assertEqual(
            section_content["extracted_metadata"]["special_field2"],
            expected_section_breadcrumb,
            "Section content should have full hierarchy in breadcrumb"
        )
        
        # Verify that metadata.breadcrumb is also updated
        self.assertEqual(
            section_content["extracted_metadata"]["metadata"].get("breadcrumb"),
            expected_section_breadcrumb,
            "metadata.breadcrumb should be updated with the full hierarchy"
        )


if __name__ == "__main__":
    unittest.main() 