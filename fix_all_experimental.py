#!/usr/bin/env python3
"""
Script to add docling_fix import to all experimental Python files
"""

import os
import glob
import re

# Find all Python files in src/experimental directory
experimental_files = glob.glob('src/experimental/*.py')

for file_path in experimental_files:
    print(f"Processing {file_path}...")
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if "import docling_fix" in content:
        print(f"  Already contains docling_fix import, skipping")
        continue
    
    # Find position to insert the import statement
    match = re.search(r'(import.*?\n)', content)
    if match:
        # Insert after the first import statement
        position = match.end()
        new_content = content[:position] + "\n# Fix docling imports\nimport docling_fix\n" + content[position:]
    else:
        # Insert at the beginning after any comment blocks or docstrings
        # Find the end of any initial docstring or comments
        doc_match = re.search(r'(""".+?"""\s*\n)', content, re.DOTALL)
        if doc_match:
            position = doc_match.end()
        else:
            position = 0
        new_content = content[:position] + "\n# Fix docling imports\nimport docling_fix\n" + content[position:]
    
    # Write updated content back to file
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"  Added docling_fix import to {file_path}")

print("Done!") 