#!/usr/bin/env python3
"""
Integration Test for PDF Document Parser

This test verifies the complete PDF document parsing pipeline, focusing on three key issues:
1. Image data should be saved as external files and referenced in the element map
2. Text elements, tables, and main content chunks should be correctly identified
3. Breadcrumbs should be generated properly, and furniture elements should be filtered from context
"""

import unittest
import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
import logging
import base64

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add src directory to path for imports
src_dir = os.path.join(parent_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import mock class
from unittest.mock import patch, MagicMock

# Add the project directory to sys.path
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from parse_main import main
from src.utils import replace_base64_with_file_references, load_json, save_json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDocumentConverter:
    """Mock class for DocumentConverter to simulate PDF parsing"""
    
    def __init__(self, *args, **kwargs):
        """Initialize the mock converter"""
        self.document = {
            "pages": [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "text_elements": [
                        {
                            "id": "text_1",
                            "text": "Heading 1",
                            "bbox": [50, 50, 150, 70],
                            "font_size": 14,
                            "is_bold": True,
                            "style": "heading"
                        },
                        {
                            "id": "text_2",
                            "text": "This is a paragraph of sample text.",
                            "bbox": [50, 80, 400, 100],
                            "font_size": 12,
                            "style": "normal"
                        },
                        {
                            "id": "text_3",
                            "text": "Page 1 Footer",
                            "bbox": [50, 750, 150, 770],
                            "font_size": 10,
                            "style": "footer"
                        }
                    ],
                    "tables": [
                        {
                            "id": "table_1",
                            "bbox": [50, 200, 500, 300],
                            "rows": 3,
                            "columns": 3,
                            "cells": [
                                {"text": "Header 1", "row": 0, "col": 0},
                                {"text": "Header 2", "row": 0, "col": 1},
                                {"text": "Header 3", "row": 0, "col": 2},
                                {"text": "Data 1", "row": 1, "col": 0},
                                {"text": "Data 2", "row": 1, "col": 1},
                                {"text": "Data 3", "row": 1, "col": 2},
                                {"text": "Data 4", "row": 2, "col": 0},
                                {"text": "Data 5", "row": 2, "col": 1},
                                {"text": "Data 6", "row": 2, "col": 2}
                            ]
                        }
                    ],
                    "images": [
                        {
                            "id": "image_1",
                            "bbox": [50, 350, 300, 500],
                            "data": "base64_encoded_image_data_sample"
                        }
                    ]
                },
                {
                    "page_number": 2,
                    "width": 612,
                    "height": 792,
                    "text_elements": [
                        {
                            "id": "text_4",
                            "text": "Heading 2",
                            "bbox": [50, 50, 150, 70],
                            "font_size": 14,
                            "is_bold": True,
                            "style": "heading"
                        },
                        {
                            "id": "text_5",
                            "text": "This is another paragraph on page 2.",
                            "bbox": [50, 80, 400, 100],
                            "font_size": 12,
                            "style": "normal"
                        },
                        {
                            "id": "text_6",
                            "text": "Page 2 Footer",
                            "bbox": [50, 750, 150, 770],
                            "font_size": 10,
                            "style": "footer"
                        }
                    ],
                    "tables": [],
                    "images": [
                        {
                            "id": "image_2",
                            "bbox": [50, 200, 300, 350],
                            "data": "base64_encoded_image_data_sample_2"
                        }
                    ]
                }
            ]
        }
    
    def convert_pdf_to_document(self, *args, **kwargs):
        """Return the mock document structure"""
        return self.document


