#!/usr/bin/env python3
"""
Test script for format_standardized_output.py

This script tests the standardized output format generation using existing JSON files.
"""

import json
import os
import sys
from pathlib import Path
import argparse

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'src'))

# Import the required modules
from src.format_standardized_output import save_standardized_output

def test_file(input_file, output_dir, pdf_path):
    """Test standardized output generation with a JSON file."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load the input JSON
    print(f"Loading input file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        document_data = json.load(f)
    
    # Generate standardized output
    print("Generating standardized output...")
    output_file = save_standardized_output(document_data, output_dir, pdf_path)
    
    print(f"Standardized output saved to: {output_file}")
    
    # Load the generated output to verify
    with open(output_file, 'r', encoding='utf-8') as f:
        output_data = json.load(f)
    
    # Print statistics
    print("\nOutput Statistics:")
    print(f"Chunks: {len(output_data['chunks'])}")
    print(f"Furniture: {len(output_data['furniture'])}")
    
    # Print the first chunk to verify format
    if output_data['chunks']:
        print("\nSample Chunk:")
        sample_chunk = output_data['chunks'][0]
        print(f"  content_type: {sample_chunk['content_type']}")
        print(f"  block_id: {sample_chunk['block_id']}")
        print(f"  master_index: {sample_chunk['master_index']}")
        
        # Print truncated text_block
        text_block = sample_chunk.get('text_block', '')
        if text_block and len(text_block) > 100:
            text_block = text_block[:100] + '...'
        print(f"  text_block: {text_block}")
    
    return output_file

def main():
    """Main function to test standardized output generation."""
    parser = argparse.ArgumentParser(description="Test standardized output format generation")
    parser.add_argument("--input", "-i", help="Input JSON file (default: uses multiple sample files)")
    parser.add_argument("--output-dir", "-o", default="./output_test", help="Output directory (default: ./output_test)")
    parser.add_argument("--pdf-path", "-p", default="test.pdf", help="PDF path for metadata (default: test.pdf)")
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    # If a specific input file is provided, test only that file
    if args.input:
        test_file(Path(args.input), output_dir, args.pdf_path)
        return 0
    
    # Otherwise, test multiple sample files
    sample_files = [
        Path('./output_pages4/SBW_AI sample page10-11.json'),
        Path('./output/SBW_AI.json')
    ]
    
    # Test each sample file
    for sample_file in sample_files:
        if sample_file.exists():
            print(f"\n{'-'*50}")
            print(f"Testing with file: {sample_file}")
            print(f"{'-'*50}")
            try:
                test_file(sample_file, output_dir, args.pdf_path)
            except Exception as e:
                print(f"Error processing {sample_file}: {e}")
        else:
            print(f"Sample file not found: {sample_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 