#!/usr/bin/env python3
"""
Integration test for breadcrumb generation in parse_main.py

Tests that parse_main.py correctly applies the breadcrumb hierarchy fixes.
"""

import unittest
import sys
import os
import json
import shutil
import tempfile
from pathlib import Path
import subprocess

# Add parent directory to path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import the module to test
import parse_main
from src.json_metadata_fixer import fix_metadata


class TestParseMainBreadcrumbs(unittest.TestCase):
    """Integration test for breadcrumb generation in parse_main.py."""
    
    def setUp(self):
        """Set up temporary test directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_doc_path = os.path.join(self.temp_dir, "test_document.json")
        
        # Create a dummy PDF file to pass validation
        self.dummy_pdf_path = os.path.join(self.temp_dir, "dummy.pdf")
        with open(self.dummy_pdf_path, 'w') as f:
            f.write("dummy PDF content")
        
        # Create a simple JSON document with nested headers
        self.document_data = {
            "texts": [
                {"text": "Main Document Title", "label": "section_header", "font_size": 20},
                {"text": "Introduction paragraph", "label": "paragraph"},
                {"text": "Chapter 1", "label": "section_header", "font_size": 18},
                {"text": "Chapter 1 content", "label": "paragraph"},
                {"text": "Section 1.1", "label": "section_header", "font_size": 16},
                {"text": "Section 1.1 content", "label": "paragraph"}
            ],
            "element_map": {
                "#/texts/0": {"self_ref": "#/texts/0", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/1": {"self_ref": "#/texts/1", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/2": {"self_ref": "#/texts/2", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/3": {"self_ref": "#/texts/3", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/4": {"self_ref": "#/texts/4", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}},
                "#/texts/5": {"self_ref": "#/texts/5", "content_layer": "body", 
                             "extracted_metadata": {"special_field2": "", "metadata": {}}}
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
            },
            "source_metadata": {
                "filename": "test_document.pdf",
                "mimetype": "application/pdf"
            }
        }
        
        # Save the document to the temporary file
        with open(self.test_doc_path, 'w', encoding='utf-8') as f:
            json.dump(self.document_data, f)
    
    def tearDown(self):
        """Clean up temporary test directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_breadcrumb_fixes_from_parse_main(self):
        """
        Test that parse_main.py correctly applies breadcrumb hierarchy fixes.
        
        This test verifies that:
        1. parse_main.py calls fix_metadata
        2. The fixed document data includes hierarchical breadcrumbs
        3. The final output has proper breadcrumb hierarchy
        """
        # Mock the process_pdf_document and save_output functions to return our test document
        original_process_pdf = parse_main.process_pdf_document
        original_save_output = parse_main.save_output
        
        # Also mock the validate method to avoid PDF file validation
        original_validate = parse_main.Configuration.validate
        
        def mock_process_pdf(pdf_path, output_dir, config_file=None):
            return self.document_data
        
        def mock_save_output(document, output_dir):
            return self.test_doc_path
        
        def mock_validate(self):
            return []  # Return empty list to indicate no validation errors
        
        # Apply the mocks
        parse_main.process_pdf_document = mock_process_pdf
        parse_main.save_output = mock_save_output
        parse_main.Configuration.validate = mock_validate
        
        try:
            # Prepare arguments for parse_main
            sys.argv = [
                'parse_main.py',
                '--pdf_path', self.dummy_pdf_path,
                '--output_dir', self.temp_dir,
                '--output_format', 'json'
            ]
            
            # Run parse_main.py
            parse_main.main()
            
            # Check if the fixed_document.json was created
            fixed_file = os.path.join(self.temp_dir, "fixed_document.json")
            self.assertTrue(os.path.exists(fixed_file), "Fixed document was not created")
            
            # Load the fixed document
            with open(fixed_file, 'r', encoding='utf-8') as f:
                fixed_doc = json.load(f)
            
            # Verify breadcrumbs in the fixed document
            # Content at section level should have the full hierarchy
            section_content = fixed_doc["element_map"]["#/texts/5"]
            expected_breadcrumb = "Main Document Title > Chapter 1 > Section 1.1"
            self.assertEqual(
                section_content["extracted_metadata"]["special_field2"],
                expected_breadcrumb,
                "Section content should have the full hierarchy in breadcrumb"
            )
            
            # Content at chapter level
            chapter_content = fixed_doc["element_map"]["#/texts/3"]
            expected_chapter_breadcrumb = "Main Document Title > Chapter 1"
            self.assertEqual(
                chapter_content["extracted_metadata"]["special_field2"],
                expected_chapter_breadcrumb,
                "Chapter content should have hierarchy up to chapter level"
            )
            
            # Content after title
            intro_content = fixed_doc["element_map"]["#/texts/1"]
            expected_intro_breadcrumb = "Main Document Title"
            self.assertEqual(
                intro_content["extracted_metadata"]["special_field2"],
                expected_intro_breadcrumb,
                "Introduction content should have just the title in breadcrumb"
            )
            
        finally:
            # Restore the original functions
            parse_main.process_pdf_document = original_process_pdf
            parse_main.save_output = original_save_output
            parse_main.Configuration.validate = original_validate


if __name__ == "__main__":
    unittest.main() 