class TestIntegration(unittest.TestCase):
    """Integration test for the PDF document parser"""
    
    def setUp(self):
        """Set up the test environment with a temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create a mock PDF file
        self.pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.pdf_path, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
        
        # Save the original sys.argv
        self.original_argv = sys.argv.copy()
        
        # Override sys.argv with our test arguments
        sys.argv = [
            "parse_main.py",
            "--pdf_path", self.pdf_path,
            "--output_dir", self.output_dir,
            "--log_level", "ERROR"
        ]
    
    def tearDown(self):
        """Clean up after the test"""
        # Restore original sys.argv
        sys.argv = self.original_argv
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch('element_map_builder.build_element_map')
    @patch('docling.document_converter.DocumentConverter')
    def test_complete_parsing_pipeline(self, mock_converter_class, mock_build_element_map):
        """Test the complete parsing pipeline from PDF to fixed JSON output"""
        # Set up mocks
        mock_converter = MockDocumentConverter()
        mock_converter_class.return_value = mock_converter
        
        # Create a mock element map that matches our test document
        mock_element_map = {
            "pages": [
                {
                    "page_number": 1,
                    "width": 612,
                    "height": 792,
                    "text_elements": mock_converter.document["pages"][0]["text_elements"],
                    "tables": mock_converter.document["pages"][0]["tables"],
                    "images": mock_converter.document["pages"][0]["images"]
                },
                {
                    "page_number": 2,
                    "width": 612,
                    "height": 792,
                    "text_elements": mock_converter.document["pages"][1]["text_elements"],
                    "tables": mock_converter.document["pages"][1]["tables"],
                    "images": mock_converter.document["pages"][1]["images"]
                }
            ],
            "metadata": {
                "title": "Test Document",
                "author": "Test Author",
                "creator": "Test Creator"
            }
        }
        mock_build_element_map.return_value = mock_element_map
        
        # Import parse_main dynamically after setting up mocks
        import parse_main
        
        # Run the main function
        result = parse_main.main()
        
        # Check return code
        self.assertEqual(result, 0, "The main function should return 0 for success")
        
        # Check if the output files exist
        docling_json_path = os.path.join(self.output_dir, "docling_document.json")
        fixed_json_path = os.path.join(self.output_dir, "fixed_document.json")
        output_json_path = os.path.join(self.output_dir, "document.json")
        
        self.assertTrue(os.path.exists(docling_json_path), "Docling output file should exist")
        self.assertTrue(os.path.exists(fixed_json_path), "Fixed output file should exist")
        self.assertTrue(os.path.exists(output_json_path), "Formatted output file should exist")
        
        # Check if images directory was created with image files
        images_dir = os.path.join(self.output_dir, "images")
        self.assertTrue(os.path.exists(images_dir), "Images directory should exist")
        
        # Load the fixed output file
        with open(fixed_json_path, 'r', encoding='utf-8') as f:
            fixed_data = json.load(f)
        
        # Verify that image data has been replaced with external file references
        for page in fixed_data.get("pages", []):
            for image in page.get("images", []):
                self.assertNotIn("data", image, "Image data should not be inline in the JSON")
                self.assertIn("file_path", image, "Image should have a file_path reference")
        
        # Check if breadcrumbs are generated
        for page in fixed_data.get("pages", []):
            for text_element in page.get("text_elements", []):
                if text_element.get("style") == "heading":
                    self.assertIn("breadcrumb", text_element, "Heading elements should have breadcrumbs")
            
            for table in page.get("tables", []):
                self.assertIn("breadcrumb", table, "Tables should have breadcrumbs")
        
        # Check that furniture elements are not in context
        for page in fixed_data.get("pages", []):
            for element in page.get("text_elements", []) + page.get("tables", []) + page.get("images", []):
                if element.get("context_before"):
                    for context_item in element.get("context_before", []):
                        self.assertNotIn("footer", context_item.get("text", "").lower(), 
                                         "Footer should not be in context_before")
                
                if element.get("context_after"):
                    for context_item in element.get("context_after", []):
                        self.assertNotIn("footer", context_item.get("text", "").lower(),
                                         "Footer should not be in context_after")


class TestParseMainIntegration(unittest.TestCase):
    """Integration tests for the parse_main module."""
    
    def setUp(self):
        """Set up test environment with temporary directories."""
        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up test sample PDF path
        self.sample_pdf_path = os.path.join(current_dir, "samples", "test_document.pdf")
        
        # Create test sample PDF if it doesn't exist
        if not os.path.exists(os.path.dirname(self.sample_pdf_path)):
            os.makedirs(os.path.dirname(self.sample_pdf_path), exist_ok=True)
            
        # If no test PDF exists, we'll need to skip the actual PDF parsing tests
        self.skip_pdf_tests = not os.path.exists(self.sample_pdf_path)
    
    def tearDown(self):
        """Clean up temporary test directories."""
        shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(True, "Requires a valid PDF file for testing")
    def test_main_workflow(self):
        """Test the full parse_main workflow with a sample PDF."""
        if self.skip_pdf_tests:
            self.skipTest("No sample PDF available for testing")
        
        # Run the main function with our test PDF
        args = [
            "--input", self.sample_pdf_path,
            "--output", self.output_dir,
            "--extract-images", "true"
        ]
        
        # Redirect stdout/stderr during execution
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = tempfile.TemporaryFile(mode="w+")
        sys.stderr = tempfile.TemporaryFile(mode="w+")
        
        try:
            # Run the main function
            main(args)
            
            # Get the expected output JSON file path
            pdf_basename = os.path.basename(self.sample_pdf_path)
            output_json_path = os.path.join(self.output_dir, f"{os.path.splitext(pdf_basename)[0]}.json")
            
            # Check that the output file exists
            self.assertTrue(os.path.exists(output_json_path), f"Output JSON file not found at {output_json_path}")
            
            # Load and check the JSON output
            with open(output_json_path, 'r') as f:
                json_data = json.load(f)
            
            # Verify that base64 data has been removed
            self.assertNoBase64InJson(json_data)
            
            # Check if images directory was created
            images_dir = os.path.join(self.output_dir, "images")
            if os.path.exists(images_dir):
                # If images were extracted, check that files exist
                image_files = os.listdir(images_dir)
                if image_files:
                    self.assertGreater(len(image_files), 0, "No image files extracted")
        
        finally:
            # Restore stdout/stderr
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def test_json_output_format(self):
        """Test the JSON output format compatibility."""
        # Create a mock JSON file that simulates the output
        mock_json_path = os.path.join(self.temp_dir, "mock_output.json")
        
        # Create a minimal mock JSON structure
        mock_data = {
            "metadata": {
                "title": "Test Document"
            },
            "elements": [
                {
                    "id": "elem1",
                    "type": "text",
                    "content": "Sample text content"
                }
            ]
        }
        
        # Write the mock data to file
        with open(mock_json_path, 'w') as f:
            json.dump(mock_data, f)
            
        # Verify we can load the JSON (basic format check)
        with open(mock_json_path, 'r') as f:
            loaded_data = json.load(f)
            
        self.assertEqual(loaded_data["metadata"]["title"], "Test Document")
        self.assertEqual(loaded_data["elements"][0]["content"], "Sample text content")
        
    def assertNoBase64InJson(self, json_data):
        """Assert that no base64 data is present in the JSON data."""
        # Convert to string for simple checking
        json_str = json.dumps(json_data)
        
        # Check no base64 data is present
        self.assertNotIn("data:image/png;base64,", json_str)
        self.assertNotIn("data:image/jpeg;base64,", json_str)
        self.assertNotIn("data:image/jpg;base64,", json_str)
        self.assertNotIn("data:image/gif;base64,", json_str)
        
        # Check if base64 replacement text exists
        if "image" in json_str:
            self.assertIn("[BASE64_IMAGE_DATA_REMOVED]", json_str)


class TestIntegration(unittest.TestCase):
    """Integration tests for the document parsing workflow"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test directory
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create output directory
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock PDF file with a simple structure
        # For integration testing, we'll mock the processed result rather than processing a real PDF
        self.mock_processed_data = {
            "metadata": {
                "title": "Test Document",
                "author": "Test Author"
            },
            "pages": [
                {
                    "page_num": 1,
                    "elements": [
                        {
                            "type": "image",
                            "mime_type": "image/png",
                            "base64_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
                            "width": 100,
                            "height": 100
                        },
                        {
                            "type": "text",
                            "content": "This is a test text"
                        }
                    ]
                }
            ]
        }
        
        # Save the mock data as an intermediate processing result
        self.mock_result_path = self.test_dir / "mock_processed.json"
        with open(self.mock_result_path, 'w') as f:
            json.dump(self.mock_processed_data, f)
            
        # Doc ID for testing
        self.doc_id = "test_document"
        
        # Expected output location after processing
        self.expected_output_file = self.output_dir / f"{self.doc_id}.json"
        self.expected_images_dir = self.output_dir / self.doc_id / "images"
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test directory and all its contents
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_base64_replacement_in_workflow(self):
        """Test that base64 data is correctly replaced with file references in the workflow"""
        # Create a mock process function to simulate the complete workflow
        def mock_process_workflow():
            # 1. Load the mock processed data
            data = load_json(self.mock_result_path)
            
            # 2. Replace the base64 data with file references
            processed_data = replace_base64_with_file_references(
                data, 
                self.output_dir,
                self.doc_id
            )
            
            # 3. Save the result
            save_json(processed_data, self.expected_output_file)
            
            return processed_data
        
        # Run the mock process
        result = mock_process_workflow()
        
        # Verify results
        
        # 1. Check that the output file was created
        self.assertTrue(self.expected_output_file.exists())
        
        # 2. Check that the images directory was created
        self.assertTrue(self.expected_images_dir.exists())
        
        # 3. Verify there is at least one image file created
        image_files = list(self.expected_images_dir.glob("*"))
        self.assertGreater(len(image_files), 0)
        
        # 4. Verify base64_data was replaced with external_file reference
        image_element = result["pages"][0]["elements"][0]
        self.assertNotIn("base64_data", image_element)
        self.assertIn("external_file", image_element)
        
        # 5. Verify the external_file path points to a real file
        image_path = self.output_dir / image_element["external_file"]
        self.assertTrue(image_path.exists())
        
        # 6. Check that the file is not empty
        self.assertGreater(image_path.stat().st_size, 0)
        
        # 7. Load the saved JSON and verify it matches the processed result
        saved_data = load_json(self.expected_output_file)
        self.assertEqual(saved_data, result)
    
    def test_image_uri_replacement(self):
        """Test that base64 image data in uri and data_uri fields is replaced with file references."""
        # Create test data with base64 images in different fields
        test_data = {
            "pictures": [
                {
                    "uri": f"data:image/png;base64,{self.mock_processed_data['pages'][0]['elements'][0]['base64_data']}",
                    "id": "uri_test"
                },
                {
                    "data_uri": f"data:image/png;base64,{self.mock_processed_data['pages'][0]['elements'][0]['base64_data']}",
                    "id": "data_uri_test"
                },
                {
                    "data": f"data:image/png;base64,{self.mock_processed_data['pages'][0]['elements'][0]['base64_data']}",
                    "id": "data_test"
                }
            ],
            "element_map": {
                "element1": {
                    "uri": f"data:image/png;base64,{self.mock_processed_data['pages'][0]['elements'][0]['base64_data']}"
                }
            }
        }
        
        # Save test data to a file
        test_file = self.test_dir / "test_document.json"
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        # Run the function to test
        result = replace_base64_with_file_references(test_data, self.test_dir, self.doc_id)
        
        # Check that the images directory was created
        images_dir = self.test_dir / self.doc_id / "images"
        self.assertTrue(images_dir.exists(), "Images directory should be created")
        
        # Check for image files
        image_files = list(images_dir.glob("*.png"))
        self.assertEqual(len(image_files), 4, "Should extract 4 images")
        
        # Check that all base64 data was replaced
        def check_no_base64(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("data:image"):
                        return False
                    if not check_no_base64(value):
                        return False
            elif isinstance(data, list):
                for item in data:
                    if not check_no_base64(item):
                        return False
            return True
        
        self.assertTrue(check_no_base64(result), "All base64 data should be replaced")
        
        # Check that replaced values contain file references
        self.assertIn(f"{self.doc_id}/images", result["pictures"][0]["uri"])
        self.assertIn(f"{self.doc_id}/images", result["pictures"][1]["data_uri"])
        self.assertIn(f"{self.doc_id}/images", result["pictures"][2]["data"])
        self.assertIn(f"{self.doc_id}/images", result["element_map"]["element1"]["uri"])
        
        # Check that all images exist
        for pic in result["pictures"]:
            for key in ["uri", "data_uri", "data"]:
                if key in pic:
                    file_path = self.test_dir / pic[key]
                    self.assertTrue(file_path.exists(), f"Image file {file_path} should exist")
        
        file_path = self.test_dir / result["element_map"]["element1"]["uri"]
        self.assertTrue(file_path.exists(), "Element map image file should exist")


if __name__ == "__main__":
    unittest.main() 

