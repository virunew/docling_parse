#!/usr/bin/env python3
"""
Unit tests for src/json_metadata_fixer.py
"""

import unittest
import json
import os
import base64
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Ensure src directory is in path for imports
import sys
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from json_metadata_fixer import fix_metadata, fix_image_references, generate_breadcrumbs, filter_furniture_from_context

# Sample base64 encoded PNG data (1x1 pixel, transparent)
SAMPLE_B64_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
SAMPLE_DATA_URI = f"data:image/png;base64,{SAMPLE_B64_PNG}"

class TestJsonMetadataFixer(unittest.TestCase):
    """Test suite for json_metadata_fixer functions."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.sample_doc_data = {
            "source_metadata": {
                "filename": "test_document.pdf"
            },
            "pictures": [
                {
                    "data": SAMPLE_DATA_URI,
                    "prov": [{"page_no": 1, "bbox_raw": {"l": 10, "t": 10, "r": 110, "b": 110}}],
                    "label": "picture"
                },
                {
                    # Image without data URI - should be ignored
                    "prov": [{"page_no": 2, "bbox_raw": {"l": 20, "t": 20, "r": 120, "b": 120}}],
                    "label": "picture"
                }
            ],
            "element_map": {
                "elem_pic1": {
                    "self_ref": "#/pictures/0",
                    "content_layer": "body",
                    "label": "picture",
                    "extracted_metadata": {
                        "metadata": {"page_no": 1},
                        "special_field1": "{'some_key': 'value'}" # Test placeholder
                    }
                },
                "elem_pic2": {
                     "self_ref": "#/pictures/1",
                     "content_layer": "body",
                     "label": "picture"
                },
                "elem_text1": {
                     "self_ref": "#/texts/0",
                     "content_layer": "body",
                     "label": "text"
                }
            },
            "texts": [{"text": "Some text"}],
            # Other elements like headers, furniture can be added for other tests
        }
        self.output_dir = Path("./test_output_fixer")
        self.images_dir = self.output_dir / "images"
        # Clean up potential leftover directory
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        """Tear down test fixtures, if any."""
        # Clean up the created directory
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("json_metadata_fixer.logger") # Mock logger to avoid console output during tests
    def test_fix_image_references(self, mock_logger, mock_mkdir, mock_file_open):
        """Test that fix_image_references saves images and updates references."""
        test_data = json.loads(json.dumps(self.sample_doc_data)) # Deep copy
        
        fixed_data = fix_image_references(test_data, self.images_dir)

        # --- Assertions for picture elements ---
        self.assertIn("pictures", fixed_data)
        pictures = fixed_data["pictures"]
        self.assertEqual(len(pictures), 2)

        # Picture 1 (with data URI)
        pic1 = pictures[0]
        self.assertNotIn("data", pic1, "Base64 data should be removed")
        self.assertIn("external_file", pic1)
        expected_rel_path = "images/test_document_image_0.png"
        # Check if the path is relative to the parent of images_dir (output_dir)
        self.assertTrue(pic1["external_file"].endswith(expected_rel_path))
        self.assertEqual(pic1["external_file"], str(Path("images") / "test_document_image_0.png"))


        # Picture 2 (without data URI)
        pic2 = pictures[1]
        self.assertNotIn("data", pic2)
        self.assertNotIn("external_file", pic2, "Should not have external_file if no data URI")

        # --- Assertions for file writing ---
        # Check if Path.mkdir was called correctly
        mock_mkdir.assert_not_called() # fix_image_references doesn't create the dir itself

        # Check if 'open' was called correctly to write the file
        expected_abs_path = self.images_dir / "test_document_image_0.png"
        mock_file_open.assert_called_once_with(expected_abs_path, "wb")
        
        # Check if write was called with decoded data
        handle = mock_file_open()
        decoded_data = base64.b64decode(SAMPLE_B64_PNG)
        handle.write.assert_called_once_with(decoded_data)

        # --- Assertions for element_map updates ---
        self.assertIn("element_map", fixed_data)
        element_map = fixed_data["element_map"]
        
        # Element referencing Picture 1
        elem_pic1 = element_map["elem_pic1"]
        self.assertIn("external_file", elem_pic1)
        self.assertEqual(elem_pic1["external_file"], pic1["external_file"])
        # Check metadata update
        self.assertIn("extracted_metadata", elem_pic1)
        self.assertIn("external_files", elem_pic1["extracted_metadata"])
        self.assertEqual(elem_pic1["extracted_metadata"]["external_files"], pic1["external_file"])

        # Element referencing Picture 2 (should be unchanged regarding external_file)
        elem_pic2 = element_map["elem_pic2"]
        self.assertNotIn("external_file", elem_pic2)
        self.assertNotIn("extracted_metadata", elem_pic2) # No metadata existed initially

        # Element referencing text (should be unchanged)
        elem_text1 = element_map["elem_text1"]
        self.assertNotIn("external_file", elem_text1)
        
        # --- Assertions for Logging ---
        mock_logger.info.assert_called_with("Fixing image references...")
        mock_logger.debug.assert_called_with(f"Saved image to {expected_abs_path}")


    # TODO: Add tests for generate_breadcrumbs
    # TODO: Add tests for filter_furniture_from_context
    # TODO: Add test for the main fix_metadata function orchestrating calls


if __name__ == '__main__':
    unittest.main()