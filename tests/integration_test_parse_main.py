"""
Integration tests for the PDF document parsing application.

These tests verify that the entire parsing flow works correctly with real files.
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

# Import the module to test
from src.parse_main import main


class TestParsePDFIntegration(unittest.TestCase):
    """Integration tests for the parse_main.py module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save original environment variables and arguments
        self.original_environ = os.environ.copy()
        self.original_argv = sys.argv.copy()
        
        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Create a sample PDF in the test_data directory
        # For integration testing, we need a real PDF file
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # For now, we'll create a mock PDF file
        # In a real scenario, you should have a real PDF file in the test_data directory
        self.mock_pdf_path = self.test_data_dir / "sample.pdf"
        if not self.mock_pdf_path.exists():
            self.mock_pdf_path.touch()  # Create an empty file for now
            self.created_pdf = True
        else:
            self.created_pdf = False
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables and arguments
        os.environ.clear()
        os.environ.update(self.original_environ)
        sys.argv = self.original_argv
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
        
        # Clean up mock PDF if we created it
        if self.created_pdf and self.mock_pdf_path.exists():
            self.mock_pdf_path.unlink()
    
    def test_full_parsing_with_command_line_args(self):
        """Test the full parsing flow using command-line arguments."""
        # Set command-line arguments
        sys.argv = [
            "src/parse_main.py",
            "--pdf_path", str(self.mock_pdf_path),
            "--output_dir", str(self.output_dir),
            "--log_level", "DEBUG"
        ]
        
        # Run the main function
        exit_code = main()
        
        # Check that the function completed successfully
        self.assertEqual(exit_code, 0)
        
        # Check that the output file was created
        output_file = self.output_dir / "element_map.json"
        self.assertTrue(output_file.exists(), f"Output file not created: {output_file}")
        
        # Check that the output file contains valid JSON
        with open(output_file) as f:
            data = json.load(f)
        
        # Check that the output contains expected keys
        # This is a basic check; you'd want more specific checks in a real test
        self.assertIsInstance(data, dict)
        self.assertGreaterEqual(len(data), 1, "Element map should contain at least one element")
    
    def test_full_parsing_with_environment_vars(self):
        """Test the full parsing flow using environment variables."""
        # Set environment variables
        os.environ["DOCLING_PDF_PATH"] = str(self.mock_pdf_path)
        os.environ["DOCLING_OUTPUT_DIR"] = str(self.output_dir)
        os.environ["DOCLING_LOG_LEVEL"] = "DEBUG"
        
        # Clear command-line arguments
        sys.argv = ["src/parse_main.py"]
        
        # Run the main function
        exit_code = main()
        
        # Check that the function completed successfully
        self.assertEqual(exit_code, 0)
        
        # Check that the output file was created
        output_file = self.output_dir / "element_map.json"
        self.assertTrue(output_file.exists(), f"Output file not created: {output_file}")
        
        # Check that the output file contains valid JSON
        with open(output_file) as f:
            data = json.load(f)
        
        # Check that the output contains expected keys
        self.assertIsInstance(data, dict)
        self.assertGreaterEqual(len(data), 1, "Element map should contain at least one element")
    
    def test_parsing_with_dotenv_file(self):
        """Test the parsing flow using a .env file."""
        # Create a temporary .env file
        env_file = Path(".env")
        env_file.write_text(f"""
DOCLING_PDF_PATH={self.mock_pdf_path}
DOCLING_OUTPUT_DIR={self.output_dir}
DOCLING_LOG_LEVEL=DEBUG
""")
        
        try:
            # Clear command-line arguments
            sys.argv = ["src/parse_main.py"]
            
            # Run the main function
            exit_code = main()
            
            # Check that the function completed successfully
            self.assertEqual(exit_code, 0)
            
            # Check that the output file was created
            output_file = self.output_dir / "element_map.json"
            self.assertTrue(output_file.exists(), f"Output file not created: {output_file}")
            
            # Check that the output file contains valid JSON
            with open(output_file) as f:
                data = json.load(f)
            
            # Check that the output contains expected keys
            self.assertIsInstance(data, dict)
            self.assertGreaterEqual(len(data), 1, "Element map should contain at least one element")
        
        finally:
            # Clean up the .env file
            if env_file.exists():
                env_file.unlink()
    
    def test_command_line_args_override_env_vars(self):
        """Test that command-line arguments override environment variables."""
        # Create a different output directory for the command-line argument
        cmd_output_dir = self.output_dir / "cmd_output"
        
        # Set environment variables
        os.environ["DOCLING_PDF_PATH"] = str(self.mock_pdf_path)
        os.environ["DOCLING_OUTPUT_DIR"] = str(self.output_dir)
        
        # Set command-line arguments
        sys.argv = [
            "src/parse_main.py",
            "--output_dir", str(cmd_output_dir)
        ]
        
        # Run the main function
        exit_code = main()
        
        # Check that the function completed successfully
        self.assertEqual(exit_code, 0)
        
        # Check that the output file was created in the command-line specified directory
        env_output_file = self.output_dir / "element_map.json"
        cmd_output_file = cmd_output_dir / "element_map.json"
        
        self.assertFalse(env_output_file.exists(), 
                         "Output file should not be in env var directory")
        self.assertTrue(cmd_output_file.exists(), 
                        "Output file should be in command-line arg directory")


if __name__ == "__main__":
    unittest.main() 