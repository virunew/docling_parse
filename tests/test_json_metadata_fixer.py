#!/usr/bin/env python3
"""
Test for JSON Metadata Fixer

Tests the functionality of the json_metadata_fixer module:
1. Image reference extraction
2. Breadcrumb generation
3. Furniture filtering from context
"""

import unittest
import os
import json
import sys
import shutil
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

# Adjust path to import local modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from src.json_metadata_fixer import (
    fix_metadata,
    fix_image_references,
    generate_breadcrumbs,
    filter_furniture_from_context,
    determine_header_level,
    get_element_position,
    build_breadcrumb_path,
    filter_context
)

class TestJsonMetadataFixer(unittest.TestCase):
    """Test cases for JSON Metadata Fixer."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a sample document data for testing
        self.sample_data = {
            "source_metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf"
            },
            "texts": [
                {
                    "self_ref": "#/texts/0",
                    "label": "section_header",
                    "text": "First Section",
                    "font_size": 18,
                    "is_bold": True
                },
                {
                    "self_ref": "#/texts/1",
                    "label": "section_header",
                    "text": "Subsection",
                    "font_size": 16,
                    "is_bold": False
                },
                {
                    "self_ref": "#/texts/2",
                    "label": "text",
                    "text": "Some content text"
                }
            ],
            "pictures": [
                {
                    "self_ref": "#/pictures/0",
                    "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                }
            ],
            "furniture": [
                {
                    "self_ref": "#/furniture/0",
                    "text": "Page Header"
                },
                {
                    "self_ref": "#/furniture/1",
                    "text": "Page Footer"
                }
            ],
            "body": {
                "elements": [
                    {"$ref": "#/texts/0"},
                    {"$ref": "#/texts/1"},
                    {"$ref": "#/texts/2"},
                    {"$ref": "#/pictures/0"}
                ]
            },
            "element_map": {
                "texts_0": {
                    "self_ref": "#/texts/0",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field1": "{'breadcrumb': '', 'context_before': 'Page Header Some content', 'context_after': 'Some more content Page Footer'}",
                        "special_field2": "",
                        "metadata": {
                            "breadcrumb": "",
                            "context_before": "Page Header Some content",
                            "context_after": "Some more content Page Footer"
                        }
                    }
                },
                "texts_1": {
                    "self_ref": "#/texts/1",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field1": "{'breadcrumb': '', 'context_before': 'First Section Page Header', 'context_after': 'Some content Page Footer'}",
                        "special_field2": "",
                        "metadata": {
                            "breadcrumb": "",
                            "context_before": "First Section Page Header",
                            "context_after": "Some content Page Footer"
                        }
                    }
                },
                "texts_2": {
                    "self_ref": "#/texts/2",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field1": "{'breadcrumb': '', 'context_before': 'Subsection Page Header', 'context_after': 'Page Footer'}",
                        "special_field2": "",
                        "metadata": {
                            "breadcrumb": "",
                            "context_before": "Subsection Page Header",
                            "context_after": "Page Footer"
                        }
                    }
                },
                "pictures_0": {
                    "self_ref": "#/pictures/0",
                    "content_layer": "body",
                    "extracted_metadata": {
                        "special_field1": "{'breadcrumb': '', 'context_before': 'Some content text Page Header', 'docling_label': 'picture', 'docling_ref': '#/pictures/0'}",
                        "special_field2": "",
                        "metadata": {
                            "breadcrumb": "",
                            "context_before": "Some content text Page Header",
                            "docling_label": "picture",
                            "docling_ref": "#/pictures/0"
                        }
                    }
                },
                "furniture_0": {
                    "self_ref": "#/furniture/0",
                    "content_layer": "furniture"
                },
                "furniture_1": {
                    "self_ref": "#/furniture/1",
                    "content_layer": "furniture"
                }
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_fix_image_references(self):
        """Test image reference extraction and saving."""
        # Test the fix_image_references function
        images_dir = Path(self.temp_dir) / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Run the function
        fixed_data = fix_image_references(self.sample_data, images_dir)
        
        # Verify results
        # 1. Image file should be saved
        image_files = list(images_dir.glob("*.png"))
        self.assertTrue(len(image_files) > 0, "No image file was saved")
        
        # 2. Data URI should be removed
        self.assertNotIn("data", fixed_data["pictures"][0], "Data URI was not removed")
        
        # 3. External file reference should be added
        self.assertIn("external_file", fixed_data["pictures"][0], "External file reference not added")
        
        # 4. Element map should be updated
        self.assertIn("external_file", fixed_data["element_map"]["pictures_0"], "Element map not updated with external file")
    
    def test_generate_breadcrumbs(self):
        """Test breadcrumb generation based on section headers."""
        # Test the generate_breadcrumbs function
        fixed_data = generate_breadcrumbs(self.sample_data)
        
        # Verify results
        # Check breadcrumb for text element
        self.assertEqual(
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["breadcrumb"],
            "First Section > Subsection",
            "Incorrect breadcrumb generated for text element"
        )
        
        # Check breadcrumb for image element
        self.assertEqual(
            fixed_data["element_map"]["pictures_0"]["extracted_metadata"]["metadata"]["breadcrumb"],
            "First Section > Subsection",
            "Incorrect breadcrumb generated for image element"
        )
    
    def test_filter_furniture_from_context(self):
        """Test filtering furniture elements from context text."""
        # Test the filter_furniture_from_context function
        fixed_data = filter_furniture_from_context(self.sample_data)
        
        # Verify results
        # Check context_before for text element
        self.assertNotIn(
            "Page Header",
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["context_before"],
            "Furniture not filtered from context_before"
        )
        
        # Check context_after for text element
        self.assertNotIn(
            "Page Footer",
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["context_after"],
            "Furniture not filtered from context_after"
        )
    
    def test_determine_header_level(self):
        """Test determining header level from element attributes."""
        # Test various header configurations
        h1 = {"label": "section_header", "font_size": 20, "is_bold": True}
        h2 = {"label": "header", "font_size": 16, "is_bold": True}
        h3 = {"label": "section_header", "font_size": 14, "is_bold": False}
        h4 = {"label": "h4", "font_size": 12}
        
        self.assertEqual(determine_header_level(h1), 1, "H1 detection failed")
        self.assertEqual(determine_header_level(h2), 2, "H2 detection failed")
        self.assertEqual(determine_header_level(h3), 3, "H3 detection failed")
        self.assertEqual(determine_header_level(h4), 4, "H4 detection failed")
    
    def test_build_breadcrumb_path(self):
        """Test building a breadcrumb path from header list."""
        # Test headers at different levels
        headers = [
            {"id": 0, "text": "Document Title", "level": 1, "ref": "#/texts/0"},
            {"id": 1, "text": "Chapter 1", "level": 2, "ref": "#/texts/1"},
            {"id": 2, "text": "Section 1.1", "level": 3, "ref": "#/texts/2"}
        ]
        
        # Element after all headers
        self.assertEqual(
            build_breadcrumb_path(headers, 3),
            "Document Title > Chapter 1 > Section 1.1",
            "Failed to build complete breadcrumb path"
        )
        
        # Element after first header only
        self.assertEqual(
            build_breadcrumb_path(headers, 1),
            "Document Title",
            "Failed to build partial breadcrumb path"
        )
    
    def test_filter_context(self):
        """Test filtering furniture text from context string."""
        context = "Page Header Some important content Page Footer"
        furniture_texts = {"Page Header", "Page Footer"}
        
        filtered = filter_context(context, furniture_texts)
        
        self.assertEqual(filtered, "Some important content", "Failed to filter furniture from context")
    
    def test_fix_metadata_integration(self):
        """Test the full metadata fixing process."""
        # Test the fix_metadata function which integrates all fixes
        fixed_data = fix_metadata(self.sample_data, self.temp_dir)
        
        # Verify all fixes were applied
        # 1. Image references fixed
        self.assertIn("external_file", fixed_data["pictures"][0], "Image references not fixed")
        
        # 2. Breadcrumbs generated
        self.assertEqual(
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["breadcrumb"],
            "First Section > Subsection",
            "Breadcrumbs not generated"
        )
        
        # 3. Context filtered
        self.assertNotIn(
            "Page Header",
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["context_before"],
            "Context not filtered"
        )


if __name__ == "__main__":
    unittest.main() 