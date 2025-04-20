"""
Tests for the element_map_builder module.
"""

import unittest
import json
from pathlib import Path
import logging
import tempfile

from src.element_map_builder import (
    extract_elements,
    find_ref_pointers,
    resolve_references,
    build_element_map
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestElementMapBuilder(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample DoclingDocument JSON with references
        self.sample_document = {
            "name": "Sample Document",
            "texts": [
                {
                    "self_ref": "text1",
                    "text": "Hello world",
                    "metadata": {"type": "heading"}
                },
                {
                    "self_ref": "text2",
                    "text": "This refers to text1",
                    "reference": {"$ref": "text1"}
                }
            ],
            "pictures": [
                {
                    "self_ref": "pic1",
                    "caption": {"$ref": "text1"}
                }
            ],
            "tables": [
                {
                    "self_ref": "table1",
                    "caption": {"$ref": "text2"},
                    "cells": [
                        {"$ref": "text1"},
                        {"content": "Regular content"}
                    ]
                }
            ],
            "groups": [
                {
                    "self_ref": "group1",
                    "children": [
                        {"$ref": "text1"},
                        {"$ref": "pic1"},
                        {"$ref": "table1"}
                    ]
                }
            ]
        }
        
        # Create a circular reference document
        self.circular_document = {
            "texts": [
                {
                    "self_ref": "text1",
                    "reference": {"$ref": "text2"}
                },
                {
                    "self_ref": "text2",
                    "reference": {"$ref": "text1"}
                }
            ]
        }
        
        # Create a document with missing references
        self.missing_ref_document = {
            "texts": [
                {
                    "self_ref": "text1",
                    "reference": {"$ref": "non_existent"}
                }
            ]
        }
        
        # Create a nested document
        self.nested_document = {
            "texts": [
                {
                    "self_ref": "text1",
                    "content": "Root text"
                },
                {
                    "self_ref": "text2",
                    "content": "Child text",
                    "parent": {"$ref": "text1"}
                },
                {
                    "self_ref": "text3",
                    "content": "Grandchild text",
                    "parent": {"$ref": "text2"}
                }
            ]
        }

    def test_extract_elements(self):
        """Test that elements with self_ref are correctly extracted."""
        element_map = extract_elements(self.sample_document)
        
        # Check that all elements with self_ref are in the map
        self.assertEqual(len(element_map), 5)
        self.assertIn("text1", element_map)
        self.assertIn("text2", element_map)
        self.assertIn("pic1", element_map)
        self.assertIn("table1", element_map)
        self.assertIn("group1", element_map)
        
        # Check that elements are correctly mapped
        self.assertEqual(element_map["text1"]["text"], "Hello world")
        self.assertEqual(element_map["text2"]["text"], "This refers to text1")

    def test_find_ref_pointers(self):
        """Test that $ref pointers are correctly identified."""
        element_map = extract_elements(self.sample_document)
        ref_pointers = find_ref_pointers(element_map)
        
        # Check that all $ref pointers are found
        self.assertEqual(len(ref_pointers), 7)
        
        # Create a set of reference values for easier checking
        ref_values = set(ref[2] for ref in ref_pointers)
        self.assertIn("text1", ref_values)
        self.assertIn("text2", ref_values)
        self.assertIn("pic1", ref_values)
        self.assertIn("table1", ref_values)

    def test_resolve_references(self):
        """Test that references are correctly resolved."""
        element_map = extract_elements(self.sample_document)
        ref_pointers = find_ref_pointers(element_map)
        resolved_map = resolve_references(element_map, ref_pointers)
        
        # Check that references have been replaced with actual elements
        text2 = resolved_map["text2"]
        self.assertIsInstance(text2["reference"], dict)
        self.assertIn("text", text2["reference"])
        self.assertEqual(text2["reference"]["text"], "Hello world")
        
        # Check nested references in group1
        group1 = resolved_map["group1"]
        self.assertIsInstance(group1["children"][0], dict)
        self.assertIn("text", group1["children"][0])
        self.assertEqual(group1["children"][0]["text"], "Hello world")

    def test_build_element_map(self):
        """Test the complete build_element_map function."""
        element_map = build_element_map(self.sample_document)
        
        # Check the number of elements
        self.assertEqual(len(element_map), 5)
        
        # Check that references are resolved
        group1 = element_map["group1"]
        self.assertIsInstance(group1["children"][0], dict)
        self.assertIn("text", group1["children"][0])
        
        # Check multi-level references
        table1 = element_map["table1"]
        self.assertIsInstance(table1["caption"], dict)
        self.assertIn("reference", table1["caption"])
        self.assertIsInstance(table1["caption"]["reference"], dict)
        self.assertIn("text", table1["caption"]["reference"])

    def test_circular_references(self):
        """Test handling of circular references."""
        # This should not cause an infinite loop
        element_map = build_element_map(self.circular_document)
        
        # The map should still contain both elements
        self.assertEqual(len(element_map), 2)
        self.assertIn("text1", element_map)
        self.assertIn("text2", element_map)

    def test_missing_references(self):
        """Test handling of missing references."""
        # This should log a warning but not fail
        element_map = build_element_map(self.missing_ref_document)
        
        # The map should still contain the existing element
        self.assertEqual(len(element_map), 1)
        self.assertIn("text1", element_map)
        
        # The reference should remain as a $ref object
        self.assertIn("reference", element_map["text1"])
        self.assertIn("$ref", element_map["text1"]["reference"])

    def test_nested_references(self):
        """Test resolution of nested references."""
        element_map = build_element_map(self.nested_document)
        
        # Check that all elements are in the map
        self.assertEqual(len(element_map), 3)
        
        # Check that text3's parent is text2, which has text1 as its parent
        text3 = element_map["text3"]
        self.assertEqual(text3["content"], "Grandchild text")
        self.assertIsInstance(text3["parent"], dict)
        self.assertEqual(text3["parent"]["content"], "Child text")
        self.assertIsInstance(text3["parent"]["parent"], dict)
        self.assertEqual(text3["parent"]["parent"]["content"], "Root text")

    def test_with_file_io(self):
        """Test with file I/O operations."""
        # Create a temporary file with the sample document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
            json.dump(self.sample_document, temp)
            temp_path = temp.name
        
        try:
            # Load the document from the file
            with open(temp_path, 'r') as f:
                loaded_document = json.load(f)
            
            # Build the element map
            element_map = build_element_map(loaded_document)
            
            # Check that it was processed correctly
            self.assertEqual(len(element_map), 5)
            self.assertIn("text1", element_map)
            
            # Write the element map to a file
            map_path = temp_path + ".map.json"
            with open(map_path, 'w') as f:
                json.dump(element_map, f)
            
            # Load the element map back
            with open(map_path, 'r') as f:
                loaded_map = json.load(f)
            
            # Check that it was saved and loaded correctly
            self.assertEqual(len(loaded_map), 5)
            self.assertIn("text1", loaded_map)
        finally:
            # Clean up temporary files
            Path(temp_path).unlink(missing_ok=True)
            Path(map_path).unlink(missing_ok=True)

if __name__ == '__main__':
    unittest.main() 