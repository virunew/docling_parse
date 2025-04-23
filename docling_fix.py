"""
Docling Import Fix Helper

This module fixes the docling imports by adding the correct paths to sys.path.
Import this at the top of any file that needs to import from docling.
"""

import sys
import os
from pathlib import Path
import logging

def fix_docling_imports():
    """
    Add the necessary paths to sys.path to fix docling imports.
    
    Returns:
        bool: True if paths were adjusted, False if they were already correct
    """
    # Get the current directory and paths
    current_dir = Path(os.getcwd())
    docling_dir = current_dir / "docling"  
    docling_package_dir = docling_dir / "docling"
    
    # Debug
    print(f"Current directory: {current_dir}")
    print(f"Docling directory: {docling_dir}")
    print(f"Docling package directory: {docling_package_dir}")
    print(f"sys.path before: {sys.path}")
    
    # Clear previous docling paths to avoid confusion
    for p in list(sys.path):
        if 'docling_parse/docling' in p:
            sys.path.remove(p)
    
    # First, add the docling package directory as the primary path
    # This should handle "import docling.backend" style imports
    sys.path.insert(0, str(docling_package_dir))
    
    # Add the parent docling dir
    sys.path.insert(0, str(docling_dir))
    
    # Add the project root to find any local modules
    sys.path.insert(0, str(current_dir))
    
    # Ensure there are no duplicate paths
    sys.path = list(dict.fromkeys(sys.path))
    
    print(f"cle: {sys.path}")
    
    # Create an empty __init__.py file in any missing package directories

    ensure_init_file(docling_package_dir)
    ensure_init_file(docling_dir)
    ensure_init_file(docling_package_dir / "backend")
    
    return True

def ensure_init_file(directory):
    """Create __init__.py file if it doesn't exist"""
    init_file = directory / "__init__.py"
    if directory.exists() and not init_file.exists():
        print(f"Creating missing __init__.py in {directory}")
        init_file.touch()

# Automatically fix imports when this module is imported
#fixed = fix_docling_imports() 