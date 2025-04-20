#!/usr/bin/env python3
"""
Integration tests for parse_main.py
"""

import os
import sys
import unittest
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

# Add the parent directory to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestParseMainIntegration(unittest.TestCase):
    """Integration tests for parse_main.py"""
    
    def setUp(self):
        """Set up test environment."""
        # Create test directories
        self.test_dir = Path("test_integration")
        self.test_dir.mkdir(exist_ok=True)
        
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Path to a sample PDF for testing
        # For actual testing, you would need a real PDF file
        self.sample_pdf = self.test_dir / "sample.pdf"
        
        # For integration test, let's create a dummy PDF if it doesn't exist
        if not self.sample_pdf.exists():
            with open(self.sample_pdf, "wb") as f:
                f.write(b"%PDF-1.4\n% Dummy PDF file for testing\n")
        
        # Make sure config file exists
        self.config_file = Path("docling_config.yaml")
        self.assertTrue(self.config_file.exists(), "docling_config.yaml must exist for this test")
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test output directory
        import shutil
        if self.output_dir.exists():
            for file in self.output_dir.glob("*"):
                if file.is_file():
                    file.unlink()
        
        # Don't remove the sample.pdf as it might be a real test file
    
    @unittest.skip("Integration test requires docling library and real PDF - run manually")
    def test_parse_main_with_config_file(self):
        """Test that parse_main.py works correctly with a configuration file."""
        # We'll use subprocess to run the parse_main.py script
        # This is a real integration test that requires a real PDF file
        
        if not self.sample_pdf.exists() or os.path.getsize(self.sample_pdf) < 1000:
            self.skipTest("A real PDF file is required for this integration test")
        
        # Set up environment variables
        env = os.environ.copy()
        env["DOCLING_CONFIG_FILE"] = str(self.config_file.absolute())
        
        # Run the script with command-line arguments
        cmd = [
            sys.executable,
            str(Path("src/parse_main.py").absolute()),
            "--pdf_path", str(self.sample_pdf),
            "--output_dir", str(self.output_dir),
            "--log_level", "DEBUG",
            "--config_file", str(self.config_file.absolute())
        ]
        
        try:
            # Run the process and capture output
            process = subprocess.run(
                cmd,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Check that the process completed successfully
            self.assertEqual(process.returncode, 0, 
                            f"Process failed with error: {process.stderr}")
            
            # Check that output file was created
            output_file = self.output_dir / "element_map.json"
            self.assertTrue(output_file.exists(), 
                           f"Output file {output_file} was not created")
            
            # Verify the output JSON has expected structure
            with open(output_file, 'r') as f:
                element_map = json.load(f)
            
            self.assertIsInstance(element_map, dict, 
                                 "Output element_map should be a dictionary")
            
            # Log the output for debugging
            print(f"Script output:\n{process.stdout}")
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Script execution failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("Script execution timed out")


if __name__ == "__main__":
    unittest.main() 