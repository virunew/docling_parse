#!/usr/bin/env python3
"""
Test module imports to ensure no circular dependencies exist.
"""
import unittest
import sys
import os
import importlib
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Create mocks for external dependencies
sys.modules['docling'] = MagicMock()
sys.modules['docling.document_converter'] = MagicMock()
sys.modules['docling.datamodel'] = MagicMock()
sys.modules['docling.datamodel.base_models'] = MagicMock()
sys.modules['docling.datamodel.pipeline_options'] = MagicMock()

# Create mocks for other potential imports
sys.modules['element_map_builder'] = MagicMock()
sys.modules['content_extractor'] = MagicMock()
sys.modules['pdf_image_extractor'] = MagicMock()


class TestImports(unittest.TestCase):
    """Test importing the key modules of the application."""

    def test_logger_config_import(self):
        """Test that logger_config module can be imported."""
        import logger_config
        self.assertIsNotNone(logger_config)
        self.assertIsNotNone(logger_config.logger)
        self.assertTrue(hasattr(logger_config, 'setup_logging'))

    def test_parse_helper_import(self):
        """Test that parse_helper module can be imported."""
        import parse_helper
        self.assertIsNotNone(parse_helper)
        self.assertTrue(hasattr(parse_helper, 'process_pdf_document'))
        self.assertTrue(hasattr(parse_helper, 'save_output'))

    def test_parse_main_imports(self):
        """Test if parse_main module can be imported."""
        import parse_main
        self.assertIsNotNone(parse_main)
        self.assertTrue(hasattr(parse_main, 'main'))
        self.assertTrue(hasattr(parse_main, 'Configuration'))

    def test_circular_dependency_check(self):
        """
        Test specifically for circular dependencies between parse_main and parse_helper.
        This is what we fixed with the logger_config module.
        """
        # First way to check - separate imports
        import logger_config
        import parse_helper
        import parse_main
        
        # Second way - reload each module separately 
        importlib.reload(logger_config)
        importlib.reload(parse_helper)
        importlib.reload(parse_main)
        
        # This test passes if all imports succeed without circular import errors

    def test_reload_modules(self):
        """Test that modules can be reloaded without errors."""
        import importlib
        
        # First import the modules
        import parse_main
        
        # Then reload them
        importlib.reload(parse_main)


if __name__ == '__main__':
    unittest.main() 