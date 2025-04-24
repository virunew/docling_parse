#!/usr/bin/env python3
"""
Integration Test for Metadata Fixing

This test verifies that the metadata fixer is correctly integrated with the main parsing workflow.
It checks the three key fixes:
1. Image data is stored as external files
2. Proper breadcrumbs are generated for elements
3. Furniture elements are filtered from context snippets
"""

import unittest
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path for imports
src_dir = os.path.join(parent_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


class TestMetadataIntegration(unittest.TestCase):
    """Test the integration of metadata fixing in the parsing workflow."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create sample document data for testing
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
        
        # Save sample data to a test file
        self.test_json_path = os.path.join(self.output_dir, "docling_document.json")
        with open(self.test_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_data, f)
        
        # Create a mock PDF for testing
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
        
        # Save the original sys.argv
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """Clean up after test."""
        # Restore original sys.argv
        sys.argv = self.original_argv
        
        # Remove temp directory
        shutil.rmtree(self.temp_dir)
    
    @patch('parse_helper.process_pdf_document')
    def test_metadata_fixes_in_main_workflow(self, mock_process_pdf):
        """Test that metadata fixes are applied in the main workflow."""
        # Set up the mock to return a fake docling document
        mock_process_pdf.return_value = self.sample_data
        
        # Override sys.argv with test arguments
        sys.argv = [
            "parse_main.py",
            "--pdf_path", self.test_pdf_path,
            "--output_dir", self.output_dir,
            "--log_level", "ERROR"
        ]
        
        # Import and run the main function
        from parse_main import main
        result = main()
        
        # Check if execution was successful
        self.assertEqual(result, 0, "The main function should return 0 for success")
        
        # Check if the fixed_document.json was created
        fixed_json_path = os.path.join(self.output_dir, "fixed_document.json")
        self.assertTrue(os.path.exists(fixed_json_path), "Fixed document JSON file should exist")
        
        # Load the fixed document data
        with open(fixed_json_path, 'r', encoding='utf-8') as f:
            fixed_data = json.load(f)
        
        # Check if images directory was created
        images_dir = os.path.join(self.output_dir, "images")
        self.assertTrue(os.path.exists(images_dir), "Images directory should exist")
        
        # Verify FIX 1: Images are saved as external files
        # Check if any image files were created
        image_files = list(Path(images_dir).glob("*.*"))
        self.assertTrue(len(image_files) > 0, "Image files should be created")
        
        # Check if pictures have external_file references instead of inline data
        for picture in fixed_data.get("pictures", []):
            self.assertNotIn("data", picture, "Image data should not be inline in pictures")
            self.assertIn("external_file", picture, "Pictures should have external_file references")
        
        # Check if element_map has been updated with external file references
        self.assertIn("external_file", fixed_data["element_map"]["pictures_0"], 
                     "Element map should have external_file reference for images")
        
        # Verify FIX 2: Proper breadcrumbs are generated
        # Check breadcrumbs for text elements
        self.assertEqual(
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["metadata"]["breadcrumb"],
            "First Section > Subsection",
            "Text element should have correct breadcrumb"
        )
        
        # Check breadcrumbs are in special_field2
        self.assertEqual(
            fixed_data["element_map"]["texts_2"]["extracted_metadata"]["special_field2"],
            "First Section > Subsection",
            "special_field2 should contain breadcrumb"
        )
        
        # Verify FIX 3: Furniture is filtered from context
        # Check if Page Header is filtered from context_before
        for element_id in ["texts_1", "texts_2"]:
            context_before = fixed_data["element_map"][element_id]["extracted_metadata"]["metadata"]["context_before"]
            self.assertNotIn("Page Header", context_before, 
                            f"Furniture 'Page Header' should be filtered from context_before in {element_id}")
        
        # Check if Page Footer is filtered from context_after
        for element_id in ["texts_0", "texts_1", "texts_2"]:
            context_after = fixed_data["element_map"][element_id]["extracted_metadata"]["metadata"]["context_after"]
            self.assertNotIn("Page Footer", context_after, 
                            f"Furniture 'Page Footer' should be filtered from context_after in {element_id}")


if __name__ == "__main__":
    unittest.main() 