"""
Tests for element_map_builder.py

These tests verify that the element map builder can handle both dictionary
and Pydantic model style access, especially for the TextItem objects.
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import json

# Add parent directory to sys.path to find src modules
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.element_map_builder import build_element_map, convert_to_serializable


class MockTextItem:
    """Mock TextItem class that mimics a Pydantic model with attributes instead of dict access"""
    
    def __init__(self, self_ref, content="Sample text", ref=None, elements=None):
        self.self_ref = self_ref
        self.content = content
        if ref:
            # Use setattr to set the attribute with '$' character
            setattr(self, "$ref", ref)
        if elements:
            self.elements = elements


class TestElementMapBuilder(unittest.TestCase):
    """Test cases for the element_map_builder module"""
    
    def test_build_element_map_with_text_items(self):
        """Test building an element map with TextItem objects (Pydantic model style)"""
        # Create a mock DoclingDocument with TextItem objects
        mock_doc = MagicMock()
        
        # Create text items with self_refs
        text1 = MockTextItem(self_ref="#/texts/0", content="Text 1")
        text2 = MockTextItem(self_ref="#/texts/1", content="Text 2")
        
        # Create a group that references text items
        group1 = MockTextItem(self_ref="#/groups/0", elements=["#/texts/0", "#/texts/1"])
        
        # Set up the document structure
        mock_doc.name = "test_document"
        mock_doc.texts = [text1, text2]
        mock_doc.tables = []
        mock_doc.pictures = []
        mock_doc.groups = [group1]
        mock_doc.pages = [MagicMock()]  # One page
        
        # Set up the body with a reference to the group
        body = MagicMock()
        body.elements = ["#/groups/0"]
        mock_doc.body = body
        
        # Build the element map
        element_map = build_element_map(mock_doc)
        
        # Verify the element map structure
        self.assertIsNotNone(element_map)
        self.assertIn("elements", element_map)
        self.assertIn("flattened_sequence", element_map)
        self.assertIn("document_info", element_map)
        
        # Check document info
        self.assertEqual(element_map["document_info"]["name"], "test_document")
        self.assertEqual(element_map["document_info"]["page_count"], 1)
        
        # Check elements are in the map
        self.assertIn("#/texts/0", element_map["elements"])
        self.assertIn("#/texts/1", element_map["elements"])
        self.assertIn("#/groups/0", element_map["elements"])
        
        # Check that elements were flattened correctly
        self.assertEqual(len(element_map["flattened_sequence"]), 2)
        
        # Verify content of flattened elements
        flattened_content = [e.get("content", None) for e in element_map["flattened_sequence"]]
        self.assertIn("Text 1", flattened_content)
        self.assertIn("Text 2", flattened_content)
    
    def test_nested_references(self):
        """Test handling of nested references with both dict and object styles"""
        # Create a mock DoclingDocument with nested references
        mock_doc = MagicMock()
        
        # Create some text items
        text1 = MockTextItem(self_ref="#/texts/0", content="Text 1")
        text2 = MockTextItem(self_ref="#/texts/1", content="Text 2")
        
        # Create a nested group structure - using MockTextItem for consistent handling
        inner_group = MockTextItem(self_ref="#/groups/1", elements=["#/texts/1"])
        outer_group = MockTextItem(self_ref="#/groups/0")
        setattr(outer_group, "$ref", "#/groups/1")  # Set the reference
        
        # Set up the document structure
        mock_doc.name = "nested_document"
        mock_doc.texts = [text1, text2]
        mock_doc.tables = []
        mock_doc.pictures = []
        mock_doc.groups = [outer_group, inner_group]
        mock_doc.pages = [MagicMock(), MagicMock()]  # Two pages
        
        # Set up the body with references
        body = MagicMock()
        body.elements = ["#/texts/0", "#/groups/0"]
        mock_doc.body = body
        
        # Build the element map
        element_map = build_element_map(mock_doc)
        
        # Verify structure
        self.assertIn("#/texts/0", element_map["elements"])
        self.assertIn("#/texts/1", element_map["elements"])
        self.assertIn("#/groups/0", element_map["elements"])
        self.assertIn("#/groups/1", element_map["elements"])
        
        # The flattened sequence should include both text items
        # Text1 is directly referenced, and Text2 is referenced through the groups
        flattened_refs = [e.get("self_ref", None) for e in element_map["flattened_sequence"]]
        
        # We should have both text items in the flattened sequence in some form
        # Either check for the content or ensure we have the expected number of elements
        flattened_content = [e.get("content", None) for e in element_map["flattened_sequence"] 
                            if e.get("content") is not None]
        
        self.assertIn("Text 1", flattened_content)
        # Text 2 should be included through the nested reference chain
        self.assertIn("Text 2", flattened_content)


if __name__ == "__main__":
    unittest.main() 