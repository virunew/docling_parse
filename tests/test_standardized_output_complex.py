"""
Test for standardized output with complex data

This test verifies that the standardized output format properly handles
different types of content including text, tables, and images.
"""

import os
import json
import unittest
import tempfile
import shutil
from pathlib import Path

# Import the module to test
from src.format_standardized_output import save_standardized_output

class TestStandardizedOutputComplex(unittest.TestCase):
    """Test the standardized output generation with complex data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a more complex document with text, tables, and images
        self.document_data = {
            "name": "complex_document",
            "element_map": {
                "flattened_sequence": [
                    # Text element with metadata
                    {
                        "type": "text",
                        "text_content": "This is a section header",
                        "content_layer": "body",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1",
                            "page_no": 1,
                            "bbox_raw": {"l": 50, "t": 100, "r": 500, "b": 120}
                        }
                    },
                    # Furniture element
                    {
                        "type": "text",
                        "text_content": "Page 1 of 10",
                        "content_layer": "furniture"
                    },
                    # Table element
                    {
                        "type": "table",
                        "content_layer": "body",
                        "table_content": [
                            ["Header 1", "Header 2", "Header 3"],
                            ["Cell 1", "Cell 2", "Cell 3"],
                            ["Cell 4", "Cell 5", "Cell 6"]
                        ],
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1 > Tables",
                            "page_no": 1,
                            "bbox_raw": {"l": 100, "t": 200, "r": 500, "b": 300},
                            "caption": "Table 1: Sample Data"
                        }
                    },
                    # Image element
                    {
                        "type": "picture",
                        "content_layer": "body",
                        "external_path": "images/sample_image.png",
                        "context_before": "Text before the image",
                        "context_after": "Text after the image",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1 > Figures",
                            "page_no": 2,
                            "bbox_raw": {"l": 150, "t": 250, "r": 450, "b": 350},
                            "caption": "Figure 1: Sample Image",
                            "image_ocr_text": "Text extracted from image via OCR"
                        }
                    },
                    # Another text element
                    {
                        "type": "text",
                        "text_content": "This is a paragraph with some content.",
                        "content_layer": "body",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1 > Subsection",
                            "page_no": 2,
                            "bbox_raw": {"l": 50, "t": 400, "r": 500, "b": 450}
                        }
                    }
                ]
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_standardized_output_with_complex_data(self):
        """Test that save_standardized_output handles complex data correctly."""
        # Call the function
        output_file = save_standardized_output(
            self.document_data,
            self.temp_dir,
            "complex_test.pdf"
        )
        
        # Check that the file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Load and check the contents
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        # Check structure
        self.assertIn("chunks", output_data)
        self.assertIn("furniture", output_data)
        self.assertIn("source_metadata", output_data)
        
        # Check content
        self.assertEqual(len(output_data["chunks"]), 4)  # 4 content elements
        self.assertEqual(len(output_data["furniture"]), 1)  # 1 furniture element
        self.assertEqual(output_data["furniture"][0], "Page 1 of 10")
        
        # Verify content types
        content_types = [chunk["content_type"] for chunk in output_data["chunks"]]
        self.assertEqual(content_types.count("text"), 2)
        self.assertEqual(content_types.count("table"), 1)
        self.assertEqual(content_types.count("image"), 1)
        
        # Check specific chunks
        text_chunks = [c for c in output_data["chunks"] if c["content_type"] == "text"]
        table_chunks = [c for c in output_data["chunks"] if c["content_type"] == "table"]
        image_chunks = [c for c in output_data["chunks"] if c["content_type"] == "image"]
        
        # Check text chunk
        self.assertIn("This is a section header", text_chunks[0]["text_block"])
        self.assertEqual(text_chunks[0]["header_text"], "Document > Section 1")
        self.assertEqual(text_chunks[0]["master_index"], 1)
        
        # Check table chunk
        self.assertIsNotNone(table_chunks[0]["table_block"])
        table_data = json.loads(table_chunks[0]["table_block"])
        self.assertEqual(len(table_data), 3)  # 3 rows
        self.assertEqual(len(table_data[0]), 3)  # 3 columns
        self.assertEqual(table_data[0][0], "Header 1")
        self.assertEqual(table_data[1][2], "Cell 3")
        self.assertEqual(table_chunks[0]["header_text"], "Document > Section 1 > Tables")
        
        # Check image chunk
        self.assertEqual(image_chunks[0]["external_files"], "images/sample_image.png")
        self.assertIn("Text before the image", image_chunks[0]["text_block"])
        self.assertIn("[Image Text: Text extracted from image via OCR]", image_chunks[0]["text_block"])
        self.assertIn("Text after the image", image_chunks[0]["text_block"])
        self.assertEqual(image_chunks[0]["header_text"], "Document > Section 1 > Figures")
        
        # Check metadata in special_field1
        for chunk in output_data["chunks"]:
            if chunk["special_field1"]:
                metadata = json.loads(chunk["special_field1"])
                self.assertIsInstance(metadata, dict)
                if "breadcrumb" in metadata:
                    self.assertEqual(metadata["breadcrumb"], chunk["header_text"])

if __name__ == '__main__':
    unittest.main() 