#!/usr/bin/env python3
"""
SQL Formatter Verification Script

This script verifies that the SQL formatter works correctly by creating
mock document data and testing that the formatter properly processes it.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import docling_fix to fix import paths
import docling_fix

print("Verifying SQL formatter functionality...")

# Import the SQLFormatter
from src.sql_formatter import SQLFormatter

# Create a mock document
mock_document = {
    "pdf_name": "test_document.pdf",
    "pdf_info": {
        "Title": "Test Document",
        "Author": "Test Author",
        "Subject": "Test Subject"
    },
    "num_pages": 3,
    "elements": [
        {
            "type": "text",
            "page_num": 1,
            "text": "This is a test document",
            "font_size": 16
        },
        {
            "type": "text",
            "page_num": 1,
            "text": "This is test content.",
            "font_size": 12
        },
        {
            "type": "table",
            "page_num": 2,
            "data": [
                ["Header 1", "Header 2"],
                ["Data 1", "Data 2"]
            ]
        }
    ]
}

# Create a temporary directory for output
temp_dir = tempfile.mkdtemp()
output_path = Path(temp_dir)

print(f"Using temporary directory: {temp_dir}")

# Create SQLFormatter instance
formatter = SQLFormatter()
print("Created SQLFormatter instance")

# Format the document
formatted_data = formatter.format_as_sql_json(mock_document)
print("Formatted document as SQL JSON")

# Verify basic structure
assert "source" in formatted_data, "Missing 'source' in formatted data"
assert "furniture" in formatted_data, "Missing 'furniture' in formatted data"
assert "chunks" in formatted_data, "Missing 'chunks' in formatted data"

# Verify source information
assert formatted_data["source"]["file_name"] == "test_document.pdf", "Incorrect file_name"
assert formatted_data["source"]["title"] == "Test Document", "Incorrect title"
assert formatted_data["source"]["author"] == "Test Author", "Incorrect author"

# Save to file
output_file = formatter.save_formatted_output(mock_document, str(output_path))
print(f"Saved formatted output to {output_file}")

# Load the output file
with open(output_file, 'r', encoding='utf-8') as f:
    saved_data = json.load(f)

# Verify saved content
assert "source" in saved_data, "Missing 'source' in saved data"
assert "furniture" in saved_data, "Missing 'furniture' in saved data"
assert "chunks" in saved_data, "Missing 'chunks' in saved data"

# Check the structure of chunks
assert isinstance(saved_data["chunks"], list), "Chunks should be a list"
if saved_data["chunks"]:
    chunk = saved_data["chunks"][0]
    assert "content_type" in chunk, "Chunk missing content_type"
    assert "content" in chunk, "Chunk missing content"
    print(f"Chunk structure is valid: {list(chunk.keys())}")

# Clean up
import shutil
shutil.rmtree(temp_dir)
print(f"Cleaned up temporary directory {temp_dir}")

print("All tests passed successfully!")
print("The SQL formatter is correctly formatting document data.") 