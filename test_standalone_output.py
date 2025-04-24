#!/usr/bin/env python3
"""
Standalone test for standardized output format

This script tests the standardized output format without relying on the full parse_main.py pipeline.
"""

import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Import the module to test
from src.format_standardized_output import save_standardized_output

def run_test():
    """Run a test of the standardized output format with sample data."""
    # Create a temporary directory for output
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create sample document data with text, tables, and images
        document_data = {
            "name": "test_document",
            "element_map": {
                "flattened_sequence": [
                    # Text element with metadata
                    {
                        "type": "text",
                        "text_content": "This is a section header",
                        "content_layer": "body",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1",
                            "page_no": 1,
                            "bbox_raw": {"l": 50, "t": 100, "r": 500, "b": 120}
                        }
                    },
                    # Furniture element
                    {
                        "type": "text",
                        "text_content": "Page 1 of 10",
                        "content_layer": "furniture"
                    },
                    # Table element
                    {
                        "type": "table",
                        "content_layer": "body",
                        "table_content": [
                            ["Header 1", "Header 2", "Header 3"],
                            ["Cell 1", "Cell 2", "Cell 3"],
                            ["Cell 4", "Cell 5", "Cell 6"]
                        ],
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1 > Tables",
                            "page_no": 1,
                            "bbox_raw": {"l": 100, "t": 200, "r": 500, "b": 300},
                            "caption": "Table 1: Sample Data"
                        }
                    },
                    # Image element
                    {
                        "type": "picture",
                        "content_layer": "body",
                        "external_path": "images/sample_image.png",
                        "context_before": "Text before the image",
                        "context_after": "Text after the image",
                        "extracted_metadata": {
                            "breadcrumb": "Document > Section 1 > Figures",
                            "page_no": 2,
                            "bbox_raw": {"l": 150, "t": 250, "r": 450, "b": 350},
                            "caption": "Figure 1: Sample Image",
                            "image_ocr_text": "Text extracted from image via OCR"
                        }
                    }
                ]
            }
        }
        
        print("Generated sample document data with different content types")
        print(f"  Elements: {len(document_data['element_map']['flattened_sequence'])}")
        
        # Find the different content types in the data
        content_types = set()
        for element in document_data['element_map']['flattened_sequence']:
            if element.get('type'):
                content_types.add(element['type'])
        
        print(f"Found content types: {content_types}")
        
        # Call the standardized output function
        print("Generating standardized output...")
        output_file = save_standardized_output(
            document_data,
            temp_dir,
            "test.pdf"
        )
        
        print(f"Standardized output saved to: {output_file}")
        
        # Load and verify the output
        with open(output_file, 'r') as f:
            output_data = json.load(f)
        
        # Check structure
        print("\nVerifying output structure:")
        print(f"  Chunks: {len(output_data['chunks'])}")
        print(f"  Furniture: {len(output_data['furniture'])}")
        
        # Check content types
        chunk_types = {}
        for chunk in output_data['chunks']:
            content_type = chunk['content_type']
            chunk_types[content_type] = chunk_types.get(content_type, 0) + 1
        
        print(f"  Content Types: {chunk_types}")
        
        # Check if all required fields are present
        required_fields = [
            "_id", "block_id", "doc_id", "content_type", "file_type", 
            "master_index", "coords_x", "coords_y", "coords_cx", "coords_cy",
            "text_block", "header_text", "creator_tool"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in output_data['chunks'][0]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"  Warning: Missing required fields: {missing_fields}")
        else:
            print("  All required fields are present")
        
        # Print a sample from the output
        print("\nSample from standardized output:")
        print("  First chunk of each type:")
        for content_type in chunk_types.keys():
            for chunk in output_data['chunks']:
                if chunk['content_type'] == content_type:
                    print(f"  {content_type}:")
                    print(f"    block_id: {chunk['block_id']}")
                    print(f"    master_index: {chunk['master_index']}")
                    
                    # For tables, check the parsed content
                    if content_type == "table" and chunk['table_block']:
                        table_data = json.loads(chunk['table_block'])
                        print(f"    Table rows: {len(table_data)}")
                        print(f"    Table columns: {len(table_data[0])}")
                    
                    # For images, check the external path
                    if content_type == "image" and chunk['external_files']:
                        print(f"    External path: {chunk['external_files']}")
                    
                    break
        
        return True, "Test completed successfully"
    
    except Exception as e:
        return False, f"Error: {str(e)}"
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def main():
    """Main function for standalone testing."""
    print("Starting standalone test for standardized output format")
    
    # Add the src directory to the path
    sys.path.append(str(Path(__file__).parent))
    
    # Run the test
    success, message = run_test()
    
    if success:
        print("\nSuccess:", message)
        return 0
    else:
        print("\nFailed:", message)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 