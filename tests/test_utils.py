"""
Test Utilities Module

This module provides utility functions and mock setup for testing the docling_parse components.
"""

import sys
from unittest.mock import MagicMock
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling fix helper
import docling_fix

def setup_mock_docling():
    """
    Set up mock docling modules to enable testing without actual docling dependencies.
    
    This function mocks all required docling modules and creates basic classes and functions
    needed for testing.
    """
    # Mock the core docling modules
    sys.modules['docling.document_converter'] = MagicMock()
    sys.modules['docling.datamodel.base_models'] = MagicMock()
    sys.modules['docling.datamodel.pipeline_options'] = MagicMock()
    sys.modules['docling.datamodel.document'] = MagicMock()
    sys.modules['docling.utils.profiling'] = MagicMock()
    sys.modules['docling.utils.utils'] = MagicMock()
    sys.modules['docling.pipeline.base_pipeline'] = MagicMock()
    sys.modules['docling.pipeline.simple_pipeline'] = MagicMock()
    sys.modules['docling.pipeline.standard_pdf_pipeline'] = MagicMock()
    sys.modules['docling.exceptions'] = MagicMock()
    
    # Mock docling_core modules
    sys.modules['docling_core.types.doc'] = MagicMock()
    sys.modules['docling_core.types.doc.document'] = MagicMock()
    sys.modules['docling_core.types.legacy_doc.base'] = MagicMock()
    sys.modules['docling_core.types.legacy_doc.document'] = MagicMock()
    sys.modules['docling_core.utils.file'] = MagicMock()
    sys.modules['docling_core.utils.legacy'] = MagicMock()
    
    # Create a mock DoclingDocument class for testing
    class MockDoclingDocument:
        def __init__(self, name="test_document"):
            self.name = name
            self.texts = []
            self.tables = []
            self.pictures = []
            self.pages = []
        
        def export_to_dict(self):
            return {
                "name": self.name,
                "texts": self.texts,
                "tables": self.tables,
                "pictures": self.pictures,
                "pages": self.pages
            }
    
    # Add the mock DoclingDocument to the mocked module
    sys.modules['docling_core.types.doc'].DoclingDocument = MockDoclingDocument

# Automatically set up the mocks when the module is imported
setup_mock_docling() 