#!/usr/bin/env python3
"""
Tests for Metadata Extraction Module

This module contains unit tests for the metadata_extractor module.
It verifies that metadata is correctly extracted from document elements
and properly formatted for database storage.
"""

import unittest
import json
import os
from pathlib import Path
from typing import Dict, List, Any

# Import the module being tested
from metadata_extractor import (
    convert_bbox,
    extract_page_number,
    extract_image_metadata,
    build_metadata_object,
    extract_full_metadata
)

class TestMetadataExtractor(unittest.TestCase):
    """Test cases for metadata extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample elements for testing
        self.text_element = {
            "id": "text_1",
            "self_ref": "#/texts/0",
            "text": "Sample text element",
            "label": "paragraph",
            "prov": {
                "page_no": 1,
                "bbox": {
                    "l": 56.7,
                    "t": 115.2,
                    "r": 555.3,
                    "b": 309.8
                }
            },
            "metadata": {
                "type": "paragraph"
            }
        }
        
        self.image_element = {
            "id": "image_1",
            "self_ref": "#/pictures/0",
            "label": "picture",
            "bounds": {
                "l": 100,
                "t": 200,
                "r": 300,
                "b": 400
            },
            "metadata": {
                "type": "picture",
                "mimetype": "image/png",
                "ocr_text": "Text extracted from the image via OCR"
            }
        }
        
        self.table_element = {
            "id": "table_1",
            "self_ref": "#/tables/0",
            "label": "table",
            "bounds": {
                "l": 50,
                "t": 350,
                "r": 550,
                "b": 450
            },
            "metadata": {
                "type": "table"
            },
            "cells": [
                {"row": 0, "col": 0, "text": "Header 1"},
                {"row": 0, "col": 1, "text": "Header 2"},
                {"row": 1, "col": 0, "text": "Cell 1"},
                {"row": 1, "col": 1, "text": "Cell 2"}
            ]
        }
        
        self.furniture_element = {
            "id": "header_1",
            "self_ref": "#/texts/1",
            "text": "Page Header",
            "content_layer": "furniture",
            "prov": {
                "page_no": 1,
                "bbox": {
                    "l": 10,
                    "t": 10,
                    "r": 590,
                    "b": 50
                }
            }
        }
        
        # Create sample flattened sequence
        self.flattened_sequence = [
            {
                "id": "section_1",
                "self_ref": "#/texts/2",
                "text": "Document Title",
                "metadata": {"type": "h1"},
                "label": "section_header"
            },
            {
                "id": "section_2",
                "self_ref": "#/texts/3",
                "text": "Section 1",
                "metadata": {"type": "h2"},
                "label": "section_header"
            },
            self.text_element,
            {
                "id": "caption_1",
                "self_ref": "#/texts/4",
                "text": "Figure 1: Sample Image",
                "metadata": {"type": "caption"}
            },
            self.image_element,
            {
                "id": "text_2",
                "self_ref": "#/texts/5",
                "text": "Text following the image"
            },
            {
                "id": "caption_2",
                "self_ref": "#/texts/6",
                "text": "Table 1: Sample Table",
                "metadata": {"type": "caption"}
            },
            self.table_element
        ]
        
        # Sample document info
        self.doc_info = {
            "filename": "test_document.pdf",
            "mimetype": "application/pdf",
            "binary_hash": "abc123"
        }
    
    def test_convert_bbox(self):
        """Test bounding box conversion."""
        # Test with valid bbox
        bbox = {
            "l": 56.7,
            "t": 115.2,
            "r": 555.3,
            "b": 309.8
        }
        
        converted = convert_bbox(bbox)
        self.assertEqual(converted["coords_x"], 56)
        self.assertEqual(converted["coords_y"], 115)
        self.assertEqual(converted["coords_cx"], 498)
        self.assertEqual(converted["coords_cy"], 194)
        
        # Test with non-integer option
        converted = convert_bbox(bbox, to_integers=False)
        self.assertEqual(converted["coords_x"], 56.7)
        self.assertEqual(converted["coords_y"], 115.2)
        self.assertAlmostEqual(converted["coords_cx"], 498.6, places=5)
        self.assertAlmostEqual(converted["coords_cy"], 194.6, places=5)
        
        # Test with empty bbox
        converted = convert_bbox({})
        self.assertEqual(converted["coords_x"], 0)
        self.assertEqual(converted["coords_y"], 0)
        self.assertEqual(converted["coords_cx"], 0)
        self.assertEqual(converted["coords_cy"], 0)
    
    def test_extract_page_number(self):
        """Test page number extraction from various element formats."""
        # Test from prov field
        page_num = extract_page_number(self.text_element)
        self.assertEqual(page_num, 1)
        
        # Test from top-level attribute
        element = {"page_no": 5}
        page_num = extract_page_number(element)
        self.assertEqual(page_num, 5)
        
        # Test from metadata
        element = {"metadata": {"page_no": 3}}
        page_num = extract_page_number(element)
        self.assertEqual(page_num, 3)
        
        # Test with non-integer page number
        element = {"page_no": "2"}
        page_num = extract_page_number(element)
        self.assertEqual(page_num, 2)
        
        # Test with missing page number
        element = {"some_field": "value"}
        page_num = extract_page_number(element)
        self.assertIsNone(page_num)
    
    def test_extract_image_metadata(self):
        """Test extraction of image-specific metadata."""
        image_meta = extract_image_metadata(self.image_element)
        
        self.assertEqual(image_meta["image_mimetype"], "image/png")
        self.assertEqual(image_meta["image_width"], 200)
        self.assertEqual(image_meta["image_height"], 200)
        self.assertEqual(image_meta["image_ocr_text"], "Text extracted from the image via OCR")
        
        # Test with missing fields
        element = {"metadata": {"type": "picture"}}
        image_meta = extract_image_metadata(element)
        self.assertEqual(image_meta["image_mimetype"], "image/png")  # Default value
        self.assertEqual(image_meta["image_width"], 0)
        self.assertEqual(image_meta["image_height"], 0)
    
    def test_build_metadata_object(self):
        """Test building complete metadata object."""
        # Test for text element
        metadata = build_metadata_object(self.text_element, self.flattened_sequence)
        
        self.assertEqual(metadata["breadcrumb"], "Document Title > Section 1")
        self.assertEqual(metadata["page_no"], 1)
        self.assertTrue("bbox_raw" in metadata)
        self.assertTrue("context_before" in metadata or "context_after" in metadata)
        self.assertEqual(metadata["docling_label"], "paragraph")
        self.assertEqual(metadata["docling_ref"], "#/texts/0")
        
        # Test for image element
        metadata = build_metadata_object(self.image_element, self.flattened_sequence)
        
        self.assertEqual(metadata["breadcrumb"], "Document Title > Section 1")
        self.assertTrue("caption" in metadata)
        self.assertEqual(metadata["caption"], "Figure 1: Sample Image")
        self.assertEqual(metadata["image_mimetype"], "image/png")
        self.assertEqual(metadata["image_width"], 200)
        self.assertEqual(metadata["image_height"], 200)
        self.assertEqual(metadata["image_ocr_text"], "Text extracted from the image via OCR")
    
    def test_extract_full_metadata(self):
        """Test extraction of full metadata ready for database."""
        # Test with text element
        full_meta = extract_full_metadata(
            self.text_element, 
            self.flattened_sequence,
            self.doc_info
        )
        
        # Check core fields
        self.assertEqual(full_meta["coords_x"], 56)
        self.assertEqual(full_meta["coords_y"], 115)
        self.assertEqual(full_meta["coords_cx"], 498)
        self.assertEqual(full_meta["coords_cy"], 194)
        self.assertEqual(full_meta["master_index"], 1)
        self.assertIsNone(full_meta["master_index2"])
        self.assertEqual(full_meta["file_type"], "application/pdf")
        self.assertEqual(full_meta["file_source"], "test_document.pdf")
        
        # Check metadata field
        self.assertTrue("metadata" in full_meta)
        self.assertEqual(full_meta["metadata"]["breadcrumb"], "Document Title > Section 1")
        self.assertEqual(full_meta["metadata"]["page_no"], 1)
        
        # Test with image element
        full_meta = extract_full_metadata(
            self.image_element, 
            self.flattened_sequence,
            self.doc_info
        )
        
        # Check image-specific metadata
        self.assertTrue("image_mimetype" in full_meta["metadata"])
        self.assertTrue("image_width" in full_meta["metadata"])
        self.assertTrue("image_height" in full_meta["metadata"])
        self.assertTrue("image_ocr_text" in full_meta["metadata"])

if __name__ == "__main__":
    unittest.main() 