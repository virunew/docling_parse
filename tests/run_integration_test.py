#!/usr/bin/env python3
"""
Integration test for parse_main.py

This script runs the parse_main.py script with a sample PDF and verifies that:
1. The process completes successfully
2. The output directory is created
3. The formatted output file exists
4. Images directory exists (if the PDF contains images)
5. The JSON output follows the expected structure

Usage:
    python tests/run_integration_test.py [sample_pdf_path]
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_parse_main(pdf_path, output_dir, output_format="json"):
    """Run parse_main.py with the given arguments."""
    parse_main_path = PROJECT_ROOT / "parse_main.py"
    
    # Run the script as a subprocess
    cmd = [
        sys.executable,
        str(parse_main_path),
        "--pdf_path", str(pdf_path),
        "--output_dir", str(output_dir),
        "--output_format", output_format,
        "--log_level", "INFO"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the process and capture output
    process = subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Print stdout and stderr
    if process.stdout:
        print("STDOUT:")
        print(process.stdout)
    
    if process.stderr:
        print("STDERR:")
        print(process.stderr)
    
    return process.returncode


def verify_output(output_dir, output_format="json"):
    """Verify that the expected output files exist and have the correct structure."""
    output_dir_path = Path(output_dir)
    
    # Check that output directory exists
    if not output_dir_path.exists() or not output_dir_path.is_dir():
        print(f"ERROR: Output directory {output_dir_path} does not exist")
        return False
    
    # Find formatted output file (should start with the output format name)
    output_files = list(output_dir_path.glob(f"*.{output_format}"))
    if not output_files:
        print(f"ERROR: No {output_format} file found in {output_dir_path}")
        return False
    
    formatted_output_file = output_files[0]
    print(f"Found formatted output file: {formatted_output_file}")
    
    # Check for images directory
    images_dir = output_dir_path / "images"
    if images_dir.exists():
        print(f"Found images directory: {images_dir}")
        image_count = len(list(images_dir.glob('*')))
        print(f"Number of images: {image_count}")
    
    # For JSON format, verify structure
    if output_format == "json":
        try:
            with open(formatted_output_file, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
            
            # Check for required top-level keys
            required_keys = ["chunks", "source_metadata"]
            missing_keys = [key for key in required_keys if key not in output_data]
            
            if missing_keys:
                print(f"ERROR: Output JSON missing required keys: {missing_keys}")
                return False
            
            # Check for chunks
            if 'chunks' in output_data and isinstance(output_data['chunks'], list):
                print(f"Found {len(output_data['chunks'])} chunks in output")
                
                # Check basic chunk structure
                if output_data['chunks']:
                    first_chunk = output_data['chunks'][0]
                    expected_fields = [
                        "block_id", "content_type", "master_index", 
                        "coords_x", "coords_y", "coords_cx", "coords_cy",
                        "text_block", "header_text"
                    ]
                    
                    missing_fields = [field for field in expected_fields if field not in first_chunk]
                    
                    if missing_fields:
                        print(f"WARNING: First chunk missing expected fields: {missing_fields}")
                    else:
                        print("First chunk contains all expected fields")
            else:
                print("WARNING: No chunks found in output")
        
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON output file: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to verify JSON structure: {e}")
            return False
    
    return True


def main():
    # Get sample PDF path from command line or use default
    if len(sys.argv) > 1:
        sample_pdf_path = Path(sys.argv[1])
    else:
        # Look for sample PDF in tests/data directory
        sample_pdf_path = PROJECT_ROOT / "tests" / "data" / "sample.pdf"
    
    # Check if sample PDF exists
    if not sample_pdf_path.exists():
        print(f"ERROR: Sample PDF not found at {sample_pdf_path}")
        print("Please provide a valid PDF path as the first argument")
        return 1
    
    print(f"Using sample PDF: {sample_pdf_path}")
    
    # Create temporary output directory
    output_dir = tempfile.mkdtemp()
    print(f"Created temporary output directory: {output_dir}")
    
    try:
        # Run parse_main.py
        return_code = run_parse_main(sample_pdf_path, output_dir)
        
        if return_code != 0:
            print(f"ERROR: parse_main.py exited with code {return_code}")
            return 1
        
        # Verify output
        if not verify_output(output_dir):
            print("ERROR: Output verification failed")
            return 1
        
        print("Integration test passed successfully!")
        return 0
    
    finally:
        # Clean up temporary directory
        print(f"Cleaning up temporary directory: {output_dir}")
        shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main()) 