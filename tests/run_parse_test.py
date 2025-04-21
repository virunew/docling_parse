#!/usr/bin/env python3
"""
Test script to run the parse_main.py module on a sample PDF file and verify the output format.

Usage:
    python run_parse_test.py <path_to_pdf_file>
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import the main function from parse_main.py
from src.parse_main import main


def verify_docling_document_json(json_file):
    """
    Verify that a JSON file follows the DoclingDocument format.
    
    Args:
        json_file: Path to the JSON file to verify
        
    Returns:
        bool: True if the file follows the DoclingDocument format, False otherwise
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Check for required top-level keys
        required_keys = ["schema_name", "version", "name", "body", "furniture"]
        for key in required_keys:
            if key not in data:
                print(f"ERROR: Missing required key '{key}' in DoclingDocument")
                return False
        
        # Verify schema name
        if data["schema_name"] != "DoclingDocument":
            print(f"ERROR: Invalid schema_name: {data['schema_name']}")
            return False
        
        # Check for body structure
        if "content_layer" not in data["body"]:
            print("ERROR: Missing 'content_layer' in body")
            return False
        
        # Check for furniture structure
        if "content_layer" not in data["furniture"]:
            print("ERROR: Missing 'content_layer' in furniture")
            return False
        
        print("SUCCESS: JSON file follows DoclingDocument format")
        
        # Print some basic metadata
        print(f"\nDocument Information:")
        print(f"  Name: {data['name']}")
        print(f"  Version: {data['version']}")
        print(f"  Schema: {data['schema_name']}")
        
        # Count elements by type
        element_counts = {}
        for key in data:
            if isinstance(data[key], list):
                element_counts[key] = len(data[key])
        
        print("\nElement Counts:")
        for key, count in element_counts.items():
            print(f"  {key}: {count}")
        
        return True
        
    except json.JSONDecodeError:
        print(f"ERROR: {json_file} is not valid JSON")
        return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the parse_main.py module on a sample PDF file"
    )
    
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to parse"
    )
    
    parser.add_argument(
        "--output_dir", "-o",
        default="test_output",
        help="Directory for output files (default: 'test_output')"
    )
    
    return parser.parse_args()


def main_test():
    """Main function for the test script."""
    args = parse_arguments()
    
    # Set environment variables
    os.environ["DOCLING_PDF_PATH"] = args.pdf_path
    os.environ["DOCLING_OUTPUT_DIR"] = args.output_dir
    os.environ["DOCLING_LOG_LEVEL"] = "INFO"
    
    print(f"Processing PDF: {args.pdf_path}")
    print(f"Output directory: {args.output_dir}")
    
    # Save original sys.argv and set it to include our options
    original_argv = sys.argv
    sys.argv = ["parse_main.py"]
    
    try:
        # Run the main function
        exit_code = main()
        
        print(f"\nParsing completed with exit code: {exit_code}")
        
        if exit_code == 0:
            # Verify the output
            output_file = Path(args.output_dir) / "element_map.json"
            if output_file.exists():
                print(f"\nVerifying output file: {output_file}")
                verify_docling_document_json(output_file)
            else:
                print(f"\nERROR: Output file not found: {output_file}")
        
        return exit_code
        
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


if __name__ == "__main__":
    sys.exit(main_test()) 