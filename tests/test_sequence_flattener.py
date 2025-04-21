"""
Unit tests for the sequence_flattener module.

These tests verify that the document sequence flattener correctly 
processes document structures into linear sequences while preserving reading order.
"""

import os
import sys
import unittest
import json
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.sequence_flattener import (
    get_flattened_body_sequence,
    get_element_by_reference, 
    sort_sequence_by_position
)


class TestSequenceFlattener(unittest.TestCase):
    """Test cases for the sequence_flattener module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample element map for testing
        self.sample_element_map = {
            "texts/0": {
                "id": "text_1",
                "text": "Header",
                "children": [],
                "bounds": {"t": 10, "l": 20, "r": 120, "b": 30}
            },
            "texts/1": {
                "id": "text_2",
                "text": "Paragraph 1",
                "children": [],
                "bounds": {"t": 40, "l": 20, "r": 200, "b": 60}
            },
            "texts/2": {
                "id": "text_3",
                "text": "Paragraph 2",
                "children": [],
                "bounds": {"t": 70, "l": 20, "r": 200, "b": 90}
            },
            "pictures/0": {
                "id": "pic_1",
                "image_data": "base64data",
                "children": [],
                "bounds": {"t": 100, "l": 50, "r": 150, "b": 150}
            },
            "tables/0": {
                "id": "table_1",
                "cells": [["A1", "B1"], ["A2", "B2"]],
                "children": [],
                "bounds": {"t": 160, "l": 20, "r": 200, "b": 200}
            },
            "sections/0": {
                "id": "section_1",
                "children": [
                    {"$ref": "texts/0"},
                    {"$ref": "texts/1"}
                ],
                "bounds": {"t": 5, "l": 10, "r": 210, "b": 65}
            },
            "sections/1": {
                "id": "section_2",
                "children": [
                    {"$ref": "texts/2"},
                    {"$ref": "pictures/0"},
                    {"$ref": "tables/0"}
                ],
                "bounds": {"t": 65, "l": 10, "r": 210, "b": 205}
            }
        }
        
        # Sample document body structure
        self.sample_body = [
            {"$ref": "sections/0"},
            {"$ref": "sections/1"}
        ]
        
        # Create a sample with references using '#/' prefix
        self.sample_element_map_with_prefix = {
            "#/texts/0": {
                "id": "text_1",
                "text": "Header with prefix",
                "children": [],
                "bounds": {"t": 10, "l": 20, "r": 120, "b": 30}
            },
            "#/texts/1": {
                "id": "text_2",
                "text": "Paragraph with prefix",
                "children": [],
                "bounds": {"t": 40, "l": 20, "r": 200, "b": 60}
            }
        }
        
        self.sample_body_with_prefix = [
            {"$ref": "#/texts/0"},
            {"$ref": "#/texts/1"}
        ]
    
    def test_get_element_by_reference(self):
        """Test getting elements by reference."""
        # Test with a valid reference
        element = get_element_by_reference(self.sample_element_map, "texts/0")
        self.assertIsNotNone(element)
        self.assertEqual(element["id"], "text_1")
        
        # Test with a reference that doesn't exist
        element = get_element_by_reference(self.sample_element_map, "nonexistent/0")
        self.assertIsNone(element)
        
        # Test with a reference that has '#/' prefix
        element = get_element_by_reference(self.sample_element_map_with_prefix, "#/texts/0")
        self.assertIsNotNone(element)
        self.assertEqual(element["id"], "text_1")
        
        # Test that the function can handle the prefix for lookup
        element = get_element_by_reference(self.sample_element_map_with_prefix, "texts/0")
        self.assertIsNone(element)
    
    def test_sort_sequence_by_position(self):
        """Test sorting sequences by position."""
        # Create a sample sequence to sort
        unsorted_sequence = [
            self.sample_element_map["tables/0"],
            self.sample_element_map["pictures/0"],
            self.sample_element_map["texts/0"],
            self.sample_element_map["texts/2"],
            self.sample_element_map["texts/1"]
        ]
        
        # Sort the sequence
        sorted_sequence = sort_sequence_by_position(unsorted_sequence)
        
        # Verify the correct order (by top position, then left)
        self.assertEqual(sorted_sequence[0]["id"], "text_1")  # t=10
        self.assertEqual(sorted_sequence[1]["id"], "text_2")  # t=40
        self.assertEqual(sorted_sequence[2]["id"], "text_3")  # t=70
        self.assertEqual(sorted_sequence[3]["id"], "pic_1")   # t=100
        self.assertEqual(sorted_sequence[4]["id"], "table_1") # t=160
    
    def test_get_flattened_body_sequence_simple(self):
        """Test flattening a simple document body."""
        # Create a simple body example
        simple_body = [
            {"$ref": "texts/0"},
            {"$ref": "texts/1"},
            {"$ref": "pictures/0"}
        ]
        
        # Flatten the sequence
        flattened = get_flattened_body_sequence(self.sample_element_map, simple_body)
        
        # Check the result
        self.assertEqual(len(flattened), 3)
        self.assertEqual(flattened[0]["id"], "text_1")
        self.assertEqual(flattened[1]["id"], "text_2")
        self.assertEqual(flattened[2]["id"], "pic_1")
    
    def test_get_flattened_body_sequence_with_children(self):
        """Test flattening a document body with nested children."""
        # Flatten the sequence with sections and children
        flattened = get_flattened_body_sequence(self.sample_element_map, self.sample_body)
        
        # Check that all elements are included
        # The sections and their children should be in the sequence
        self.assertGreaterEqual(len(flattened), 2)  # At least the 2 sections
        
        # Verify that section elements are included
        section_ids = [elem["id"] for elem in flattened if elem["id"].startswith("section")]
        self.assertEqual(len(section_ids), 2)
        self.assertIn("section_1", section_ids)
        self.assertIn("section_2", section_ids)
        
        # The full sequence should include sections and their children
        # If the recursive processing works, we should have 7 elements total
        # (2 sections + 3 texts + 1 picture + 1 table)
        self.assertEqual(len(flattened), 7)
    
    def test_get_flattened_body_sequence_with_prefix(self):
        """Test flattening a document body with '#/' prefixes in references."""
        flattened = get_flattened_body_sequence(
            self.sample_element_map_with_prefix, 
            self.sample_body_with_prefix
        )
        
        # Check the result
        self.assertEqual(len(flattened), 2)
        self.assertEqual(flattened[0]["id"], "text_1")
        self.assertEqual(flattened[1]["id"], "text_2")
    
    def test_get_flattened_body_sequence_empty_inputs(self):
        """Test flattening with empty inputs."""
        # Test with empty element map
        flattened = get_flattened_body_sequence({}, self.sample_body)
        self.assertEqual(flattened, [])
        
        # Test with empty body
        flattened = get_flattened_body_sequence(self.sample_element_map, [])
        self.assertEqual(flattened, [])
    
    def test_get_flattened_body_sequence_invalid_references(self):
        """Test flattening with invalid references."""
        # Create a body with nonexistent references
        invalid_body = [
            {"$ref": "texts/0"},
            {"$ref": "nonexistent/0"},
            {"$ref": "pictures/0"}
        ]
        
        # Flatten the sequence (should skip the invalid reference)
        flattened = get_flattened_body_sequence(self.sample_element_map, invalid_body)
        
        # Check the result (only 2 valid references should be processed)
        self.assertEqual(len(flattened), 2)
        self.assertEqual(flattened[0]["id"], "text_1")
        self.assertEqual(flattened[1]["id"], "pic_1")


if __name__ == "__main__":
    unittest.main() 